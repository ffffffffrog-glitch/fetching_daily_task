import re
import sys
import json
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

TW_TZ = timezone(timedelta(hours=8))


def get_page_text():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.threads.com/@earthonlinequest", wait_until="networkidle")
        page.wait_for_timeout(3000)
        text = page.inner_text("body")
        browser.close()
    return text


def parse_tasks(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    main_tasks = []
    side_tasks = []
    found_main = False
    found_side = False

    for line in lines:
        if "主線任務" in line and not found_main:
            found_main = True
            found_side = False
            continue
        if "支線任務" in line and found_main and not found_side:
            found_side = True
            continue
        if re.match(r"^\d+[\.。]\s", line):
            clean = re.sub(r"^\d+[\.。]\s*", "", line)
            if found_side:
                side_tasks.append(clean)
            elif found_main:
                main_tasks.append(clean)
        else:
            if found_side and side_tasks:
                break

    return main_tasks, side_tasks


def main():
    today = datetime.now(TW_TZ).strftime("%Y-%m-%d")

    try:
        print("正在抓取頁面...")
        text = get_page_text()
        main_tasks, side_tasks = parse_tasks(text)
        if not main_tasks:
            print("Warning: 未找到任務，保留原有 tasks.json", file=sys.stderr)
            return
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return

    try:
        with open("tasks.json", "r", encoding="utf-8") as f:
            old = json.load(f)
        history = old.get("history", [])
    except Exception:
        history = []

    entry = {"date": today, "main": main_tasks, "side": side_tasks}
    if not history or history[-1]["date"] != today:
        history.append(entry)
    else:
        history[-1] = entry
    history = history[-30:]  # 保留最近 30 天

    result = {
        "date": today,
        "main": main_tasks,
        "side": side_tasks,
        "fetched_at": datetime.now(TW_TZ).isoformat(),
        "history": history
    }

    with open("tasks.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"tasks.json 已更新（{today}）")
    print(f"  主線: {main_tasks}")
    print(f"  支線: {side_tasks}")


if __name__ == "__main__":
    main()
