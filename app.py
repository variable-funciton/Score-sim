
import streamlit as st

st.set_page_config(page_title="成績評価シミュレーター", layout="wide")
st.title("成績評価シミュレーション（通年）")

# サイドバー：配分設定
st.sidebar.header("配点設定")
paper_ratio = st.sidebar.slider("筆記試験の割合 (%)", 0, 100, 70)
assignment_limit = 100 - paper_ratio
st.sidebar.info(f"現在の設定:\n- 筆記試験: {paper_ratio}%\n- 課題等: {assignment_limit}%")

# 入力セクション
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📅 前期")
    x1 = st.number_input("前期中間試験 (0点-100点)", 0.0, 100.0, 60.0)
    x2 = st.number_input("前期期末試験 (0点-100点)", 0.0, 100.0, 60.0)
    y1 = st.number_input(f"前期課題点 (0-{assignment_limit})", 0, assignment_limit, 0)

with col_right:
    st.subheader("📅 後期")
    x3 = st.number_input("後期中間試験 (0点-100点)", 0.0, 100.0, 60.0)
    x4 = st.number_input("後期期末試験 (0点-100点)", 0.0, 100.0, 60.0)
    y2 = st.number_input(f"後期課題点 (0-{assignment_limit})", 0, assignment_limit, 0)

# 計算ロジック
zenki_exam_avg = (x1 + x2) / 2
kouki_exam_avg = (x3 + x4) / 2

zenki_total = (zenki_exam_avg * paper_ratio / 100) + y1
kouki_total = (kouki_exam_avg * paper_ratio / 100) + y2
final_score = (zenki_total + kouki_total) / 2

# 結果表示
st.divider()
st.header("📊 計算結果")

res_col1, res_col2, res_col3 = st.columns(3)
res_col1.metric("前期成績", f"{zenki_total:.1f} 点")
res_col2.metric("後期成績", f"{kouki_total:.1f} 点")

# 通年成績の判定と表示
if final_score >= 60:
    res_col3.metric("通年成績", f"{final_score:.1f} 点", delta="合格", delta_color="normal")
    st.success(f"最終結果: 合格 ({final_score:.1f}点)")
else:
    res_col3.metric("通年成績", f"{final_score:.1f} 点", delta="- 不合格", delta_color="inverse")
    st.error(f"最終結果: 単位取得にはあと {60.0 - final_score:.1f} 点必要です。")
