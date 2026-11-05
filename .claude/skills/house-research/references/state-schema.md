# 상태 파일 구조 (`state_YYYY-MM-DD.json`)

```json
{
  "updated": "2026-11-05",
  "processed": [
    {"date": "2026-11-04", "type": "기업", "title": "…", "analyst": "…",
     "source_id": "<원본 Drive id>", "source_name": "…pdf", "note_url": "https://docs.google.com/…"}
  ],
  "markets": {
    "kr": {
      "name": "한국",
      "current": {"view": "중립", "target": "KOSPI 4Q26 5,000–6,000", "thesis": ["…"],
                  "prefer": ["반도체"], "avoid": [], "risks": ["…"],
                  "as_of": "2026-11-04", "analyst": "…", "note_url": "…"},
      "history": [{"date": "2026-11-04", "view": "중립", "target": "…", "note_url": "…"}],
      "changelog": [{"date": "2026-11-04", "text": "…"}]
    }
  },
  "sectors": {
    "semiconductors": {
      "name": "반도체",
      "current": {"view": "비중확대", "cycle": "…", "thesis": ["…"], "top_picks": ["SK하이닉스"],
                  "avoid": [], "catalysts": ["…"], "risks": ["…"],
                  "as_of": "…", "analyst": "…", "note_url": "…"},
      "history": [{"date": "…", "view": "…", "top_picks": ["…"], "note_url": "…"}],
      "changelog": [{"date": "…", "text": "…"}]
    }
  },
  "stocks": {
    "000660": {
      "name": "SK하이닉스", "sector": "semiconductors",
      "current": {"rating": "매수", "target_price": "1,000,000원", "change": "▲",
                  "base_price": "…", "upside": "…", "valuation": "12MF P/B 2.5배",
                  "thesis": ["…"], "catalysts": ["…"], "risks": ["…"],
                  "estimates": [{"year": "2026E", "revenue": "…", "op": "…", "ni": "…", "eps": "…", "vs_cons": "…"}],
                  "as_of": "…", "analyst": "…", "note_url": "…"},
      "history": [{"date": "…", "rating": "매수", "target_price": "…", "change": "▲", "note_url": "…"}],
      "changelog": [{"date": "…", "text": "…"}]
    }
  },
  "dissent": [{"date": "…", "topic": "…", "a": "전략팀(홍길동): …", "b": "반도체(김철수): …"}]
}
```

- 키: 시장 `kr|us|cn|jp|eu|em|global|rates|fx|commodities`, 섹터는 영문 슬러그, 종목은 티커(국내 6자리 코드, 해외 티커).
- `change`: ▲ 상향 / ▼ 하향 / – 유지 / 신규.
- 값은 원문 단위 그대로 문자열로 둔다. 모르는 필드는 비워 두거나 뺀다.
