import math

import streamlit as st

from charts import CONFIG, gauge, outlook_chart
from grading import (PASS_LINE, PATTERNS, RETEST_LINE, compute, exam_names,
                     judge, need_text, outlook, term_names)
from report import build_html

st.set_page_config(page_title="成績シミュレーター", layout="centered")

# ---------------------------------------------------------------------------
# 科目設定（URL のクエリパラメータから初期値を読み、変更したら URL に書き戻す）
#   例: https://score2026.streamlit.app/?pattern=half2&ratio=80
# ---------------------------------------------------------------------------
qp = st.query_params
if "pattern" not in st.session_state:
    p = qp.get("pattern", "full4")
    st.session_state.pattern = p if p in PATTERNS else "full4"
if "ratio" not in st.session_state:
    try:
        st.session_state.ratio = min(100, max(0, int(qp.get("ratio", 70))))
    except ValueError:
        st.session_state.ratio = 70

with st.sidebar:
    st.header("科目の設定")
    pattern = st.radio("試験のパターン", list(PATTERNS),
                       format_func=lambda k: PATTERNS[k][0], key="pattern")
    paper_ratio = st.slider("筆記試験の割合 (%)", 0, 100, key="ratio")
    assignment_limit = 100 - paper_ratio
    st.info(f"筆記試験: {paper_ratio}%　／　課題等: {assignment_limit} 点満点（各期）")
    st.caption("この画面の URL をそのまま共有すると、同じ科目設定で開けます。")

    with st.expander("判定基準"):
        st.markdown(
            f"- **{PASS_LINE:.0f} 点以上**：合格\n"
            f"- **{RETEST_LINE:.0f} 点以上 {PASS_LINE:.0f} 点未満**：再試験"
            f"（再試験で {PASS_LINE:.0f} 点未満なら不合格）\n"
            f"- **{RETEST_LINE:.0f} 点未満**：不合格（再試験なし）"
        )

st.query_params.update({"pattern": pattern, "ratio": str(paper_ratio)})
ratio = paper_ratio / 100

st.title("🧭 成績シミュレーター")
st.caption("試験の点数と課題点を入力してください。まだ受けていない試験は「未実施」に"
           "チェックを入れると、単位取得に必要な点数を逆算します。")

# ---------------------------------------------------------------------------
# 入力
# ---------------------------------------------------------------------------
terms = PATTERNS[pattern][1]
exams: dict[str, float] = {}
pending: list[str] = []
assignments: dict[str, float] = {}
over_limit = []

cols = st.columns(len(terms))
for col, (term, names) in zip(cols, terms):
    with col:
        st.subheader(f"📅 {term}")
        for name in names:
            done = not st.checkbox(f"{name}は未実施", key=f"pend_{name}")
            exams[name] = st.number_input(f"{name}試験", 0.0, 100.0, 60.0, step=1.0,
                                          key=f"exam_{name}", disabled=not done)
            if not done:
                pending.append(name)
        # ラベルと上限を固定して key を付けることで、割合を変えても入力が消えないようにする
        y = st.number_input(f"{term}課題点（見込みでも可）", 0.0, 100.0, 0.0, step=1.0,
                            key=f"assign_{term}")
        if y > assignment_limit:
            over_limit.append(term)
            y = float(assignment_limit)
        assignments[term] = y

if over_limit:
    st.warning(f"{'・'.join(over_limit)}の課題点が上限 {assignment_limit} 点を超えているため、"
               f"{assignment_limit} 点として計算しています。")

# ---------------------------------------------------------------------------
# 結果（画面に表示しながら、HTML レポートの中身も集める）
# ---------------------------------------------------------------------------
results: list[tuple[str, str]] = []
verdicts: list[tuple[str, str]] = []
figures = []


def say(kind: str, msg: str):
    """画面にメッセージを出し、レポートにも残す."""
    {"success": st.success, "warning": st.warning, "error": st.error, "info": st.info}[kind](msg)
    verdicts.append((kind, msg))


def show_chart(fig):
    st.plotly_chart(fig, theme=None, config=CONFIG)


st.divider()

