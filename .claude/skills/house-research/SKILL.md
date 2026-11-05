---
name: house-research
description: 사용자가 다니는 회사(신한투자증권) 리서치 리포트를 Google Drive '신한리서치' 폴더에서 정독해 시장·섹터·종목별 전략을 분석하고, 결과를 Drive '신한리서치 기록' 폴더에 누적 기록한다(리포트 노트 + 날짜별 현황판 3종 + 상태 파일 4종: 하우스뷰, 의견·목표 이력, 논리 변화, 하우스 내 이견). "회사 리포트 정리", "자사 리서치 정리", "신한리서치 올렸어" 요청 시 사용. 타 증권사 시황·전략 일일 브리핑은 market-research 스킬이다.
---

# 자사 리서치 리포트 분석·기록

목표는 한 번 읽고 끝나는 요약이 아니라 **하우스뷰가 시간에 따라 어떻게 바뀌는지 추적 가능한 기록**이다.

**기록은 전부 Google Drive에 둔다. 저장소(공개)에는 리포트 내용·노트·원본을 커밋하지 않는다.** 작업 파일은 스크래치패드에만 둔다.

## 위치
| 용도 | Drive 폴더 | id |
|---|---|---|
| 입력: 사용자가 리포트를 올리는 곳 | `신한리서치` | `1lwsoUxQnX0LcTWo2lviPLaPKZsToRGvN` |
| 출력 루트 | `신한리서치 기록` | `1uWwGUZOMeYyK3fgfgFq9czaPNzWNwP1W` |
| 리포트별 노트 (Google Doc) | `신한리서치 기록/리포트 노트` | `1LaJHae2j--VmnhRE7UDQZtln8wcSWDh9` |
| 현황판 + 상태 파일 | `신한리서치 기록/현황판` | `1GQH2qbpyf0L4bc6V3TSkyBrnGYuBCaAI` |

## 기록 방식: 고치지 않고 쌓는다
Google Docs 편집 커넥터가 없어 Drive로 **새 파일 생성만** 한다.
- 리포트 노트는 리포트당 1개를 만들고 다시 고치지 않는다.
- 실행마다 `현황판` 폴더에 **현황판 3개**(`현황판 YYYY-MM-DD`, `… 시장·섹터 상세`, `… 종목`, Google Doc)와 **상태 파일 4개**(`state_YYYY-MM-DD_{meta,markets,sectors,stocks}.json`, 일반 텍스트)를 새로 만든다. 같은 날 두 번째 실행이면 날짜 뒤에 `_2` 를 붙인다.
- 이전 현황판·상태 파일은 지우지 않는다 (그 자체가 이력이다).
- `create_file` 은 내용을 호출에 그대로 싣는다. 파일 하나가 4만 자를 넘지 않게 한다 (`compact.py`·`render_board.py` 가 그렇게 나눈다).

## 1. 대상 고르기
1. `search_files` 로 `parentId = '1lwsoUxQnX0LcTWo2lviPLaPKZsToRGvN'` 를 `nextPageToken` 이 없을 때까지 조회한다 (하위 폴더도). id 중복을 제거한다.
2. `현황판` 폴더에서 가장 최근 날짜의 `state_*_{meta,markets,sectors,stocks}.json` 4개를 `read_file_content` 로 읽어 스크래치패드에 `prev_{meta,…}.json` 으로 저장한다. 없으면 첫 실행이다.
3. `meta.processed[].source_id`, `skipped_duplicates`, `failed` 와 비교해 새 파일만 고른다. `failed` 에 있던 리포트는 다시 시도한다. 파일명·크기가 같은 중복 업로드(`… (1).pdf`)는 하나만 처리하고 `skipped_duplicates` 에 적는다.
4. 새 파일이 없으면 "새 리포트 없음"만 말하고 끝낸다.

