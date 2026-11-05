"""상태 JSON을 Drive에 올릴 수 있는 크기로 줄인다. 상세 논리는 리포트 노트에 있다.
사용: python3 -I compact.py in.json <out_prefix>  → <out_prefix>_{meta,markets,sectors,stocks}.json"""
import json, re, sys
s = json.load(open(sys.argv[1]))
RID = {}
nxt = max([int(p["rid"][1:]) for p in s["processed"] if p.get("rid")] + [0])
for p in sorted(s["processed"], key=lambda p: p["date"]):
    if not p.get("rid"):
        nxt += 1; p["rid"] = f"r{nxt}"
    RID[p.get("note_url") or p["rid"]] = p["rid"]
    RID[p["rid"]] = p["rid"]
def did(u):
    return RID.get(u, u or "")
def cut(v, n):
    if isinstance(v, list): v = "; ".join(map(str, v))
    v = str(v or "")
    return v if len(v) <= n else v[: n - 1] + "…"
KEEP = {"markets": {"view": 110, "target": 130, "prefer": 60, "avoid": 60},
        "sectors": {"view": 90, "top_picks": 70},
        "stocks": {"rating": 30, "target_price": 25, "change": 15, "valuation": 50}}
NTH = {"markets": (2, 100), "sectors": (2, 90), "stocks": (1, 70)}
for grp, keep in KEEP.items():
    for k, it in s[grp].items():
        if it.get("mention_only"):
            continue
        c = it["current"]
        n = {f: cut(c[f], lim) for f, lim in keep.items() if c.get(f)}
        th = c.get("thesis") or []
        if isinstance(th, str): th = [th]
        cnt, lim = NTH[grp]
        if th: n["thesis"] = [cut(t, lim) for t in th[:cnt]]
        rk = c.get("risks") or []
        if isinstance(rk, str): rk = [rk]
        if rk and grp != "stocks": n["risks"] = [cut(rk[0], 70)]
        for f in ("as_of", "rank"):
            if c.get(f) is not None: n[f] = c[f]
        n["analyst"] = cut(c.get("analyst"), 20); n["note"] = did(c.get("note_url") or c.get("note"))
        if c.get("filled_from"): n["filled_from"] = cut(c["filled_from"], 60)
        if c.get("mentions"): n["mentions"] = [cut(m, 60) for m in c["mentions"]]
        it["current"] = n
        hist = []
        for h in it["history"]:
            r = {"date": h["date"], "note": did(h.get("note_url") or h.get("note"))}
            for f, lim in keep.items():
                if f in ("view", "rating", "target", "target_price", "top_picks", "change") and h.get(f):
                    r[f] = cut(h[f], 40)
            hist.append(r)
        it["history"] = hist
        it["changelog"] = [{"date": c2["date"], "text": cut(c2["text"], 90)} for c2 in it["changelog"] if not c2["text"].startswith("첫 기록")]
RATING_RE = re.compile(r"매수|매도|중립|Buy|BUY|Hold|Not Rated|NR|★|Trading")
for k, it in s["stocks"].items():
    if it.get("mention_only"):
        continue
    c = it["current"]
    if not (c.get("target_price") or RATING_RE.search(c.get("rating", ""))):
        # 정식 투자의견이 없는 종목: 언급 기록만 남긴다
        ms = [f"{h['date'][5:]} {cut(h.get('rating') or '언급', 25)} {h['note']}" for h in it["history"]]
        s["stocks"][k] = {"name": it["name"], "sector": it.get("sector"), "mention_only": True, "mentions": it.get("mentions", []) + ms}
for p in s["processed"]:
    if p.get("note_url"):
        p["note"] = re.search(r"/d/([\w-]+)", p.pop("note_url")).group(1)
    p.pop("source_name", None)
out = sys.argv[2]
meta = {k: s.get(k, []) for k in ("updated", "processed", "dissent", "failed", "skipped_duplicates")}
for name, obj in (("meta", meta), ("markets", s["markets"]), ("sectors", s["sectors"]), ("stocks", s["stocks"])):
    json.dump(obj, open(f"{out}_{name}.json", "w"), ensure_ascii=False, separators=(",", ":"))
