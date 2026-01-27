import streamlit as st

st.title("成績評価シミュレーション 数学")

# 入力セクション
st.header("得点入力")

col1, col2 = st.columns(2)
with col1:
    x1 = st.number_input("前期中間試験 得点", 0.0, 100.0, 45.0)
    x2 = st.number_input("前期期末試験 得点", 0.0, 100.0, 45.0)
    y1 = st.number_input("前期課題点 ", 0, 30, 0)

with col2:
    x3 = st.number_input("後期中間試験 得点", 0.0, 100.0, 45.0)
    x4 = st.number_input("後期期末試験 得点", 0.0, 100.0, 45.0)
    y2 = st.number_input("後期課題点 ", 0, 30, 0)

# 計算ロジック
m1 = (x1 + x2) / 2
m2 = (x3 + x4) / 2
m3 = (x1 + x2 + x3 + x4) / 4
n = (y1 + y2) / 2

zenki = m1 * 0.7 + y1
kouki = m2 * 0.7 + y2
tsunen = (zenki + kouki) / 2  # 通年成績の計算

# 出力セクション
st.divider()
st.header("計算結果")

st.write(f"**前期試験の平均点:** {m1:.2f}")
st.write(f"**後期試験の平均点:** {m2:.2f}")
st.write(f"**すべての試験の平均点:** {m3:.2f}")
st.write(f"**課題点の平均:** {n:.2f}")

st.subheader("総合成績")
st.info(f"前期の総合成績： {zenki:.2f}")
st.info(f"後期の総合成績： {kouki:.2f}")
st.success(f"通年の成績： {tsunen:.2f}")
