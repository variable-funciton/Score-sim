
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib_fontja
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
# --- 日本語フォント設定用の追加 ---
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from io import BytesIO
# 日本語フォント（平成角ゴシック）を登録
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))

st.set_page_config(page_title="成績シミュレーター", layout="centered")

st.title("成績評価シミュレーション")

# --- 入力セクション ---
with st.sidebar:
    st.header("配点設定")
    paper_ratio = st.slider("筆記試験の割合 (%)", 0, 100, 70)
    assignment_limit = 100 - paper_ratio
    st.sidebar.info(f"現在の設定:\n- 筆記試験: {paper_ratio}%\n- 課題等: {assignment_limit}%")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📅 前期")
    x1 = st.number_input("前期中間", 0.0, 100.0, 60.0)
    x2 = st.number_input("前期期末", 0.0, 100.0, 60.0)
    y1 = st.number_input(f"前期課題(最大{assignment_limit})", 0.0, float(assignment_limit), 0.0)

with col2:
    st.subheader("📅 後期")
    x3 = st.number_input("後期中間", 0.0, 100.0, 60.0)
    x4 = st.number_input("後期期末", 0.0, 100.0, 60.0)
    y2 = st.number_input(f"後期課題(最大{assignment_limit})", 0.0, float(assignment_limit), 0.0)

# --- 計算 ---
zenki_score = ((x1 + x2) / 2 * paper_ratio / 100) + y1
kouki_score = ((x3 + x4) / 2 * paper_ratio / 100) + y2
final_score = (zenki_score + kouki_score) / 2

# --- 可視化（Matplotlibを使用して画像化） ---
st.divider()
st.subheader("📊 筆記試験得点の推移")

labels = ["前期中間試験", "前期期末試験", "後期中間試験", "後期期末試験"]
scores = [x1, x2, x3, x4]

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(labels, scores, marker='o', linestyle='-', color='#007bff')
ax.set_ylim(0, 105)
ax.set_ylabel("得点")
ax.grid(True, linestyle='--', alpha=0.6)
st.pyplot(fig)

# 結果表示
st.divider()
st.header("📊 計算結果")

res_col1, res_col2, res_col3 = st.columns(3)
res_col1.metric("前期総合成績", f"{zenki_score:.2f} 点")
res_col2.metric("後期総合成績", f"{kouki_score:.2f} 点")

# 通年成績の判定と表示
if final_score >= 60:
    res_col3.metric("通年成績", f"{final_score:.2f} 点", delta="合格", delta_color="normal")
    st.success(f"最終結果: 合格 ({final_score:.2f} 点)")
else:
    res_col3.metric("通年成績", f"{final_score:.2f} 点", delta="- 不合格", delta_color="inverse")
    st.error(f"最終結果: 単位取得にはあと {60.0 - final_score:.2f} 点必要です。")

# --- PDF生成（画像埋め込み） ---
def create_pdf(fig_data):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # テキスト情報
    p.setFont("HeiseiKakuGo-W5", 20)
    p.drawString(50, h - 50, "成績レポート")
    
    p.setFont("HeiseiKakuGo-W5", 14)
    p.drawString(50, h - 100, f"前期総合成績: {zenki_score:.2f} 点, 前期課題: {y1:.2f}点")
    p.drawString(50, h - 120, f"後期総合成績: {kouki_score:.2f} 点, 後期課題: {y2:.2f}点")
    p.setFont("HeiseiKakuGo-W5", 16)
    p.drawString(50, h - 150, f"総合成績: {final_score:.2f} 点")
    
    status = "合格" if final_score >= 60 else "不合格"
    p.drawString(50, h - 180, f"単位認定の可否: {status}")

    # グラフ画像をPDFに貼り付け
    img_buffer = BytesIO()
    fig_data.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    p.drawImage(ImageReader(img_buffer), 50, h - 600, width = 500, preserveAspectRatio=True)

    p.showPage()
    p.save()
    return buffer.getvalue()

st.divider()
if st.download_button(
    label="📈 グラフ付きPDFをダウンロード",
    data=create_pdf(fig),
    file_name="grade_report_with_chart.pdf",
    mime="application/pdf",
):
    st.balloons()

