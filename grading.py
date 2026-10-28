"""成績計算ロジック（Streamlit に依存しない純粋な関数群）.

総合成績の定義
    各期の成績 = (その期の試験の平均点) × 筆記割合 + その期の課題点
    総合成績   = 各期の成績の平均
判定
    60 点以上        : 合格
    40 点以上 60 未満 : 再試験（再試験で 60 点未満なら不合格）
    40 点未満        : 不合格（再試験なし）
"""

from __future__ import annotations

import math
from dataclasses import dataclass

PASS_LINE = 60.0
RETEST_LINE = 40.0

# key -> (表示名, [(期の名前, [試験名, ...]), ...])
PATTERNS: dict[str, tuple[str, list[tuple[str, list[str]]]]] = {
    "full4": (
        "通年4回（中間・期末 × 前期・後期）",
        [("前期", ["前期中間", "前期期末"]), ("後期", ["後期中間", "後期期末"])],
    ),
    "final2": (
        "通年 期末2回（前期末・後期末）",
        [("前期", ["前期末"]), ("後期", ["後期末"])],
    ),
    "half2": (
        "半期2回（中間・期末）",
        [("半期", ["中間", "期末"])],
    ),
}


def exam_names(pattern: str) -> list[str]:
    return [e for _, exams in PATTERNS[pattern][1] for e in exams]


def term_names(pattern: str) -> list[str]:
    return [t for t, _ in PATTERNS[pattern][1]]


def compute(pattern: str, exams: dict[str, float], assignments: dict[str, float],
            ratio: float) -> tuple[float, dict[str, float]]:
    """総合成績と各期の成績を返す. ratio は筆記割合 (0〜1)."""
    term_scores = {}
    for term, names in PATTERNS[pattern][1]:
        avg = sum(exams[n] for n in names) / len(names)
        term_scores[term] = avg * ratio + assignments[term]
    total = sum(term_scores.values()) / len(term_scores)
    return total, term_scores


def judge(score: float) -> tuple[str, str]:
    """(判定ラベル, 状態) を返す. 状態は success / warning / error."""
    if score >= PASS_LINE:
        return "合格", "success"
    if score >= RETEST_LINE:
        return "再試験（再試験で60点以上が必要）", "warning"
    return "不合格（再試験なし）", "error"


@dataclass
class Outlook:
    """未実施の試験がある場合の見通し."""
    pending: list[str]          # 未実施の試験
    floor: float                # 残り全部 0 点のときの総合成績
    ceiling: float              # 残り全部 100 点のときの総合成績
    need_pass: float | None     # 合格に必要な「残り試験の平均点」(None: 達成済み, inf: 不可能)
    need_retest: float | None   # 再試験資格に必要な「残り試験の平均点」

    def at(self, t: float) -> float:
        """残り試験の平均が t 点のときの総合成績（t の一次関数）."""
        return self.floor + (self.ceiling - self.floor) * t / 100.0


def _required(floor: float, ceiling: float, line: float) -> float | None:
    if floor >= line:
        return None
    if ceiling < line:
        return math.inf
    return 100.0 * (line - floor) / (ceiling - floor)


def outlook(pattern: str, exams: dict[str, float], pending: list[str],
            assignments: dict[str, float], ratio: float) -> Outlook:
    def with_rest(t: float) -> float:
        filled = {n: (t if n in pending else v) for n, v in exams.items()}
        return compute(pattern, filled, assignments, ratio)[0]

    lo, hi = with_rest(0.0), with_rest(100.0)
    return Outlook(pending, lo, hi, _required(lo, hi, PASS_LINE), _required(lo, hi, RETEST_LINE))


def need_text(need: float | None) -> str:
    """必要平均点を学生向けの短い文に. 試験は整数点なので切り上げる."""
    if need is None:
        return "達成済み"
    if math.isinf(need):
        return "残りが満点でも届かない"
    return f"平均 {math.ceil(need - 1e-9)} 点以上"
