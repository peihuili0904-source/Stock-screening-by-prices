"""상태 파일(<prefix>_{meta,markets,sectors,stocks}.json)로 현황판 마크다운 2개를 만든다.

사용: python3 -I render_board.py <prefix> <out_dir>
  → <out_dir>/board_main.md   (개요: 시장·섹터 의견표, 이견, 최근 변화, 처리한 리포트)
  → <out_dir>/board_detail.md (시장·섹터 상세: 논리, 이력, 논리 변화)
  → <out_dir>/board_stocks.md (종목: 정식 의견 종목 상세 + 언급 종목 목록)
"""

import json
import os
import sys

DOC = "https://docs.google.com/document/d/{}/edit"


def load(prefix):
    s = json.load(open(f"{prefix}_meta.json", encoding="utf-8"))
    for g in ("markets", "sectors", "stocks"):
        s[g] = json.load(open(f"{prefix}_{g}.json", encoding="utf-8"))
    return s


def cell(v):
    if v is None:
        return ""
    if isinstance(v, list):
        v = ", ".join(str(x) for x in v)
    return str(v).replace("|", "/").replace("\n", " ").replace("~", "–")


def table(head, rows):
    out = ["", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out + [""]


class Ref:
    def __init__(self, processed):
        self.p = {p["rid"]: p for p in processed}

    def link(self, rid, text=None):
        p = self.p.get(rid)
        if not p:
            return cell(text or rid)
        return f"[{cell(text or p['title'])}]({DOC.format(p['note'])})"

    def short(self, rid):
        return rid if rid in self.p else ""

    def src(self, cur):
        p = self.p.get(cur.get("note"))
        if not p:
            return ""
        line = f"> 기준: {cur['note']} {p['date']} 「{cell(p['title'])}」 · {cell(cur.get('analyst'))}"
        if cur.get("filled_from"):
            line += f"  \n> 일부 항목 보충: {cell(cur['filled_from'])}"
        return line


def bullets(label, v):
    if not v:
        return []
    if isinstance(v, list):
        return [f"- {label}:"] + [f"  - {cell(x)}" for x in v]
    return [f"- {label}: {cell(v)}"]


def item(ref, key, it, fields, hist_cols):
    cur = it.get("current", {})
    o = [f"### {cell(it.get('name', key))} ({key})", "", ref.src(cur), ""]
    for label, f in fields:
        o += bullets(label, cur.get(f))
    if cur.get("mentions"):
        o += bullets("전략·퀀트 언급", cur["mentions"])
    hist = it.get("history", [])
    if len(hist) > 1:
        o += table(["날짜"] + [h for h, _ in hist_cols] + ["리포트"],
                   [[h["date"][5:]] + [cell(h.get(k)) for _, k in hist_cols] + [ref.short(h.get("note"))] for h in hist])
    if it.get("changelog"):
        o += ["", "논리 변화", ""] + [f"- {c['date'][5:]}: {cell(c['text'])}" for c in reversed(it["changelog"])]
    return o + [""]


def main():
    s = load(sys.argv[1])
    out_dir = sys.argv[2]
    ref = Ref(s["processed"])
    mk, sc, st = s["markets"], s["sectors"], s["stocks"]
    rated = {k: v for k, v in st.items() if not v.get("mention_only")}
    ment = {k: v for k, v in st.items() if v.get("mention_only")}
    upd = s.get("updated", "")

    o = [f"# 신한리서치 현황판 {upd}", "",
         f"처리한 리포트 {len(s['processed'])}건 · 시장 {len(mk)} · 섹터 {len(sc)} · 정식 의견 종목 {len(rated)} · 언급 종목 {len(ment)}. "
         "시장·섹터 상세와 종목은 같은 날짜의 「현황판 … 시장·섹터 상세」, 「현황판 … 종목」 문서. r1, r2 … 는 맨 아래 「처리한 리포트」 표의 번호이며, 상세 논리·숫자는 그 리포트 노트에 있다.", ""]
    o += ["## 시장별 하우스뷰"]
    o += table(["시장", "시각", "밴드·목표", "기준"],
               [[cell(m["name"]), cell(m["current"].get("view")), cell(m["current"].get("target")), ref.short(m["current"].get("note"))]
                for m in mk.values()])
    o += ["## 섹터 의견"]
    o += table(["섹터", "의견", "Top pick", "기준"],
               [[cell(x["name"]), cell(x["current"].get("view")), cell(x["current"].get("top_picks")), ref.short(x["current"].get("note"))]
                for x in sc.values()])
    o += ["## 하우스 내 이견", "", "같은 회사 안에서 리포트끼리 시각이 다른 곳. 어느 쪽이 맞는지는 판단하지 않는다."]
    o += table(["쟁점", "의견 A", "의견 B"], [[cell(d["topic"]), cell(d["a"]), cell(d["b"])] for d in s.get("dissent", [])])
    changes = []
    for group, items in (("시장", mk), ("섹터", sc), ("종목", rated)):
        for k, it in items.items():
            for c in it.get("changelog", []):
                if c["text"].startswith("참고") or "같은 시각 유지" in c["text"]:
                    continue
                changes.append((c["date"], f"{group} · {cell(it.get('name', k))}", cell(c["text"])))
    changes.sort(key=lambda r: r[0], reverse=True)
    o += ["## 최근 변화 (현재 의견을 바꾼 것만, 최신순)"] + table(["날짜", "대상", "내용"], [(d[5:], a, b) for d, a, b in changes[:40]])
    tail = ["## 처리한 리포트"] + table(["#", "날짜", "유형", "제목", "애널리스트"],
               [[p["rid"], p["date"], cell(p.get("type")), ref.link(p["rid"], p["title"]), cell(p.get("analyst"))]
                for p in sorted(s["processed"], key=lambda p: p["date"], reverse=True)])
    if s.get("failed"):
        tail += ["## 읽지 못한 리포트"] + table(["날짜", "제목", "사유"], [[f["date"], cell(f["title"]), cell(f["reason"])] for f in s["failed"]])
    main_doc = o + tail
    o = [f"# 신한리서치 현황판 {upd} 시장·섹터 상세", "", "r1, r2 … 는 「현황판 " + upd + "」 문서의 「처리한 리포트」 번호.", ""]
    o += ["## 시장 상세", ""]
    for k, m in mk.items():
        o += item(ref, k, m, [("시각", "view"), ("밴드·목표", "target"), ("핵심 논리", "thesis"), ("선호", "prefer"),
                              ("비선호", "avoid"), ("리스크", "risks")], [("시각", "view"), ("밴드·목표", "target")])
    o += ["## 섹터 상세", ""]
    for k, x in sc.items():
        o += item(ref, k, x, [("의견", "view"), ("Top pick", "top_picks"), ("핵심 논리", "thesis"), ("리스크", "risks")],
                  [("의견", "view"), ("Top pick", "top_picks")])

    t = [f"# 신한리서치 현황판 {upd} 종목", "", "정식 투자의견(매수·중립·Not Rated·★ 등)이나 목표주가가 있는 종목은 상세, 전략·퀀트·ETF 리포트에서 언급만 된 종목은 목록으로 둔다. r1, r2 … 는 아래 「리포트 번호」 표 참조.", ""]
    t += ["## 정식 의견 종목"]
    t += table(["종목", "섹터", "의견", "목표주가", "변경", "기준"],
               [[f"{cell(x['name'])} ({k})", cell(sc.get(x.get("sector"), {}).get("name", x.get("sector"))),
                 cell(x["current"].get("rating")), cell(x["current"].get("target_price")), cell(x["current"].get("change")),
                 ref.short(x["current"].get("note"))] for k, x in sorted(rated.items(), key=lambda kv: str(kv[1].get("sector")))])
    t += ["## 언급 종목 (정식 의견 없음)"]
    t += table(["종목", "섹터", "언급"],
               [[f"{cell(x['name'])} ({k})", cell(sc.get(x.get("sector"), {}).get("name", x.get("sector"))),
                 "; ".join(cell(m) for m in x.get("mentions", []))]
                for k, x in sorted(ment.items(), key=lambda kv: str(kv[1].get("sector")))])
    t += ["## 리포트 번호"] + table(["#", "날짜", "리포트 노트"], [[p["rid"], p["date"], ref.link(p["rid"])] for p in sorted(s["processed"], key=lambda p: p["date"], reverse=True)])
    t += ["## 종목 상세", ""]
    for k, x in sorted(rated.items(), key=lambda kv: str(kv[1].get("sector"))):
        t += item(ref, k, x, [("투자의견", "rating"), ("목표주가", "target_price"), ("변경", "change"),
                              ("밸류에이션", "valuation"), ("투자 포인트", "thesis")],
                  [("의견", "rating"), ("목표주가", "target_price"), ("변경", "change")])

    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "board_main.md"), "w", encoding="utf-8").write("\n".join(main_doc))
    open(os.path.join(out_dir, "board_detail.md"), "w", encoding="utf-8").write("\n".join(o))
    open(os.path.join(out_dir, "board_stocks.md"), "w", encoding="utf-8").write("\n".join(t))


if __name__ == "__main__":
    main()
