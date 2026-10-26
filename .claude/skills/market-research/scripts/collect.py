"""FnGuide 리서치 리포트 수집기.

로그인 → 카테고리별 목록 → 당일(또는 --date) 발간 리포트 PDF 다운로드 → 텍스트 추출.
결과는 data/<date>/ 아래에 저장하고 manifest.json 에 메타데이터를 남긴다.

사용:
    python3 collect.py                 # 오늘(KST) 리포트 수집
    python3 collect.py --date 2026-10-26
    python3 collect.py --discover      # 로그인 후 리서치 페이지 스냅샷만 저장 (목록 구조 확인용)
    python3 collect.py --force-login   # 다른 기기 로그인이 있어도 이 세션으로 로그인 (다른 기기는 로그아웃됨)
"""

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from pypdf import PdfReader

SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = SKILL_DIR.parent.parent.parent
KST = dt.timezone(dt.timedelta(hours=9))
BASE = "https://www.fnguide.com"

# /Users/UserLogin 응답 코드 (사이트 login 스크립트 기준)
LOGIN_ERRORS = {
    "80111": "아이디 또는 비밀번호 오류",
    "80112": "아이디 또는 비밀번호 오류 (10회 누적 시 잠김)",
    "80114": "허용되지 않은 IP",
    "80115": "다른 기기에 로그인되어 있음",
    "80116": "다른 기기에 로그인되어 있음",
    "80117": "지정 PC가 아님",
    "80118": "로그인 10회 오류로 잠김",
    "80199": "비정상 이용 감지로 계정 이용 제한",
}


def get(session, url, **kw):
    """연결이 가끔 끊기므로 짧게 재시도한다."""
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30, **kw)
            resp.raise_for_status()
            return resp
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def encrypt_password(public_key_pem, password):
    # 사이트와 동일: forge RSA-OAEP(SHA-256, MGF1 SHA-256) → base64
    body = re.sub(r"-----(BEGIN|END) PUBLIC KEY-----|\s", "", public_key_pem)
    pem = "-----BEGIN PUBLIC KEY-----\n" + "\n".join(body[i:i + 64] for i in range(0, len(body), 64)) + "\n-----END PUBLIC KEY-----\n"
    key = serialization.load_pem_public_key(pem.encode())
    cipher = key.encrypt(password.encode(), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    return base64.b64encode(cipher).decode()


def login(session, force=False):
    user, pw = os.environ.get("FNGUIDE_ID"), os.environ.get("FNGUIDE_PW")
    if not user or not pw:
        sys.exit("FNGUIDE_ID / FNGUIDE_PW 환경 변수가 없습니다. 클라우드 환경 설정에 추가한 뒤 새 세션에서 실행하세요.")
    page = get(session, f"{BASE}/Users/Login").text
    m = re.search(r'publicKey\s*=\s*"([^"]+)"', page)
    if not m:
        sys.exit("로그인 페이지에서 공개키를 찾지 못했습니다. 사이트 로그인 방식이 바뀌었는지 확인하세요.")
    data = {"loginType": "2" if force else "", "userId": user, "userPassword": encrypt_password(m.group(1), pw)}
    resp = session.post(f"{BASE}/Users/UserLogin", files={k: (None, v) for k, v in data.items()}, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    code = str(result.get("returnCode"))
    if code != "0":
        reason = LOGIN_ERRORS.get(code, result.get("returnMessage") or "알 수 없는 오류")
        hint = " (--force-login 으로 다시 실행하면 다른 기기는 로그아웃됩니다)" if code in ("80115", "80116") else ""
        sys.exit(f"로그인 실패 [{code}]: {reason}{hint}")


def snapshot(html, out_dir, name):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.html").write_text(html, encoding="utf-8")


def slug(text, limit=60):
    return re.sub(r"[^\w가-힣-]+", "_", text).strip("_")[:limit] or "report"


def text_of(row, selector):
    el = row.select_one(selector) if selector else None
    return el.get_text(" ", strip=True) if el else ""


def pdf_text(path):
    try:
        return "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
    except Exception as e:  # 손상/암호화 PDF는 건너뛰고 기록만 남긴다
        return f"[텍스트 추출 실패: {e}]"


def collect_category(session, cat, date, out_dir):
    sel = cat.get("selectors") or {}
    html = get(session, cat["list_url"]).text
    if not sel.get("row"):
        snapshot(html, out_dir / "_discover", cat["id"])
        print(f"[{cat['name']}] selectors 미설정 → 스냅샷만 저장: {out_dir / '_discover'}")
        return []

    reports = []
    for row in BeautifulSoup(html, "html.parser").select(sel["row"]):
        item = {k: text_of(row, sel.get(k)) for k in ("date", "title", "broker", "analyst")}
        if date not in re.sub(r"[./]", "-", item["date"]):
            continue
        item["category"] = cat["name"]
        link = row.select_one(sel["link"]) if sel.get("link") else None
        href = link.get("href") if link else None
        if href:
            url = href if href.startswith("http") else f"{BASE}{href}"
            item["url"] = url
            base = out_dir / cat["id"] / slug(f"{item['broker']}_{item['analyst']}_{item['title']}")
            resp = get(session, url)
            if "pdf" in resp.headers.get("content-type", ""):
                pdf = base.with_suffix(".pdf")
                pdf.parent.mkdir(parents=True, exist_ok=True)
                pdf.write_bytes(resp.content)
                base.with_suffix(".txt").write_text(pdf_text(pdf), encoding="utf-8")
                item["text_file"] = str(base.with_suffix(".txt").relative_to(REPO_DIR))
            else:
                item["note"] = f"PDF가 아닌 응답 ({resp.headers.get('content-type')})"
            time.sleep(1)  # 서버에 부담을 주지 않도록 천천히 받는다
        reports.append(item)
    print(f"[{cat['name']}] {date} 리포트 {len(reports)}건")
    return reports


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.datetime.now(KST).strftime("%Y-%m-%d"))
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--force-login", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load((SKILL_DIR / "config.yaml").read_text(encoding="utf-8"))
    out_dir = REPO_DIR / "data" / args.date

    session = requests.Session()
    login(session, force=args.force_login)
    manifest = []
    for cat in cfg["categories"]:
        if args.discover:
            cat = {**cat, "selectors": {}}
        manifest += collect_category(session, cat, args.date, out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest: {out_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