## 2. 정독과 추출 (서브에이전트)
- `references/extract-brief.md` 를 스크래치패드 `extract/BRIEF.md` 로 복사한다. 리포트를 성격별로 4–6건씩 묶어 서브에이전트(general-purpose)에 맡긴다. 각 프롬프트에는 BRIEF 경로, 그룹 이름, 출력 JSON 경로, 배정 리포트(Drive id·파일명), 그룹별 중점만 쓴다.
- **서브에이전트는 Drive에 쓰지 않는다.** 노트는 스크래치패드에 마크다운으로, 추출 결과는 `extract/<그룹>.json` 으로 남긴다 (서브에이전트의 Drive 쓰기는 권한 확인에서 막힌다).
- 텍스트가 잘리거나(대형 PDF는 80쪽 안팎에서 끊긴다) 읽히지 않는 리포트는 노트에 범위를 밝히고, 아예 못 읽은 것은 `failed` 에 사유와 함께 남긴다.

## 3. 리포트 노트 올리기 (메인 세션)
노트 파일을 읽어 `create_file`(`parentId` = 리포트 노트 폴더, `contentMimeType: "text/markdown"`, 제목 = 파일명에서 `.md` 제외)로 올린다. 결과 id 로 각 `extract/*.json` 의 `processed.note_url` 을 `https://docs.google.com/document/d/<id>/edit` 로 채운다.

## 4. 병합 → 현황판
1. 검토: 종목코드 오류·중복 키(같은 종목 두 코드), 엉뚱한 층에 들어간 항목(예: 은행채 → 은행주 섹터)을 `extract/*.json` 에서 고친다.
2. 병합: `python3 -I <skill>/scripts/merge.py <prev 접두어|-> state.json extract/*.json`
   - 현재 의견은 리포트 등급으로 정한다: 그 층 담당 리포트(시장은 시장전략·매크로, 섹터·종목은 섹터·기업) +1, 담당 연간 전망 +1 더. 종목은 정식 투자의견이나 목표주가가 있는 리포트만 현재 의견을 바꾼다. 전략·퀀트 언급은 `mentions` 로 붙는다.
3. 이견·이름: `overlay.json`(`dissent`, `failed`, `skipped_duplicates`, 섹터 표시 이름)을 직접 써서 `state.json` 에 덮는다. 이견은 이전 `meta.dissent` 를 이어받고 새로 생긴 것을 더한다. **같은 회사 안에서 리포트끼리 시각이 다른 곳**(예: 전략팀 비중 축소 vs 업종 애널리스트 비중확대, 3개월 vs 연간 시계)을 양쪽 출처와 함께 적고, 어느 쪽이 맞는지는 쓰지 않는다.
4. 축약: `python3 -I <skill>/scripts/compact.py state.json st` → `st_{meta,markets,sectors,stocks}.json`
5. 렌더: `python3 -I <skill>/scripts/render_board.py st out` → `out/board_main.md`, `board_detail.md`, `board_stocks.md`
6. `현황판` 폴더에 상태 파일 4개(`contentMimeType: "text/plain"`, `disableConversionToGoogleType: true`)와 현황판 3개(`text/markdown`)를 만든다. 상태 파일은 결과의 `fileSize` 가 로컬 바이트 수와 같은지 확인한다.
7. `현황판 YYYY-MM-DD` 를 `read_file_content` 로 다시 읽어 표가 깨지지 않았는지 확인한다.

## 4-1. 전망 장부와 인뎁스 상세 (정독 단계에서 함께)
서브에이전트에 `references/extract-brief.md` 와 함께 `references/ledger-depth-brief.md` 를 준다.
- **전망 장부:** 리포트마다 검증 가능한 전망을 한 줄씩(대상 유형·대상·지표·범위/점/방향/의견·단위·기간·검증 시점 `due`·기준값·원문·근거·검증 방법). 자산·국가·섹터·종목·매크로를 모두 담는다. 장부의 줄은 지우지 않는다. 같은 대상의 새 전망은 새 줄로 쌓고, 예전 줄은 `superseded_by` 로 잇는다.
- **인뎁스 상세:** 본문 7쪽 이상이면 executive summary, 현재 상황(애널리스트 기술), 전망, 판단 근거, caveat 다섯 칸을 채운다.
- **인뎁스 차트:** 숫자의 변동은 글로만 쓰지 않는다. 장부에서 시점별·항목별 수치를 골라 `depth_charts` 데이터(`{rid, chart, chart_title, chart_type, unit, series, x, x_order, value, low, high, note, fid}`)로 만든다. 대시보드는 이것을 '3. 전망' 아래에 그린다.
  - 분기·연도 경로(금리, 스프레드, 정제마진, 유가) → `line`
  - 연도·국가·기업 비교(EPS 성장률, 영업이익) → `bar`, 항목이 8개 넘거나 이름이 길면 `hbar`
  - 밴드·시나리오(지수 범위, 상방·기본·하방) → `range`(범위) + `bar`(시나리오 점)
  - 단위가 섞인 가정치·목표주가 묶음 → `table`
  - 모든 점에 근거 장부 번호(`fid`)를 남긴다.

