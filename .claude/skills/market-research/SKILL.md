---
name: market-research
description: Google Drive '주식전략' 폴더에 올라온 증권사 주식시황·주식전략 리포트(PDF)를 정독해 전반적 화두와 의견을 종합하고, 증권사·애널리스트별 요약과 리포트 간 공통점·차이점을 정리하며, 리포트의 사실 주장을 외신(FT·WSJ·Economist·Barron's) 아침 브리핑과 대조해 팩트체크한다. 매일 오전 리서치 브리핑, 또는 "오늘 시황/전략 리포트 정리" 요청 시 사용.
---

# 증권사 시황·전략 리포트 일일 브리핑

## 입력
| 무엇 | 어디서 |
|---|---|
| 증권사 리포트 PDF | Google Drive 폴더 `주식전략` (id `1MgqvsYEPdG05oBmor4DqE-LkrB-M3oay`). 사용자가 FnGuide 등에서 직접 내려받아 올린다. 파일명 규칙 `증권사_카테고리_제목_YYYYMMDD.pdf` (해외 IB는 `JPM_..._YYYY-MM-DD_...pdf` 처럼 다를 수 있음) |
| 외신 기사 (팩트체크 기준) | 예약 작업 "Morning news briefing" (`trig_01QAUD51gvmjVVXUxPC2WHRq`, 매일 05:30 KST) 의 최신 실행 결과. `get_trigger` → `last_run.session_id` → `list_events(kinds=["result"])` 의 `result` 텍스트 |

FnGuide에 자동 로그인해 수집하지 않는다. 사이트가 자동 접속을 차단하고, 비정상 이용 감지 시 계정이 무기한 정지될 수 있다.

## 1. 대상 리포트 고르기
- `search_files` 로 `parentId = '<폴더 id>' and createdTime > '<전날 09:30 KST의 UTC 시각>'` 를 조회한다 (페이지 끝까지).
- 새 파일이 0건이면 "오늘 새 리포트 없음"만 출력하고 끝낸다. 결과를 지어내지 않는다.
- 파일명의 발간일이 3일 이상 지난 리포트는 포함하되 브리핑에 "(발간일 YYYY-MM-DD, 참고용)"으로 표시한다.

## 2. 정독
`read_file_content` 로 각 PDF를 끝까지 읽는다. 리포트가 많으면 서브에이전트에 4~5건씩 나눠 맡긴다. 리포트별로 뽑을 것:
- 증권사, 애널리스트, 카테고리(시황/전략), 제목, 발간일
- 시장 시각(강세/중립/약세)과 핵심 주장
- 근거 수치(지수 밴드·목표치, 수급, 금리·환율, 실적) — 단위·기간·기준을 원문 그대로
- 선호/비선호 업종·종목, 리스크
- 리포트가 사실로 제시한 외부 사건·지표·일정 (팩트체크 대상)

## 3. 팩트체크
기준은 FT·WSJ·Economist 공개 RSS(제목·요약). `python3 -I .claude/skills/market-research/scripts/fetch_news.py` → `data/news/<날짜>.json`. 로그인하지 않는다. Barron's는 공개 피드가 없다.
- 판정: bad(불일치) / part(확인 필요) / ok(일치). 요약에 없는 세부 수치는 판정하지 않고 unchecked 로 둔다.
- 전망·의견은 대상이 아니다. 리포트 문장과 외신 근거(매체·링크)를 나란히 적고, 리포트끼리도 교차검증한다.
- 피드가 모두 실패하면 그 사실만 적는다. 다른 매체로 대체하지 않는다.

## 4. 브리핑 페이지 갱신
브리핑은 문서가 아니라 페이지(Artifact) https://claude.ai/artifact/QKoaRvx6GgTPkVQ4pNSBiH 로 낸다. 원본은 `briefing/index.html`.
- 페이지 안 `<script type="application/json" id="brief-data">` 블록의 JSON만 오늘 내용으로 바꾸고 같은 url 로 다시 게시한다. HTML/CSS/JS는 건드리지 않는다.
- 구성: 오늘의 결론 3개 → 시각 분포 → KOSPI 밴드 → S&P 500 목표 레인지 → 의견이 갈리는 곳 → 이번 주 일정 → 증권사별 한 줄(펼치면 3개 포인트) → 팩트체크(불일치·확인 필요만 펼쳐 보이고, 일치는 접어 둠).
- 원칙: 모든 주장 옆에 증권사/애널리스트. 짧은 문장, 숫자는 원문 그대로. 리포트에 없는 해석은 쓰지 않는다. 범위는 `–` 로 쓴다.
