# 신한투자증권 리서치 리포트 정독·노트 작성 지침 (서브에이전트용)

메인 세션은 이 파일을 스크래치패드 `extract/BRIEF.md` 로 복사하고, 서브에이전트에게 "BRIEF.md를 읽고 따르라"며 그룹 이름·출력 경로·배정 리포트(Drive id·파일명)만 준다.

사용자는 신한투자증권 직원이고, 회사 리서치 리포트로 "하우스뷰"를 시장·섹터·종목별로 누적 기록하려 한다. 당신은 배정된 리포트들을 끝까지 정독하고 (1) 리포트별 노트를 Google Drive에 만들고 (2) 구조화된 추출 결과를 JSON 파일로 저장한다.

## 도구
- Drive 도구는 지연 로딩이다. 먼저 ToolSearch `select:mcp__Google_Drive__read_file_content` 로 불러온다.
- 읽기: `mcp__Google_Drive__read_file_content(fileId)`. 결과가 파일로 저장되면 그 파일을 끝까지 읽는다 (Read 를 offset 으로 나눠서). 앞부분만 읽고 끝내지 않는다.
- 노트는 Drive에 올리지 않는다. `<scratchpad>/extract/<그룹>_notes/YYYY-MM-DD_<유형>_<제목>.md` 로 저장하고, JSON의 `processed.note_local` 에 경로를 적는다 (Drive 업로드는 메인 세션이 한다). Drive 파일은 읽기만 한다.

## 노트 양식 (마크다운, 한국어)
```
# YYYY-MM-DD 「리포트 제목」

| 항목 | 내용 |
|---|---|
| 유형 | 시장전략 / 시황 / 섹터 / 기업 / 매크로·채권·환율 / 퀀트 / 기타 |
| 애널리스트 | 이름 (팀) |
| 대상 | 시장·섹터·종목 |
| 시각·의견 | |
| 원본 파일 | 파일명 |

## 한 줄 결론

## 핵심 논리
1. 주장 — 근거 (수치, 기준)

## 숫자
| 항목 | 값 | 기준 |
|---|---|---|

## 섹터·종목 의견   (해당 시)
| 종목 | 투자의견 | 목표주가 (변경) | 근거 |
|---|---|---|---|

## 전략 행동
## 리스크 / 틀리는 조건
## 직전 하우스뷰와 비교
- 첫 기록. (리포트 안에서 이전 신한 의견 대비 변경을 밝혔다면 그 내용 — 예: 목표주가 상향, 의견 변경)
```
규칙: 리포트에 없는 숫자·의견은 쓰지 않는다. 숫자는 원문 단위 그대로. 범위는 반드시 `–` (en dash) 로 쓰고 `~` 는 절대 쓰지 않는다 (취소선으로 깨짐). 표 셀 안에 `|` 금지. 본문을 길게 그대로 옮기지 말고 요약. 노트 분량은 리포트 규모에 맞게 (대형 전망 리포트는 충분히 자세히, 짧은 코멘트는 짧게).

## 추출 JSON (`<scratchpad>/extract/<그룹>.json`, UTF-8)
```json
{
  "reports": [
    {
      "processed": {"date": "2026-11-05", "type": "섹터", "title": "…", "analyst": "홍길동", "source_id": "<Drive id>", "source_name": "…pdf", "note_local": "<노트 경로>"},
      "markets": {"kr": {"name": "한국", "current": {"view": "…", "target": "…", "thesis": ["…"], "prefer": ["…"], "avoid": ["…"], "risks": ["…"]}}},
      "sectors": {"shipbuilding": {"name": "조선", "current": {"view": "비중확대", "cycle": "…", "thesis": ["…"], "top_picks": ["…"], "avoid": [], "catalysts": ["…"], "risks": ["…"]}}},
      "stocks": {"009540": {"name": "HD한국조선해양", "sector": "shipbuilding", "current": {"rating": "매수", "target_price": "…원", "change": "▲|▼|–|신규", "base_price": "…", "upside": "…", "valuation": "…", "thesis": ["…"], "catalysts": ["…"], "risks": ["…"], "estimates": [{"year": "2027F", "revenue": "…", "op": "…", "ni": "…", "eps": "…", "vs_cons": "…"}]}}},
      "notes": "이 리포트가 다른 신한 리포트와 충돌할 수 있는 지점, 기타 메모 (선택)"
    }
  ]
}
```
- 리포트가 다루는 층만 채운다. 비어 있는 키는 생략. 각 current 에 as_of/analyst/note_url 은 넣지 않아도 된다 (병합 시 processed 에서 채움).
- 시장 키: `kr`(한국 주식), `us`(미국 주식), `tw`(대만), `em`(신흥국), `global`, `rates-kr`(국내 금리·채권), `rates-us`(미국 금리·채권), `credit-kr`(국내 크레딧), `macro-us`(미국 경제·연준), `macro-kr`(한국 경제·물가), `fx`, `commodities`, `asset-allocation`(자산배분).
- 섹터 키(영문 슬러그, 가능하면 이 목록 사용): `semiconductors`, `shipbuilding`, `autos`, `chemicals`, `utilities-power`(전력·유틸리티), `electrical-equipment-ess`(전자장비·ESS·2차전지 소재 제외), `secondary-battery`, `games-entertainment`, `internet`, `defense`, `banks`, `insurance`, `securities`, `bio-healthcare`, `steel-materials`, `construction`, `consumer`, `telecom`, `machinery`, `energy`, `software`, `us-tech` 등. 없으면 새 슬러그를 만든다.
- 종목 키: 국내는 6자리 종목코드(리포트에 있으면 그대로, 없으면 아는 코드), 해외는 티커(예 `NVDA`, `2330.TW`). 확실하지 않으면 키를 `?<종목명>` 으로 둔다.
- 투자의견·목표주가는 리포트에 적힌 그대로. 시장전략·퀀트·ETF 리포트가 종목을 예시로 들거나 Top pick 으로 꼽은 경우: 투자의견이 없으면 rating 은 "선호(전략)" 같이 리포트 표현대로 적고 target_price 는 비운다.
- 마지막 응답(당신의 최종 메시지)은 짧게: 처리한 리포트별 한 줄(제목·시각·핵심 숫자 1개·노트 경로), 읽기 실패/잘림 여부. 상세는 JSON과 노트에.
