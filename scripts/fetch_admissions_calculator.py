#!/usr/bin/env python3
"""
Fetch Admissions Calculator JSON via existing Chrome login session.

Workflow:
- Connect to an already-running Chrome with remote debugging enabled
- Navigate to the university's applying page
- Capture DevTools performance logs and filter the admissions-calculator API
- Save the first successful JSON response to downloads/<University>/admissions_calculator.json

Prerequisites:
1) Launch Chrome with remote debugging and an isolated user-data-dir to keep your login session:
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
       --remote-debugging-port=9222 \
       --user-data-dir=/tmp/chrome_dev_session

2) Ensure you are logged in to US News in that Chrome session.

Usage examples:
  python scripts/fetch_admissions_calculator.py --name "Princeton University"
  python scripts/fetch_admissions_calculator.py --link "/best-colleges/princeton-university-2627"
  python scripts/fetch_admissions_calculator.py --school-id 2627 --name "Princeton University"
"""

import os
import re
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


BASE_URL = "https://premium.usnews.com"
APPLYING_SEGMENT = "applying"
ADMISSIONS_API_PREFIX = (
    "https://premium.usnews.com/best-colleges/compass/api/admissions-calculator?school_id="
)


def setup_logger() -> None:
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.INFO, format='%(message)s')


def slugify_name(name: str) -> str:
    normalized = name.replace(' ', '_').replace('&', 'and').replace(',', '').replace('.', '')
    normalized = ''.join(c for c in normalized if c.isalnum() or c in '_-')
    return normalized


def derive_school_id_from_link(link: str) -> Optional[str]:
    if not link:
        return None
    match = re.search(r'-(\d+)(?:\?|$)', link)
    return match.group(1) if match else None


def construct_url_from_link(link: str, page_type: str) -> str:
    page_type = (page_type or "").strip("/")
    if not isinstance(link, str) or not link:
        return BASE_URL
    if "://" in link:
        from urllib.parse import urlparse
        path = urlparse(link).path
    else:
        path = link
    if not path.startswith("/"):
        path = "/" + path
    if page_type == "":
        return f"{BASE_URL}{path}"
    return f"{BASE_URL}{path}/{page_type}"


def read_universities(universities_path: str) -> list[dict[str, Any]]:
    try:
        with open(universities_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"❌ Failed to read universities JSON: {e}")
        return []


def find_university(universities: list[dict[str, Any]], name_query: str) -> Optional[dict[str, Any]]:
    if not name_query:
        return None
    q = name_query.lower()
    for u in universities:
        if q in str(u.get('name', '')).lower():
            return {"name": u.get("name", ""), "link": u.get("link", "")}
    return None


def create_driver_attached_to_existing(debugger_address: str = "127.0.0.1:9222") -> Optional[webdriver.Chrome]:
    """Attach to an existing Chrome with remote debugging enabled and enable performance logs."""
    try:
        options = Options()
        options.add_experimental_option("debuggerAddress", debugger_address)
        # Enable performance logging to capture Network.* events via driver.get_log('performance')
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        # Hint perf logging network preference
        options.set_capability("goog:chromeOptions", {"perfLoggingPrefs": {"enableNetwork": True}})

        driver = webdriver.Chrome(options=options)
        # Additionally enable Network via CDP
        try:
            driver.execute_cdp_cmd("Network.enable", {
                "maxTotalBufferSize": 10000000,
                "maxResourceBufferSize": 5000000
            })
        except Exception:
            pass
        logging.info("✅ Attached to existing Chrome (remote debugging).")
        return driver
    except Exception as e:
        logging.error(f"❌ Failed to attach to existing Chrome: {e}")
        logging.info("💡 Start Chrome like this and log in first:")
        logging.info("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_dev_session")
        return None


def get_performance_entries(driver: webdriver.Chrome) -> list[dict[str, Any]]:
    try:
        entries = driver.get_log("performance")
        return entries or []
    except Exception:
        return []


def extract_cdp_message(entry: dict[str, Any]) -> Optional[dict[str, Any]]:
    try:
        msg_raw = entry.get("message")
        if not msg_raw:
            return None
        return json.loads(msg_raw).get("message")
    except Exception:
        return None


def capture_first_admissions_json(driver: webdriver.Chrome, wait_seconds: int = 30) -> Optional[dict[str, Any]]:
    """Poll performance logs to find the first successful admissions-calculator response and return its JSON body."""
    deadline = time.time() + max(1, wait_seconds)
    seen_request_ids: set[str] = set()
    while time.time() < deadline:
        time.sleep(0.5)
        for entry in get_performance_entries(driver):
            msg = extract_cdp_message(entry)
            if not msg:
                continue
            method = msg.get("method")
            if method != "Network.responseReceived":
                continue
            params = msg.get("params", {})
            response = params.get("response", {})
            url = response.get("url", "")
            status = int(response.get("status", 0) or 0)
            request_id = params.get("requestId")
            if not request_id or request_id in seen_request_ids:
                continue
            if not url.startswith(ADMISSIONS_API_PREFIX):
                continue
            if status != 200:
                continue
            seen_request_ids.add(request_id)
            # Fetch body via CDP
            try:
                body_obj = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                body_text = body_obj.get("body")
                if not body_text:
                    continue
                # Some responses may be base64-encoded; handle automatically when indicated
                if body_obj.get("base64Encoded"):
                    import base64
                    decoded = base64.b64decode(body_text)
                    try:
                        return json.loads(decoded.decode("utf-8", errors="ignore"))
                    except Exception:
                        continue
                # Plain JSON text
                return json.loads(body_text)
            except Exception:
                continue
    return None


