# 상태 파일 구조

Drive `현황판` 폴더에 실행마다 4개를 새로 만든다 (일반 텍스트, 변환 없음).

| 파일 | 내용 |
|---|---|
| `state_YYYY-MM-DD_meta.json` | `updated`, `processed[]`, `dissent[]`, `failed[]`, `skipped_duplicates[]` |
| `state_YYYY-MM-DD_markets.json` | 시장 키 → 항목 |
| `state_YYYY-MM-DD_sectors.json` | 섹터 키 → 항목 |
| `state_YYYY-MM-DD_stocks.json` | 종목 키 → 항목 |

`scripts/compact.py` 가 만든다. 한 파일이 4만 자를 넘지 않게 문자열을 줄인다 (상세 논리는 리포트 노트에 있다).

## processed
```json
{"date": "2026-11-04", "type": "섹터", "title": "…", "analyst": "…", "source_id": "<원본 Drive id>", "rid": "r20", "note": "<노트 Doc id>"}
```
`rid` 는 리포트 번호(r1, r2 …). 한 번 붙이면 바꾸지 않고, 다음 실행은 가장 큰 번호 다음부터 붙인다. 다른 파일에서는 리포트를 `rid` 로만 가리킨다.

## 시장·섹터·종목 항목
```json
{
  "name": "조선",
  "sector": "shipbuilding",                 // 종목만
  "current": {
    "view": "비중확대 (유지)",               // 시장·섹터
    "target": "…", "prefer": "…", "avoid": "…", "top_picks": "…",
    "rating": "매수", "target_price": "410,000원", "change": "▲|▼|–|미기재", "valuation": "…",  // 종목
    "thesis": ["…"], "risks": ["…"],
    "as_of": "2026-11-03", "rank": 4, "analyst": "…", "note": "r14",
    "filled_from": "…",                      // 일부 항목을 이전 리포트에서 보충했을 때
    "mentions": ["…"]                        // 종목: 정식 의견이 있는 상태에서 들어온 전략·퀀트 언급
  },
  "history": [{"date": "…", "note": "r14", "view|rating": "…", "target|target_price|top_picks": "…", "change": "…"}],
  "changelog": [{"date": "…", "text": "…"}]   // "첫 기록"은 저장하지 않음. "참고 …"는 현재 의견을 바꾸지 않은 언급
}
```

정식 투자의견이 없는 종목(전략·퀀트·ETF 리포트 언급만)은 축약형으로 둔다.
```json
{"name": "삼성전자", "sector": "semiconductors", "mention_only": true, "mentions": ["10-28 비중 확대(전략 중심) r3"]}
```

## 키
- 시장: `kr`, `us`, `tw`, `em`, `global`, `asset-allocation`, `fx`, `commodities`, `macro-us`, `macro-kr`, `rates-us`, `rates-kr`, `rates-global`, `credit-kr`
- 섹터: 영문 슬러그(`semiconductors`, `shipbuilding`, `autos`, `steel-materials`, `utilities-power`, `secondary-battery`, `energy`(정유), `games-entertainment` …). 이미 있는 키를 우선 쓴다.
- 종목: 국내 6자리 코드, 해외 티커.
