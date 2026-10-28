"""plotly による図の作成（アプリ画面と HTML レポートの両方で共用）."""

from __future__ import annotations

import math

import plotly.graph_objects as go

from grading import PASS_LINE, RETEST_LINE, Outlook

RED, AMBER, GREEN = "#e57373", "#ffb74d", "#81c784"
NAVY, PINK = "#1a237e", "#d81b60"
FONT = "'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', Meiryo, sans-serif"

# 画面・HTML 共通の表示設定（ツールバーを隠し、スマホでの誤操作によるズームを防ぐ）
CONFIG = {"displayModeBar": False, "responsive": True}

ZONES = [(0, RETEST_LINE, RED, "再試験なし"),
         (RETEST_LINE, PASS_LINE, AMBER, "再試験"),
         (PASS_LINE, 100, GREEN, "合格")]


def _base_layout(fig: go.Figure, height: int) -> None:
    fig.update_layout(
        height=height,
        margin=dict(l=50, r=20, t=20, b=40),
        font=dict(family=FONT, size=13, color="#333"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        dragmode=False,
        hoverlabel=dict(font_family=FONT),
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)


def gauge(score: float, low: float | None = None, high: float | None = None) -> go.Figure:
    """総合成績の位置を示す横長のゲージ. low〜high は取りうる範囲."""
    fig = go.Figure()
    for x0, x1, color, label in ZONES:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=color, opacity=0.3, line_width=0, layer="below")
        fig.add_annotation(x=(x0 + x1) / 2, y=0.88, text=label, showarrow=False,
                           font=dict(size=12, color="#444"))
    if low is not None and high is not None:
        fig.add_trace(go.Scatter(
            x=[low, high], y=[0.4, 0.4], mode="lines+markers+text",
            line=dict(color="rgba(80,80,80,0.35)", width=10),
            marker=dict(size=1, color="rgba(0,0,0,0)"),
            text=[f"{low:.1f}", f"{high:.1f}"], textposition="bottom center",
            textfont=dict(size=11, color="#555"),
            hovertemplate="取りうる範囲の端：%{x:.1f} 点<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=[score], y=[0.4], mode="markers+text",
        marker=dict(symbol="triangle-down", size=20, color=NAVY),
        text=[f"<b>{score:.1f}</b>"], textposition="top center",
        textfont=dict(size=15, color=NAVY),
        hovertemplate="総合成績：%{x:.2f} 点<extra></extra>"))
    _base_layout(fig, height=170)
    fig.update_xaxes(range=[0, 100], tickvals=[0, RETEST_LINE, PASS_LINE, 100],
                     showgrid=False, showline=True, linecolor="#333", ticks="outside")
    fig.update_yaxes(range=[0, 1], visible=False)
    fig.update_layout(margin=dict(l=15, r=15, t=10, b=30))
    return fig


def outlook_chart(o: Outlook, t_now: float) -> go.Figure:
    """残り試験の平均点 t と総合成績の関係（一次関数）."""
    fig = go.Figure()
    for y0, y1, color, label in ZONES:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=color, opacity=0.25, line_width=0, layer="below")
        fig.add_annotation(x=99, y=(y0 + y1) / 2, text=label, showarrow=False, xanchor="right",
                           font=dict(size=11, color="#666"))

    ts = list(range(101))
    fig.add_trace(go.Scatter(
        x=ts, y=[o.at(t) for t in ts], mode="lines", line=dict(color=NAVY, width=3),
        hovertemplate="残り平均 %{x} 点 → 総合 %{y:.1f} 点<extra></extra>"))

    for need, line, color, what in [(o.need_retest, RETEST_LINE, "#ef6c00", "再試験の資格"),
                                    (o.need_pass, PASS_LINE, "#2e7d32", "合格")]:
        if need is not None and not math.isinf(need):
            fig.add_trace(go.Scatter(x=[need, need], y=[0, line], mode="lines",
                                     line=dict(color=color, width=1.5, dash="dash"),
                                     hoverinfo="skip"))
            fig.add_trace(go.Scatter(
                x=[need], y=[line], mode="markers+text", marker=dict(size=10, color=color),
                text=[f"{need:.1f} 点"], textposition="bottom right",
                textfont=dict(color=color, size=12),
                hovertemplate=f"{what}ライン：残り平均 %{{x:.1f}} 点<extra></extra>"))

    fig.add_trace(go.Scatter(
        x=[t_now], y=[o.at(t_now)], mode="markers",
        marker=dict(symbol="star", size=20, color=PINK, line=dict(color="white", width=1)),
        hovertemplate="見込み %{x} 点 → 総合 %{y:.1f} 点<extra></extra>"))

    _base_layout(fig, height=400)
    axis = dict(range=[0, 100], dtick=20, gridcolor="#ddd", griddash="dot",
                showline=True, linecolor="#333", mirror=True, zeroline=False)
    fig.update_xaxes(title=dict(text="残りの試験の平均点"), **axis)
    fig.update_yaxes(title=dict(text="総合成績"), **axis)
    return fig