def ensure_download_dir(university_name: str, downloads_root: str = "downloads") -> Path:
    uni_dir = Path(downloads_root) / slugify_name(university_name)
    uni_dir.mkdir(parents=True, exist_ok=True)
    return uni_dir


def main():
    setup_logger()
    parser = argparse.ArgumentParser(description="Fetch Admissions Calculator JSON using existing Chrome session")
    parser.add_argument("--name", type=str, default="", help="University name (partial match from data/universities.json)")
    parser.add_argument("--link", type=str, default="", help="University link path like /best-colleges/princeton-university-2627")
    parser.add_argument("--school-id", type=str, default="", help="Override school_id explicitly")
    parser.add_argument("--universities", type=str, default="data/universities.json", help="Path to universities.json")
    parser.add_argument("--debugger-address", type=str, default="127.0.0.1:9222", help="Chrome debugger address")
    parser.add_argument("--wait", type=int, default=30, help="Seconds to wait for API capture")
    # Batch options
    parser.add_argument("--all", action="store_true", help="Process all universities from the JSON list")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of universities to process in --all mode")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds to wait between universities in --all mode")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing admissions_calculator.json if present")
    args = parser.parse_args()

    # If batch mode, iterate all using a single driver attach
    if args.all:
        universities = read_universities(args.universities)
        if not universities:
            logging.error("❌ No universities data available for --all mode.")
            return

        limit = int(args.limit) if args.limit and args.limit > 0 else None
        if limit is not None:
            universities = universities[:limit]

        driver = create_driver_attached_to_existing(args.debugger_address)
        if not driver:
            return

        processed = 0
        saved = 0
        skipped = 0

        try:
            for u in universities:
                uni_name = str(u.get("name", "")).strip()
                link = str(u.get("link", "")).strip()
                if not uni_name or not link:
                    skipped += 1
                    continue

                school_id = derive_school_id_from_link(link) or ""
                if not school_id:
                    logging.warning(f"⏭️ No school_id for: {uni_name}")
                    skipped += 1
                    continue

                applying_url = construct_url_from_link(link, APPLYING_SEGMENT)
                logging.info("\n=" * 30)
                logging.info(f"📘 {uni_name}")
                logging.info(f"🎯 {applying_url}")
                logging.info(f"🎯 {ADMISSIONS_API_PREFIX}{school_id}")

                # Ensure output path
                out_dir = ensure_download_dir(uni_name)
                out_file = out_dir / "admissions_calculator.json"
                if out_file.exists() and not args.overwrite:
                    logging.info(f"⏭️ Already exists, skipping (use --overwrite to replace): {out_file}")
                    skipped += 1
                    processed += 1
                    if args.delay > 0:
                        time.sleep(args.delay)
                    continue

                # Clear perf log buffer and navigate
                _ = get_performance_entries(driver)
                driver.get(applying_url)
                logging.info("🔎 Waiting for admissions-calculator API response...")
                data = capture_first_admissions_json(driver, wait_seconds=args.wait)
                if not data:
                    logging.warning("⏭️ No API response captured within timeout")
                    skipped += 1
                else:
                    try:
                        with open(out_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        logging.info(f"✅ Saved: {out_file}")
                        saved += 1
                    except Exception as e:
                        logging.error(f"❌ Save failed: {e}")
                        skipped += 1

                processed += 1
                if args.delay > 0:
                    time.sleep(args.delay)

        finally:
            try:
                driver.quit()
            except Exception:
                pass

        logging.info("\n📦 Batch result")
        logging.info(f"Processed: {processed}")
        logging.info(f"Saved:     {saved}")
        logging.info(f"Skipped:   {skipped}")
        return

    # Resolve university info (single mode)
    uni_name = args.name.strip()
    link = args.link.strip()
    school_id = args.school_id.strip()

    if not link or not uni_name:
        universities = read_universities(args.universities)
        if not universities:
            logging.error("❌ No universities data available. Provide --link and --name or fix data/universities.json")
            return
        if not uni_name:
            logging.error("❌ --name is required (partial match supported)")
            return
        found = find_university(universities, uni_name)
        if not found:
            logging.error(f"❌ University not found for name: {uni_name}")
            return
        uni_name = found.get("name") or uni_name
        link = found.get("link") or link

    # Derive school_id if needed
    if not school_id:
        school_id = derive_school_id_from_link(link) or ""
    if not school_id:
        logging.error("❌ Could not derive school_id. Provide --school-id explicitly.")
        return

    applying_url = construct_url_from_link(link, APPLYING_SEGMENT)
    logging.info(f"🎯 Target applying page: {applying_url}")
    logging.info(f"🎯 Admissions API prefix: {ADMISSIONS_API_PREFIX}{school_id}")

    driver = create_driver_attached_to_existing(args.debugger_address)
    if not driver:
        return

    try:
        # Make sure performance log buffer is empty before navigation
        _ = get_performance_entries(driver)

        logging.info("🌐 Navigating to applying page...")
        driver.get(applying_url)

        # Wait a little for SPA/network to kick in and then poll logs
        logging.info("🔎 Waiting for admissions-calculator API response...")
        data = capture_first_admissions_json(driver, wait_seconds=args.wait)
        if not data:
            logging.error("❌ Admissions-calculator API response not captured within timeout.")
            return

        out_dir = ensure_download_dir(uni_name)
        out_file = out_dir / "admissions_calculator.json"
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"✅ Saved: {out_file}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()


