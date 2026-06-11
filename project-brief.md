# 地球Online 每日任務系統 — 專案說明

## 目標

建立一個靜態網站，偽裝成 App 跑在手機上（PWA），每天自動從 Threads 帳號 [@earthonlinequest](https://www.threads.com/@earthonlinequest) 抓取當日任務，並顯示在系統裡供使用者完成。

---

## 資料來源

- **Threads 帳號：** `@earthonlinequest`
- **更新時間：** 每天早上 9 點
- **貼文格式（固定）：**

```
今日地球online主線任務：
1. 任務一
2. 任務二
3. 任務三
額外支線任務：
1. 支線任務一
```

---

## 整體架構

```
每天定時（台灣早上9點後）
   ↓
GitHub Actions（雲端免費）
   ↓ 執行 Python 爬蟲，抓 Threads 最新貼文
   ↓ 解析出主線任務 + 支線任務
   ↓ 存成 tasks.json，自動 commit 進 repo
   ↓
GitHub Pages 靜態網站
   ↓ 讀取 tasks.json
   ↓
使用者手機（PWA，釘選到桌面像 App）
```

- 不需要伺服器，不需要電腦開著
- 完全免費（GitHub 免費帳號）

---

## 已完成：Python 爬蟲

檔案：`scraper.py`

**使用套件：** `playwright`（操控無頭 Chromium，因為 Threads 是 JS 渲染頁面）

**邏輯：**
1. 用 Playwright 開啟 Threads 頁面
2. 提取整頁純文字（不依賴 HTML 結構，靠關鍵字解析）
3. 找到第一個含「主線任務」的段落，提取 `1. 2. 3.` 開頭的行
4. 找到緊接著的「支線任務」段落，提取 `1.` 開頭的行
5. 只取最新一篇（頁面最頂端的貼文）

```python
import re
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")


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
            if found_side:
                side_tasks.append(line)
            elif found_main:
                main_tasks.append(line)
        else:
            if found_side and side_tasks:
                break

    return main_tasks, side_tasks


def main():
    text = get_page_text()
    main_tasks, side_tasks = parse_tasks(text)

    print("=== 主線任務 ===")
    for task in main_tasks:
        print(task)

    print("\n=== 支線任務 ===")
    for task in side_tasks:
        print(task)


if __name__ == "__main__":
    main()
```

**測試結果（2026-06-11）：**
```
=== 主線任務 ===
1. 如果要使用鈔票，查看那張鈔票的編號
2. 抬頭凝視天花板30秒
3. 進食蔬菜

=== 支線任務 ===
1. 比昨晚提前半小時入睡
```

---

## 待完成：GitHub Actions 設定

爬蟲跑完後要把結果存成 `tasks.json`，格式建議如下：

```json
{
  "date": "2026-06-11",
  "main": [
    "如果要使用鈔票，查看那張鈔票的編號",
    "抬頭凝視天花板30秒",
    "進食蔬菜"
  ],
  "side": [
    "比昨晚提前半小時入睡"
  ]
}
```

GitHub Actions workflow 每天台灣時間早上9點後觸發，執行爬蟲並 commit `tasks.json` 回 repo。

---

## 待完成：靜態網站（PWA）

- 讀取 repo 內的 `tasks.json`
- 顯示當日主線任務 + 支線任務
- 支援 PWA（manifest + service worker），讓使用者能釘選到手機桌面
- 設計風格可以參考遊戲任務介面（配合「地球Online」主題）

---

## 備註

- Threads 沒登入狀態可以看到最近幾篇公開貼文，不需要帳號
- 爬蟲以**關鍵字**解析（`主線任務`、`支線任務`），不依賴 HTML 結構，對格式小改動有一定容錯性
- 若 Threads 改版需要登入才能看，爬蟲會需要調整