if not pending:
    total, term_scores = compute(pattern, exams, assignments, ratio)
    label, kind = judge(total)

    st.header("📊 計算結果")
    mcols = st.columns(len(term_scores) + 1)
    for c, (term, s) in zip(mcols, term_scores.items()):
        c.metric(f"{term}の成績", f"{s:.2f} 点")
    mcols[-1].metric("総合成績", f"{total:.2f} 点")
    say(kind, f"総合成績：**{total:.2f} 点** → {label}")
    if kind == "warning":
        say("info", f"あと {PASS_LINE - total:.2f} 点で合格ラインでした。再試験に向けて準備しましょう。")

    fig = gauge(total)
    show_chart(fig)
    figures.append(("総合成績の位置", fig))

    results += [(f"{t}の成績", f"{s:.2f} 点") for t, s in term_scores.items()]
    results += [("総合成績", f"{total:.2f} 点"), ("判定", label)]

else:
    o = outlook(pattern, exams, pending, assignments, ratio)

    st.header("🧭 単位取得までの目標")
    st.write(f"未実施の試験：**{'・'.join(pending)}**（{len(pending)} 回）")

    c1, c2 = st.columns(2)
    c1.metric("合格（60点）に必要な点", need_text(o.need_pass))
    c2.metric("再試験の資格（40点）に必要な点", need_text(o.need_retest))
    st.caption("「平均◯点以上」は、残りの試験の平均点です。残りが1回ならその試験の点数です。")

    if o.need_pass is None:
        say("success", "残りの試験が0点でも総合成績は60点以上です。気を抜かずに受けましょう。")
    elif math.isinf(o.need_pass):
        if o.need_retest is not None and math.isinf(o.need_retest):
            say("error", "残りの試験が満点でも総合成績は40点に届きません。"
                         "早めに担当の先生・担任の先生に相談してください。")
        elif o.need_retest is None:
            say("warning", "残りの試験が満点でも60点には届きませんが、再試験の資格（40点以上）は"
                           "すでに確保しています。残りの試験も全力で取り組み、再試験に備えましょう。")
        else:
            say("warning", "残りの試験が満点でも60点には届きません。"
                           f"再試験の資格（40点以上）を確実に取りにいきましょう（**{need_text(o.need_retest)}**）。")
    else:
        say("info", f"残りの試験で **{need_text(o.need_pass)}** を取れば合格です。")

    st.subheader("見込みで試算する")
    t_now = st.slider("残りの試験で取れそうな平均点", 0, 100, 60, key="expect")
    predicted = o.at(t_now)
    label, kind = judge(predicted)
    say(kind, f"残りの平均が {t_now} 点のときの総合成績：**{predicted:.2f} 点** → {label}")

    fig1 = gauge(predicted, o.floor, o.ceiling)
    show_chart(fig1)
    st.caption(f"灰色の帯は取りうる総合成績の範囲（残り0点：{o.floor:.1f} 点 〜 残り満点：{o.ceiling:.1f} 点）")
    fig2 = outlook_chart(o, t_now)
    with st.expander("残りの試験の点数と総合成績の関係（グラフ）"):
        show_chart(fig2)
        st.caption("線の上にカーソルを合わせる（スマホではタップする）と、その点数での総合成績が表示されます。")
    figures += [("総合成績の位置（見込み）", fig1), ("残りの試験の点数と総合成績の関係", fig2)]

    results += [
        ("未実施の試験", "・".join(pending)),
        ("合格（60点）に必要な点", need_text(o.need_pass)),
        ("再試験の資格（40点）に必要な点", need_text(o.need_retest)),
        ("取りうる総合成績の範囲", f"{o.floor:.2f} 〜 {o.ceiling:.2f} 点"),
        (f"見込み（残り平均 {t_now} 点）の総合成績", f"{predicted:.2f} 点（{label}）"),
    ]

# ---------------------------------------------------------------------------
# HTML ダウンロード
# ---------------------------------------------------------------------------
html = build_html(
    settings=[("試験のパターン", PATTERNS[pattern][0]),
              ("筆記試験の割合", f"{paper_ratio} %"),
              ("課題点の満点（各期）", f"{assignment_limit} 点")],
    inputs=[(f"{n}試験", "未実施" if n in pending else f"{exams[n]:.0f} 点")
            for n in exam_names(pattern)]
           + [(f"{t}課題点", f"{assignments[t]:.1f} 点") for t in term_names(pattern)],
    results=results,
    verdicts=verdicts,
    figures=figures,
)

st.divider()
st.download_button("📄 結果をHTMLでダウンロード", data=html.encode("utf-8"),
                   file_name="grade_simulation.html", mime="text/html")
st.caption("ダウンロードしたファイルはブラウザで開けます。ファイル内の「印刷 / PDFで保存」から"
           "PDF にもできます。入力した点数はこの画面の中だけで計算に使われ、保存されません。")
