"""
FnGuide 신규 리포트 자동 다운로드 → Google Drive '주식전략' 폴더 저장

동작
  1) FnGuide 로그인 (ID/PW는 .env에서 읽음)
  2) 리포트 목록 페이지(LIST_URL) 접속
  3) 목록 상단부터 '전 영업일' 이후 발간 리포트만 골라
     제목 클릭 → 새 창 → 다운로드 버튼 → PDF 저장
  4) SAVE_DIR(Google Drive for desktop 의 '주식전략' 폴더)에 저장 → 자동 업로드
  5) 받은 목록을 history.json 에 기록해 중복 다운로드 방지

사용
  python fnguide_download.py --inspect   # 화면 구조 확인용 (스크린샷/HTML 저장)
  python fnguide_download.py             # 실제 다운로드
  python fnguide_download.py --dry-run   # 받을 목록만 출력
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

ID = os.getenv("FNGUIDE_ID", "")
PW = os.getenv("FNGUIDE_PW", "")
LOGIN_URL = os.getenv("LOGIN_URL", "https://www.fnguide.com/Users/Login")
LIST_URL = os.getenv("LIST_URL", "")
SAVE_DIR = Path(os.getenv("SAVE_DIR", str(BASE / "downloads")))
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

# 화면 구조에 맞춰 조정하는 셀렉터 (--inspect 결과를 보고 수정)
ROW_SELECTOR = os.getenv("ROW_SELECTOR", "table tbody tr")
LINK_SELECTOR = os.getenv("LINK_SELECTOR", "a")
DOWNLOAD_SELECTOR = os.getenv(
    "DOWNLOAD_SELECTOR",
    "text=다운로드 >> visible=true",
)

HISTORY = BASE / "history.json"
DEBUG_DIR = BASE / "debug"
DATE_RE = re.compile(r"(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})")


def log(msg):
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def prev_business_day(today: dt.date) -> dt.date:
    d = today - dt.timedelta(days=1)
    while d.weekday() >= 5:  # 토·일 건너뜀
        d -= dt.timedelta(days=1)
    return d


def load_history() -> set:
    if HISTORY.exists():
        return set(json.loads(HISTORY.read_text(encoding="utf-8")))
    return set()


def save_history(h: set):
    HISTORY.write_text(json.dumps(sorted(h), ensure_ascii=False, indent=1), encoding="utf-8")


def safe_name(s: str) -> str:
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", s).strip()
    return re.sub(r"\s+", " ", s)[:150]


def dump(page, name):
    DEBUG_DIR.mkdir(exist_ok=True)
    page.screenshot(path=str(DEBUG_DIR / f"{name}.png"), full_page=True)
    (DEBUG_DIR / f"{name}.html").write_text(page.content(), encoding="utf-8")
    log(f"  저장: debug/{name}.png, debug/{name}.html  (URL: {page.url})")


def login(page):
    log("로그인 중...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    page.fill("#userId", ID)
    page.fill("#userPw", PW)
    page.click("#loginBtn")
    try:
        page.wait_for_url(lambda u: "/Users/Login" not in u, timeout=20000)
    except PWTimeout:
        dump(page, "login_failed")
        sys.exit("로그인 실패: ID/PW 또는 중복로그인 안내창을 확인하세요 (debug/login_failed.png)")
    log("로그인 성공")


def collect_targets(page, cutoff: dt.date):
    """목록 상단부터 cutoff 이후 날짜의 행만 수집 (최신순 목록 가정)."""
    targets = []
    rows = page.locator(ROW_SELECTOR)
    for i in range(rows.count()):
        row = rows.nth(i)
        text = row.inner_text()
        m = DATE_RE.search(text)
        if not m:
            continue
        d = dt.date(int(m[1]), int(m[2]), int(m[3]))
        if d < cutoff:
            break  # 이후는 더 오래된 리포트
        link = row.locator(LINK_SELECTOR).first
        if link.count() == 0:
            continue
        title = link.inner_text().strip() or text.split("\n")[0]
        targets.append((i, d, title))
    return targets


def download_one(context, page, row_idx, date, title):
    link = page.locator(ROW_SELECTOR).nth(row_idx).locator(LINK_SELECTOR).first
    with context.expect_page(timeout=20000) as pinfo:
        link.click()
    popup = pinfo.value
    popup.wait_for_load_state("domcontentloaded")
    try:
        with popup.expect_download(timeout=60000) as dinfo:
            popup.locator(DOWNLOAD_SELECTOR).first.click()
        dl = dinfo.value
        ext = Path(dl.suggested_filename).suffix or ".pdf"
        fname = f"{date:%Y%m%d}_{safe_name(title)}{ext}"
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        dl.save_as(str(SAVE_DIR / fname))
        log(f"  ✔ {fname}")
        return True
    except PWTimeout:
        dump(popup, f"download_failed_{row_idx}")
        log(f"  ✘ 다운로드 실패: {title}")
        return False
    finally:
        popup.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", action="store_true", help="화면 구조 확인용 덤프")
    ap.add_argument("--dry-run", action="store_true", help="받을 목록만 출력")
    ap.add_argument("--since", help="YYYY-MM-DD 이후 리포트 (기본: 전 영업일)")
    args = ap.parse_args()

    if not ID or not PW:
        sys.exit(".env 에 FNGUIDE_ID / FNGUIDE_PW 를 입력하세요")
    if not LIST_URL and not args.inspect:
        sys.exit(".env 에 LIST_URL(리포트 목록 페이지 주소)을 입력하세요")

    cutoff = dt.date.fromisoformat(args.since) if args.since else prev_business_day(dt.date.today())

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS and not args.inspect)
        context = browser.new_context(accept_downloads=True, locale="ko-KR")
        page = context.new_page()
        page.on("dialog", lambda d: d.accept())  # 중복로그인 등 알림창 자동 확인

        login(page)

        if args.inspect:
            dump(page, "01_after_login")
            if LIST_URL:
                page.goto(LIST_URL, wait_until="networkidle")
                dump(page, "02_list")
                try:
                    link = page.locator(ROW_SELECTOR).first.locator(LINK_SELECTOR).first
                    with context.expect_page(timeout=15000) as pinfo:
                        link.click()
                    popup = pinfo.value
                    popup.wait_for_load_state("networkidle")
                    dump(popup, "03_popup")
                except Exception as e:
                    log(f"  첫 항목 새 창 열기 실패: {e}")
            else:
                log("LIST_URL 미설정: 열린 브라우저에서 리포트 목록으로 직접 이동해 보세요.")
                input("목록 화면에 도착하면 Enter... ")
                dump(context.pages[-1], "02_list")
            browser.close()
            return

        page.goto(LIST_URL, wait_until="networkidle")
        targets = collect_targets(page, cutoff)
        history = load_history()
        todo = [t for t in targets if f"{t[1]}|{t[2]}" not in history]
        log(f"기준일 {cutoff} 이후 리포트 {len(targets)}건, 신규 {len(todo)}건")
        if not targets:
            dump(page, "list_no_match")
            log("  날짜가 있는 행을 못 찾았습니다. ROW_SELECTOR 를 확인하세요.")

        for idx, d, title in todo:
            log(f"- {d} {title}")
            if args.dry_run:
                continue
            if download_one(context, page, idx, d, title):
                history.add(f"{d}|{title}")
                save_history(history)
        browser.close()
    log("완료")


if __name__ == "__main__":
    main()