## 4-2. 외신 대조
`python3 -I .claude/skills/market-research/scripts/fetch_news.py --hours 240 --out <scratchpad>/news.json` 과, 가능하면 예약 작업 "Morning news briefing" 결과를 읽는다. 아직 유효한 리포트의 전제·전망 가운데 외신이 다룬 것을 대조해 `{rids, topic, claim, now, change(변화|확인|새 변수|판단 보류), implication, source, url, date}` 로 남긴다. 외신 요약에 없는 수치는 지어내지 않는다.

## 4-3. 사후 검증
매 실행마다 장부에서 `due` 가 지난 줄을 골라 실제 값을 찾는다(지수·금리·환율·주가: 공개 시세나 연결된 데이터 도구, 실적: 발표 자료). `actual`, `actual_date`, `verdict`(적중|부분 적중|빗나감|판단 불가), `verify_note` 를 채운다. 범위 전망은 범위 안이면 적중, 점 전망은 오차율을 적는다. 찾은 값의 출처를 남기고, 값을 못 찾으면 판단 불가로 둔다.

## 4-4. 대시보드 갱신 (증분)
대시보드 https://claude.ai/artifact/Eun9PzUVEkMyLZqzYB8r2M (Dashboard 유형, 비공개). 섹터·전략은 매일 바뀌지 않으므로 **새로 올린 리포트가 기존 내용을 대체할 때만 바꾸고, 그 밖에는 추가만 한다.**
- 바꾸는 경우: 같은 대상의 의견·밴드·목표주가가 새 리포트로 바뀌었을 때(그 줄만 교체하고 변경 이력에 남김), 내러티브의 장이 새 리포트로 뒤집히거나 보강될 때(그 장만 고쳐 쓰고 근거 rid 를 더함)
- 추가하는 경우: 새 리포트 카드·투자 포인트·장부 줄·인뎁스 상세·외신 대조
- 그대로 두는 경우: 새 리포트가 기존 판단을 반복하거나 다루지 않는 영역
- 일간 자료(신한 생각, 주간 시황)만 들어온 날은 리포트 카드·장부·외신 대조만 추가하고 내러티브·섹터 표는 손대지 않는다.
- 각 데이터 파일을 새로 만들어 `asset: true` 로 올리고 해당 `datasets/<id>` 의 `source.url`·`updated`·`edit` 를 `update` 한다. 페이지(`files/index.html`)는 새 탭·표가 필요할 때만 고친다.
- 데이터 파일: `reports`, `points`, `forecasts`, `narrative`, `sectors`, `dissent`, `tp_changes`, `ledger`, `depth`, `depth_meta`, `depth_charts`, `news_check`
- 이 파일들의 원본은 대시보드 첨부 파일이다(장부가 커서 Drive 상태 파일에는 넣지 않는다). 다음 실행은 `Artifact` `action: "read"`, `path: "<asset id>"` 로 내려받아 이어 쓴다. asset id 는 `datasets/<id>` 문서의 `source.url` 에 있다.

## 5. 보고
바뀐 하우스뷰(의견·목표주가 변경, 새 커버리지, 하우스 내 이견), 읽지 못했거나 잘린 리포트, 노트에 있는 계산값 등 원문에 없는 내용을 짧게 보고하고 현황판을 링크한다. 저장소에는 아무것도 커밋하지 않는다 (스킬 자체를 고친 경우만 예외).

## 원칙
- 리포트에 없는 숫자·의견은 쓰지 않는다. 역산한 값은 쓰지 않거나 "계산값"이라고 밝힌다.
- 숫자는 원문 단위 그대로, 범위는 `–` 로 쓴다 (`~` 는 마크다운 변환 시 취소선으로 깨진다).
- 모든 판단 옆에 애널리스트와 발간일(또는 리포트 번호)을 붙인다.
