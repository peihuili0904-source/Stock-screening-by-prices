"""상태 JSON을 현황판 마크다운으로 바꾼다.

사용: python3 -I render_board.py state.json > board.md
"""

import json
import sys


def cell(v):
    if v is None:
        return ""
    if isinstance(v, list):
        v = ", ".join(str(x) for x in v)
    return str(v).replace("|", "/").replace("\n", " ").replace("~", "–")


def link(text, url):
    return f"[{cell(text)}]({url})" if url else cell(text)


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(cell(c) if not str(c).startswith("[") else str(c) for c in r) + " |" for r in rows]
    return out


def bullets(label, items):
    if not items:
        return []
    if isinstance(items, str):
        return [f"- {label}: {cell(items)}"]
    return [f"- {label}:"] + [f"  - {cell(x)}" for x in items]


def source(cur):
    line = f"> 기준: {link(cur.get('as_of', ''), cur.get('note_url'))} · {cell(cur.get('analyst'))}"
    if cur.get("title"):
        line += f" · 「{cell(cur['title'])}」"
    if cur.get("filled_from"):
        line += f"  \n> 일부 항목 보충: {cell(cur['filled_from'])}"
    return line


def section(title, items, fields, hist_cols):
    out = [f"## {title}", ""]
    if not items:
        return out + ["(아직 없음)", ""]
    for key, it in items.items():
        cur = it.get("current", {})
        out += [f"### {cell(it.get('name', key))} ({key})", "", source(cur), ""]
        for label, f in fields:
            out += bullets(label, cur.get(f))
        if cur.get("estimates"):
            out += ["", "실적 추정", ""]
            out += table(["연도", "매출", "영업이익", "순이익", "EPS", "컨센서스 대비"],
                         [[e.get(k, "") for k in ("year", "revenue", "op", "ni", "eps", "vs_cons")] for e in cur["estimates"]])
        if it.get("history"):
            out += ["", "이력", ""]
            out += table([h for h, _ in hist_cols] + ["리포트"],
                         [[h.get(k, "") for _, k in hist_cols] + [link("노트", h.get("note_url"))] for h in it["history"]])
        if it.get("changelog"):
            out += ["", "논리 변화", ""]
            out += [f"- {c.get('date', '')}: {cell(c.get('text'))}" for c in reversed(it["changelog"])]
        out.append("")
    return out


def main():
    s = json.load(open(sys.argv[1], encoding="utf-8"))
    mk, sc, st = s.get("markets", {}), s.get("sectors", {}), s.get("stocks", {})
    o = [f"# 신한리서치 현황판 {s.get('updated', '')}", "",
         f"처리한 리포트 {len(s.get('processed', []))}건 · 시장 {len(mk)} · 섹터 {len(sc)} · 종목 {len(st)}", ""]

    o += ["## 한눈에 보기", "", "시장", ""]
    o += table(["시장", "시각", "밴드·목표", "기준일"],
               [[m.get("name", k), m.get("current", {}).get("view"), m.get("current", {}).get("target"),
                 m.get("current", {}).get("as_of")] for k, m in mk.items()])
    o += ["", "섹터", ""]
    o += table(["섹터", "의견", "Top pick", "기준일"],
               [[x.get("name", k), x.get("current", {}).get("view"), x.get("current", {}).get("top_picks"),
                 x.get("current", {}).get("as_of")] for k, x in sc.items()])
    o += ["", "종목", ""]
    o += table(["종목", "섹터", "의견", "목표주가", "변경", "기준일"],
               [[f"{x.get('name', k)} ({k})", sc.get(x.get("sector"), {}).get("name", x.get("sector")),
                 x.get("current", {}).get("rating"), x.get("current", {}).get("target_price"),
                 x.get("current", {}).get("change"), x.get("current", {}).get("as_of")] for k, x in st.items()])
    o.append("")

    changes = []
    for group, items in (("시장", mk), ("섹터", sc), ("종목", st)):
        for k, it in items.items():
            for c in it.get("changelog", []):
                changes.append((c.get("date", ""), f"{group} · {it.get('name', k)}", c.get("text", "")))
    changes.sort(key=lambda r: r[0], reverse=True)
    o += ["## 최근 변화 (최신순)", ""] + table(["날짜", "대상", "내용"], changes[:30]) + [""]

    o += ["## 하우스 내 이견", ""]
    o += table(["날짜", "쟁점", "의견 A", "의견 B"],
               [[d.get("date"), d.get("topic"), d.get("a"), d.get("b")] for d in s.get("dissent", [])]) + [""]

    o += section("시장", mk, [("시각", "view"), ("밴드·목표", "target"), ("핵심 논리", "thesis"),
                              ("선호", "prefer"), ("비선호", "avoid"), ("리스크", "risks")],
                 [("날짜", "date"), ("시각", "view"), ("밴드·목표", "target")])
    o += section("섹터", sc, [("의견", "view"), ("업황", "cycle"), ("핵심 논리", "thesis"), ("Top pick", "top_picks"),
                              ("비선호", "avoid"), ("카탈리스트", "catalysts"), ("리스크", "risks")],
                 [("날짜", "date"), ("의견", "view"), ("Top pick", "top_picks")])
    o += section("종목", st, [("투자의견", "rating"), ("목표주가", "target_price"), ("변경", "change"),
                              ("기준 주가", "base_price"), ("상승여력", "upside"), ("밸류에이션", "valuation"),
                              ("투자 포인트", "thesis"), ("카탈리스트", "catalysts"), ("리스크", "risks")],
                 [("날짜", "date"), ("의견", "rating"), ("목표주가", "target_price"), ("변경", "change")])

    o += ["## 처리한 리포트", ""]
    o += table(["날짜", "유형", "제목", "애널리스트", "노트"],
               [[p.get("date"), p.get("type"), p.get("title"), p.get("analyst"), link("노트", p.get("note_url"))]
                for p in sorted(s.get("processed", []), key=lambda p: p.get("date", ""), reverse=True)])
    print("\n".join(o))


if __name__ == "__main__":
    main()
