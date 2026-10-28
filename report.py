"""ダウンロード用の HTML レポート（1ファイル完結。図は plotly.js を CDN から読み込む）."""

from __future__ import annotations

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

import plotly.graph_objects as go

from charts import CONFIG

CSS = """
:root { --navy:#1a237e; --ok:#2e7d32; --warn:#ef6c00; --ng:#c62828; }
* { box-sizing: border-box; }
body { font-family: 'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP',Meiryo,sans-serif;
       color:#222; background:#f5f6fa; margin:0; line-height:1.6; }
main { max-width: 760px; margin: 24px auto; padding: 24px 28px; background:#fff;
       border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
h1 { font-size: 1.5rem; margin: 0 0 4px; color: var(--navy); }
h2 { font-size: 1.1rem; margin: 28px 0 10px; padding-bottom: 4px; border-bottom: 2px solid #e3e5ef; }
.meta { color:#666; font-size:.85rem; margin:0; }
table { border-collapse: collapse; width: 100%; font-size: .95rem; }
th, td { border: 1px solid #dde; padding: 6px 10px; text-align: left; }
th { background:#f0f2fa; width: 45%; font-weight: normal; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.verdict { margin: 14px 0; padding: 12px 16px; border-radius: 8px; border-left: 6px solid; }
.verdict.success { background:#e8f5e9; border-color: var(--ok); }
.verdict.warning { background:#fff3e0; border-color: var(--warn); }
.verdict.error   { background:#ffebee; border-color: var(--ng); }
.verdict.info    { background:#e8eaf6; border-color: var(--navy); }
.chart { margin: 8px 0 4px; break-inside: avoid; page-break-inside: avoid; }
.note { color:#666; font-size:.85rem; }
.toolbar { text-align: right; margin-bottom: 8px; }
.toolbar button { font: inherit; padding: 6px 14px; border-radius: 6px; border: 1px solid #99a;
                  background: #fff; cursor: pointer; }
@media (max-width: 600px) { main { margin: 0; border-radius: 0; padding: 16px; } }
@page { size: A4; margin: 15mm; }
@media print {
  body { background: #fff; }
  main { box-shadow: none; margin: 0; max-width: none; padding: 0; }
  .toolbar { display: none; }
  h2 { break-after: avoid; }
}
"""


def _table(rows: list[tuple[str, str]]) -> str:
    body = "".join(f"<tr><th>{escape(k)}</th><td class='num'>{escape(v)}</td></tr>" for k, v in rows)
    return f"<table>{body}</table>"


def build_html(*, settings: list[tuple[str, str]], inputs: list[tuple[str, str]],
               results: list[tuple[str, str]], verdicts: list[tuple[str, str]],
               figures: list[tuple[str, go.Figure]]) -> str:
    """verdicts は (状態, 文) のリスト. 状態は success / warning / error / info.
    文中の **強調** は太字にする."""
    now = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y年%m月%d日 %H:%M")

    def emph(s: str) -> str:
        parts = escape(s).split("**")
        return "".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(parts))

    verdict_html = "".join(f"<div class='verdict {k}'>{emph(s)}</div>" for k, s in verdicts)

    charts_html = ""
    for i, (title, fig) in enumerate(figures):
        div = fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False,
                          config=CONFIG)
        charts_html += f"<h2>{escape(title)}</h2><div class='chart'>{div}</div>"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>成績シミュレーション結果</title>
<style>{CSS}</style>
</head>
<body>
<main>
  <div class="toolbar"><button onclick="window.print()">🖨 印刷 / PDFで保存</button></div>
  <h1>🧭 成績シミュレーション結果</h1>
  <p class="meta">作成日時：{now}</p>

  <h2>科目の設定</h2>
  {_table(settings)}

  <h2>入力した点数</h2>
  {_table(inputs)}

  <h2>結果</h2>
  {_table(results)}
  {verdict_html}

  {charts_html}

  <p class="note">判定基準：60点以上で合格／40点以上60点未満は再試験（再試験で60点未満なら不合格）／40点未満は不合格（再試験なし）。<br>
  ※この結果は入力値にもとづく試算です（小数点以下はそのまま計算しています）。正式な成績は担当教員の評価によります。<br>
  ※図の表示にはインターネット接続が必要です。</p>
</main>
</body>
</html>
"""
