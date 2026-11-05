"""extract/*.json 을 이전 상태(선택)에 병합해 새 상태를 만든다.
사용: python3 -I merge.py <prev_prefix|-> <out_full.json> <extract1.json> ...

현재 의견(current) 결정 규칙
- 시장·섹터: 리포트 등급이 높거나 같으면 교체. 기본 등급은 시장전략·섹터·기업·매크로 3, 시황·퀀트·기타 2, 종합(일간) 1.
  그 층의 담당 리포트(시장은 시장전략·매크로, 섹터·종목은 섹터·기업)는 +1, 담당 리포트이면서 연간 전망이면 다시 +1.
  더 높은 등급의 기준 리포트도 60일이 지나면 교체 허용. 교체되지 않은 리포트는 이력·논리 변화에만 남는다.
- 종목: 정식 투자의견(매수·중립·Not Rated·★ 등) 또는 목표주가가 있는 리포트만 현재 의견을 교체한다.
  전략·퀀트·ETF 리포트의 언급은 mentions 로 붙인다.
- 새 current 에 빠진 항목은 직전 current 에서 보충하고 filled_from 에 출처를 적는다.
"""
import datetime as dt, json, re, sys
prev, out, files = sys.argv[1], sys.argv[2], sys.argv[3:]
s = {}
if prev != "-":  # 이전 상태 파일 접두어: <prev>_{meta,markets,sectors,stocks}.json
    s = json.load(open(f"{prev}_meta.json"))
    for g in ("markets", "sectors", "stocks"):
        s[g] = json.load(open(f"{prev}_{g}.json"))
for k in ("markets", "sectors", "stocks"):
    s.setdefault(k, {})
s.setdefault("processed", []); s.setdefault("dissent", [])
done = {p.get("source_id") for p in s["processed"]}
reps = [r for f in files for r in json.load(open(f))["reports"] if r["processed"].get("source_id") not in done]
TYPE_RANK = {"시장전략": 3, "섹터": 3, "기업": 3, "매크로·채권·환율": 3, "시황": 2, "퀀트": 2, "기타": 2, "종합": 1}
DOMAIN = {"markets": ("시장전략", "매크로·채권·환율"), "sectors": ("섹터", "기업"), "stocks": ("섹터", "기업")}
def rank(p, grp="markets"):
    base = TYPE_RANK.get(p.get("type"), 2)
    if p.get("type") in DOMAIN[grp]:
        base += 1  # 해당 층의 담당 리포트
        if re.search(r"20\d\d.*전망", p["title"]):
            base += 1  # 연간 전망
    return base
RATING_RE = re.compile(r"매수|매도|중립|Buy|BUY|Hold|Not Rated|NR|★|Trading")
def authoritative(cur):
    return bool(cur.get("target_price")) or bool(RATING_RE.search(str(cur.get("rating") or "")))
def days(a, b):
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days
reps.sort(key=lambda r: (r["processed"]["date"], rank(r["processed"])))
HIST = {"markets": ("view", "target"), "sectors": ("view", "top_picks"), "stocks": ("rating", "target_price", "change")}
LABEL = {"view": "시각", "target": "목표", "rating": "의견", "target_price": "목표주가", "top_picks": "Top pick"}
META = ("as_of", "analyst", "note_url", "title", "rank", "filled_from", "mentions")
for r in reps:
    p = r["processed"]
    s["processed"].append(p)
    for grp in ("markets", "sectors", "stocks"):
        for key, it in (r.get(grp) or {}).items():
            rk = rank(p, grp)
            new = {f: v for f, v in (it.get("current") or {}).items() if v not in (None, "", [], {})}
            new.update(as_of=p["date"], analyst=p.get("analyst"), note_url=p.get("note_url"), title=p.get("title"), rank=rk)
            ent = s[grp].get(key)
            first = ent is None
            if first:
                ent = {"name": it.get("name", key), "current": {}, "history": [], "changelog": []}
                s[grp][key] = ent
            if ent.get("mention_only"):  # 이전엔 언급만 있던 종목
                ent.pop("mention_only"); ent.setdefault("current", {}); ent.setdefault("history", []); ent.setdefault("changelog", [])
            if grp == "stocks" and it.get("sector") and not ent.get("sector"):
                ent["sector"] = it["sector"]
            old = ent["current"]
            if first:
                replace = True
            elif grp == "stocks":
                replace = authoritative(new) or not authoritative(old)
            else:
                replace = rk >= old.get("rank", 0) or days(old.get("as_of", p["date"]), p["date"]) > 60
            if first:
                msg = f"첫 기록 — 「{p['title']}」"
            else:
                diffs = [f"{LABEL[f]} {old.get(f)} → {new.get(f)}" for f in HIST[grp]
                         if f != "change" and new.get(f) and old.get(f) and str(new[f]) != str(old[f])]
                if replace:
                    msg = f"「{p['title']}」: " + ("; ".join(diffs) if diffs else "같은 시각 유지·보강")
                else:
                    headline = new.get("view") or new.get("rating") or ""
                    msg = f"참고 「{p['title']}」" + (f": {str(headline)[:80]}" if headline else "")
            if replace:
                filled = [f for f, v in old.items() if f not in new and f not in META and v not in (None, "", [], {})]
                for f in filled:
                    new[f] = old[f]
                if filled:
                    new["filled_from"] = f"{old.get('as_of')} 「{old.get('title')}」 ({', '.join(filled)})"
                if old.get("mentions"):
                    new["mentions"] = old["mentions"]
                ent["current"] = new
            elif grp == "stocks":
                tag = new.get("rating") or "언급"
                old.setdefault("mentions", []).append(f"{p['date']} 「{p['title']}」: {tag}")
            row = {"date": p["date"], "note_url": p.get("note_url"), "title": p.get("title")}
            for f in HIST[grp]:
                row[f] = (it.get("current") or {}).get(f)
            ent["history"].append(row)
            ent["changelog"].append({"date": p["date"], "text": msg})
s["updated"] = max([p["date"] for p in s["processed"]] + [s.get("updated", "")])
json.dump(s, open(out, "w"), ensure_ascii=False, indent=1)
print(len(reps), "reports;", {k: len(s[k]) for k in ("markets", "sectors", "stocks")})
