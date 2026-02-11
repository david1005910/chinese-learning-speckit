"""
성조 다이어그램 시각화 모듈
matplotlib 기반 성조 피치 곡선 렌더링
"""

import io
from typing import List, Dict

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# 성조별 색상 (constitution.md 표준)
TONE_COLORS = {
    1: "#EF4444",  # 빨강
    2: "#22C55E",  # 초록
    3: "#3B82F6",  # 파랑
    4: "#A855F7",  # 보라
    5: "#9CA3AF",  # 회색 (경성)
}

TONE_NAMES_KR = {
    1: "1성 (음평)",
    2: "2성 (양평)",
    3: "3성 (상성)",
    4: "4성 (거성)",
    5: "경성 (轻声)",
}

# 성조 피치 곡선 데이터 (5단계 피치: 1=낮음, 5=높음)
# x: 0~1 (시간 진행), y: 피치 값
_TONE_CURVES = {
    1: ([0, 0.5, 1.0], [5, 5, 5]),           # 高平 55
    2: ([0, 0.5, 1.0], [3, 4, 5]),           # 上升 35
    3: ([0, 0.25, 0.5, 0.75, 1.0], [2, 1, 1, 2, 4]),  # 低凹 214
    4: ([0, 0.5, 1.0], [5, 3, 1]),           # 下降 51
    5: ([0, 0.5, 1.0], [3, 2.5, 2]),         # 경성 (가벼운 하강)
}


def render_all_tones_chart() -> bytes:
    """
    4성(+경성) 전체 개요 차트를 PNG 바이트로 반환.
    """
    if not HAS_MPL:
        return b""

    fig, ax = plt.subplots(figsize=(7, 4), facecolor="none")
    ax.set_facecolor("none")

    for tone in [1, 2, 3, 4, 5]:
        xs, ys = _TONE_CURVES[tone]
        # 곡선을 부드럽게 보간
        x_smooth = np.linspace(xs[0], xs[-1], 50)
        y_smooth = np.interp(x_smooth, xs, ys)
        label = TONE_NAMES_KR[tone]
        color = TONE_COLORS[tone]
        lw = 3.5 if tone != 5 else 2.0
        ls = "-" if tone != 5 else "--"
        ax.plot(x_smooth, y_smooth, color=color, linewidth=lw,
                linestyle=ls, label=label)

    ax.set_ylim(0.5, 5.5)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylabel("Pitch", color="white", fontsize=11)
    ax.set_xlabel("Time", color="white", fontsize=11)
    ax.set_title("Chinese Tones Overview", color="white", fontsize=14, fontweight="bold")
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1 (Low)", "2", "3 (Mid)", "4", "5 (High)"],
                       color="white", fontsize=9)
    ax.set_xticks([])
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color((1, 1, 1, 0.3))
    ax.legend(loc="upper left", fontsize=9, framealpha=0.3,
              labelcolor="white", facecolor="none", edgecolor=(1, 1, 1, 0.3))

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, transparent=True, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def render_word_tone_diagram(syllables: List[Dict]) -> bytes:
    """
    단어별 성조 곡선 PNG.

    Args:
        syllables: [{"syllable": "nǐ", "tone_number": 3, "tone3": "ni3"}, ...]

    Returns:
        PNG 바이트
    """
    if not HAS_MPL or not syllables:
        return b""

    n = len(syllables)
    fig, ax = plt.subplots(figsize=(max(3, n * 2.2), 3), facecolor="none")
    ax.set_facecolor("none")

    for i, syl in enumerate(syllables):
        tone = syl["tone_number"]
        xs, ys = _TONE_CURVES.get(tone, _TONE_CURVES[5])
        x_smooth = np.linspace(xs[0], xs[-1], 40)
        y_smooth = np.interp(x_smooth, xs, ys)
        # 각 음절을 x 축에서 간격을 두고 배치
        offset = i * 1.5
        ax.plot(x_smooth + offset, y_smooth, color=TONE_COLORS.get(tone, "#9CA3AF"),
                linewidth=4, solid_capstyle="round")
        # 음절 라벨
        ax.text(offset + 0.5, -0.3, syl["syllable"],
                ha="center", va="top", fontsize=14, color="white", fontweight="bold")

    ax.set_ylim(-1, 6)
    ax.set_xlim(-0.3, n * 1.5 - 0.2)
    ax.set_yticks([1, 3, 5])
    ax.set_yticklabels(["Low", "Mid", "High"], color="white", fontsize=9)
    ax.set_xticks([])
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color((1, 1, 1, 0.3))

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, transparent=True, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def tone_indicator_html(tone_number: int) -> str:
    """
    성조 번호에 대한 인라인 컬러 배지 HTML.

    Args:
        tone_number: 1-5

    Returns:
        HTML 문자열 (인라인 배지)
    """
    color = TONE_COLORS.get(tone_number, "#9CA3AF")
    label = str(tone_number) if tone_number <= 4 else "轻"
    return (
        f'<span style="display:inline-block; background:{color}; color:#fff; '
        f'font-size:0.7rem; font-weight:700; width:22px; height:22px; '
        f'line-height:22px; text-align:center; border-radius:50%; '
        f'margin:0 2px; vertical-align:middle; '
        f'box-shadow:0 2px 6px rgba(0,0,0,0.25);">{label}</span>'
    )
