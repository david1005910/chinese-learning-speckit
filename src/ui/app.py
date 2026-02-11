"""
Streamlit 웹 인터페이스 - AI 기반 중국어 학습 프로그램
spec-kit 사양에 따른 풀스택 구현
"""

import streamlit as st
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# .env 자동 로드
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
except ImportError:
    pass

from src.core.data_parser import ChineseDataParser
from src.core.lesson_manager import LessonManager
from src.core.progress_tracker import ProgressTracker
from src.ai.ai_tutor import ChineseAITutor
from src.ai.agents import OrchestratorAgent, EvalAgent
from src.speech.speech_handler import SpeechHandler
from src.learning.gamification import GamificationSystem, calculate_level, xp_progress_in_level
from src.learning.spaced_repetition import SpacedRepetitionSystem

st.set_page_config(
    page_title="중국어 학습",
    page_icon="🇨🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS 스타일 (Gooey / Liquid Morphism) ──────────────────────────────────────
st.markdown("""
<style>
/* ── 최상단 흰색 공백 제거 ── */
html, body {
    background: linear-gradient(135deg, #f97316 0%, #ec4899 35%, #8b5cf6 65%, #3b82f6 100%) !important;
    margin: 0 !important; padding: 0 !important;
}
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"],
.stAppHeader, .stAppViewBlockContainer ~ div {
    background: transparent !important;
    border-bottom: none !important;
}
#MainMenu { visibility: hidden; }
header { background: transparent !important; }

/* ── 전체 배경: 활기찬 액체 그라디언트 + 블롭 ── */
.stApp {
    background: linear-gradient(135deg, #f97316 0%, #ec4899 35%, #8b5cf6 65%, #3b82f6 100%) !important;
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}
/* 장식용 블롭 ── */
.stApp::before {
    content: '';
    position: fixed;
    top: -80px; left: -80px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(249,115,22,0.55) 0%, transparent 70%);
    border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
    filter: blur(40px);
    pointer-events: none;
    z-index: 0;
    animation: blobFloat 8s ease-in-out infinite alternate;
}
.stApp::after {
    content: '';
    position: fixed;
    bottom: -80px; right: -60px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(59,130,246,0.55) 0%, transparent 70%);
    border-radius: 40% 60% 70% 30% / 40% 70% 30% 60%;
    filter: blur(45px);
    pointer-events: none;
    z-index: 0;
    animation: blobFloat 10s ease-in-out infinite alternate-reverse;
}
@keyframes blobFloat {
    0%   { transform: translate(0,0) scale(1); }
    100% { transform: translate(30px,20px) scale(1.08); }
}

/* ── 사이드바 액체 패널 ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0.10) 100%) !important;
    backdrop-filter: blur(18px) !important;
    -webkit-backdrop-filter: blur(18px) !important;
    border-right: 1px solid rgba(255,255,255,0.30) !important;
    box-shadow: 4px 0 32px rgba(236,72,153,0.20), inset 0px 1px 2px rgba(255,255,255,0.35);
    border-radius: 0 32px 32px 0 !important;
}
section[data-testid="stSidebar"] * { color: #fff !important; text-shadow: 0 1px 4px rgba(0,0,0,0.25); }

/* ── 메인 컨텐츠 액체 패널 ── */
[data-testid="stMainBlockContainer"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0.10) 100%);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 32px;
    border: 1px solid rgba(255,255,255,0.32);
    box-shadow: 0px 12px 32px rgba(0,0,0,0.18),
                inset 0px 1px 2px rgba(255,255,255,0.35);
    padding: 28px !important;
    margin: 12px !important;
    position: relative;
    overflow: visible;
}
/* 패널 상단 광택 하이라이트 */
[data-testid="stMainBlockContainer"]::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 100%);
    border-radius: 32px 32px 0 0;
    pointer-events: none;
}

/* ── 글자 색상 ── */
.stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span {
    color: #fff !important;
    text-shadow: 0px 2px 4px rgba(0,0,0,0.28);
}

/* ── 버튼 ── */
.stButton > button {
    background: linear-gradient(135deg, rgba(255,255,255,0.30) 0%, rgba(255,255,255,0.12) 100%) !important;
    border: 1px solid rgba(255,255,255,0.38) !important;
    border-radius: 18px !important;
    color: #fff !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.25) !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.16), inset 0px 1px 2px rgba(255,255,255,0.40) !important;
    transition: all 0.22s ease;
    font-weight: 600;
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(255,255,255,0.45) 0%, rgba(255,255,255,0.22) 100%) !important;
    box-shadow: 0 10px 28px rgba(236,72,153,0.35), inset 0px 1px 2px rgba(255,255,255,0.5) !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(236,72,153,0.75) 0%, rgba(139,92,246,0.75) 100%) !important;
    box-shadow: 0 8px 24px rgba(236,72,153,0.40), inset 0px 1px 2px rgba(255,255,255,0.35) !important;
}

/* ── 입력 필드 (글자색 강제 지정) ── */
input, input:focus, input:active,
textarea, textarea:focus, textarea:active {
    color: #fff !important;
    -webkit-text-fill-color: #fff !important;
    background: rgba(30, 10, 60, 0.82) !important;
}
input::placeholder, textarea::placeholder {
    color: rgba(255, 210, 235, 0.55) !important;
    -webkit-text-fill-color: rgba(255, 210, 235, 0.55) !important;
    opacity: 1 !important;
}
.stTextInput input, .stTextArea textarea,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
[data-baseweb="base-input"] input, [data-baseweb="base-input"] textarea {
    background: rgba(30, 10, 60, 0.82) !important;
    border: 1px solid rgba(255,255,255,0.30) !important;
    border-radius: 14px !important;
    color: #fff !important;
    -webkit-text-fill-color: #fff !important;
    caret-color: #f9a8d4 !important;
    backdrop-filter: blur(10px) !important;
}
[data-baseweb="base-input"], [data-baseweb="input"], [data-baseweb="textarea"] {
    background: rgba(30, 10, 60, 0.82) !important;
    border-radius: 14px !important;
}

/* ── Selectbox 드롭다운 ── */
[data-baseweb="select"] > div,
[data-baseweb="select"] [class*="ValueContainer"],
div[data-baseweb="select"] {
    background: rgba(30, 10, 60, 0.82) !important;
    border: 1px solid rgba(255,255,255,0.28) !important;
    border-radius: 14px !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div,
[data-baseweb="select"] [class*="singleValue"],
[data-baseweb="select"] [class*="placeholder"] {
    color: #fff !important;
    -webkit-text-fill-color: #fff !important;
}
[data-baseweb="menu"], [data-baseweb="popover"] {
    background: rgba(25, 8, 55, 0.97) !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
    border-radius: 14px !important;
}
[role="option"] { color: #fff !important; background: transparent !important; }
[role="option"]:hover, [aria-selected="true"] {
    background: rgba(255,255,255,0.15) !important;
}

/* ── chat input ── */
[data-testid="stChatInput"] > div,
[data-testid="stChatInputContainer"] {
    background: rgba(30, 10, 50, 0.65) !important;
    border: 1px solid rgba(255,255,255,0.28) !important;
    border-radius: 24px !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.18), inset 0px 1px 2px rgba(255,255,255,0.25) !important;
}
[data-testid="stChatInput"] textarea {
    color: #fff !important;
    caret-color: #f9a8d4 !important;
    background: transparent !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(255, 220, 240, 0.55) !important;
}

/* ── 메트릭 카드 ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0.10) 100%);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.30);
    border-radius: 24px;
    padding: 14px 18px;
    box-shadow: 0px 8px 24px rgba(0,0,0,0.15),
                inset 0px 1px 2px rgba(255,255,255,0.30);
}
[data-testid="stMetricValue"] { color: #fde68a !important; font-weight: 700; text-shadow: 0 2px 8px rgba(249,115,22,0.45); }
[data-testid="stMetricLabel"] { color: rgba(255,255,255,0.85) !important; }

/* ── 단어 카드 ── */
.word-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0.10) 100%);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255,255,255,0.32);
    border-radius: 28px;
    padding: 32px;
    color: #fff;
    text-align: center;
    margin-bottom: 16px;
    box-shadow: 0px 12px 32px rgba(0,0,0,0.18),
                inset 0px 1px 2px rgba(255,255,255,0.38);
    text-shadow: 0px 2px 4px rgba(0,0,0,0.28);
    position: relative;
    overflow: hidden;
}
.word-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0) 100%);
    border-radius: 28px 28px 0 0;
}
.word-card .chinese { font-size: 3rem; font-weight: bold; color: #fff; text-shadow: 0 2px 12px rgba(236,72,153,0.5); }
.word-card .pinyin  { font-size: 1.2rem; margin-top: 6px; color: #fde68a; text-shadow: 0 1px 4px rgba(0,0,0,0.3); }

/* ── XP 바 ── */
.xp-bar  { height: 12px; border-radius: 8px; background: rgba(255,255,255,0.18); overflow: hidden; }
.xp-fill { height: 12px; border-radius: 8px;
           background: linear-gradient(90deg, #f97316, #ec4899, #8b5cf6, #3b82f6);
           box-shadow: 0 0 12px rgba(236,72,153,0.6); }

/* ── 뱃지 ── */
.badge-unlocked {
    background: linear-gradient(135deg, rgba(255,215,0,0.35) 0%, rgba(249,115,22,0.25) 100%);
    border: 1px solid rgba(255,215,0,0.55);
    border-radius: 18px; padding: 8px 16px; margin: 4px;
    display: inline-block; color: #fde68a !important;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 14px rgba(249,115,22,0.30), inset 0 1px 1px rgba(255,255,255,0.30);
    text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
.badge-locked {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 18px; padding: 8px 16px; margin: 4px;
    display: inline-block; opacity: 0.40; backdrop-filter: blur(8px);
}

/* ── metric-card ── */
.metric-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0.10) 100%);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.28);
    border-radius: 24px; padding: 18px;
    box-shadow: 0px 8px 24px rgba(0,0,0,0.15), inset 0 1px 2px rgba(255,255,255,0.28);
    color: #fff !important;
}

/* ── 교정/제안 박스 ── */
.correction-box {
    background: linear-gradient(135deg, rgba(251,191,36,0.20) 0%, rgba(245,158,11,0.10) 100%);
    border-left: 4px solid rgba(251,191,36,0.80);
    backdrop-filter: blur(10px);
    border-radius: 14px; padding: 14px; margin: 8px 0;
    color: #fde68a !important;
    box-shadow: 0 4px 14px rgba(245,158,11,0.18);
}
.suggestion-box {
    background: linear-gradient(135deg, rgba(52,211,153,0.20) 0%, rgba(16,185,129,0.10) 100%);
    border-left: 4px solid rgba(52,211,153,0.80);
    backdrop-filter: blur(10px);
    border-radius: 14px; padding: 14px; margin: 8px 0;
    color: #a7f3d0 !important;
    box-shadow: 0 4px 14px rgba(16,185,129,0.18);
}

/* ── expander ── */
[data-testid="stExpander"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0.06) 100%) !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(12px) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12) !important;
}

/* ── info/success/warning 박스 ── */
[data-testid="stAlert"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.08) 100%) !important;
    border: 1px solid rgba(255,255,255,0.28) !important;
    border-radius: 18px !important;
    backdrop-filter: blur(10px) !important;
    color: #fff !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12) !important;
}

/* ── chat 메시지 ── */
[data-testid="stChatMessage"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.08) 100%) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(12px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.14), inset 0 1px 2px rgba(255,255,255,0.28) !important;
}
</style>
""", unsafe_allow_html=True)


# ─── 초기화 ────────────────────────────────────────────────────────────────────
@st.cache_resource
def init_resources():
    parser = ChineseDataParser()
    tracker = ProgressTracker('database/learning_progress.db')
    gamification = GamificationSystem(tracker)
    srs = SpacedRepetitionSystem(tracker)
    speech = SpeechHandler('audio_cache')
    ai_tutor = ChineseAITutor()
    orchestrator = OrchestratorAgent(tracker)
    eval_agent = EvalAgent()
    vocabulary = parser.load_hsk_words(level=1)
    lesson_manager = LessonManager(vocabulary)
    return {
        "parser": parser,
        "tracker": tracker,
        "gamification": gamification,
        "srs": srs,
        "speech": speech,
        "ai_tutor": ai_tutor,
        "orchestrator": orchestrator,
        "eval_agent": eval_agent,
        "vocabulary": vocabulary,
        "lesson_manager": lesson_manager,
    }


res = init_resources()


def get(key):
    return res[key]


# ─── 사이드바 ─────────────────────────────────────────────────────────────────
_PAGES = ["🏠 홈", "📚 단어 학습", "🔄 간격 복습 (SRS)", "💬 AI 회화", "📝 퀴즈", "📊 진도 확인", "🏆 업적"]


def nav_to(page: str):
    """페이지 이동 헬퍼: 세션 키를 직접 설정하고 rerun."""
    st.session_state["sidebar_sel"] = page
    st.rerun()


def render_sidebar():
    with st.sidebar:
        st.title("🇨🇳 중국어 학습")
        st.markdown("---")

        # 레벨 & XP 표시
        level_info = get("gamification").get_level_info()
        level = level_info["level"]
        xp_cur = level_info["current_in_level"]
        xp_tot = level_info["xp_for_next_level"]
        pct = level_info["progress_percent"]
        streak = level_info["current_streak"]

        st.markdown(f"### Lv.{level} 학습자")
        st.markdown(f"""
<div class="xp-bar">
  <div class="xp-fill" style="width:{pct}%"></div>
</div>
<small>{xp_cur} / {xp_tot} XP</small>
""", unsafe_allow_html=True)

        if streak > 0:
            st.markdown(f"🔥 **{streak}일 연속 학습 중!**")

        st.markdown("---")

        # key="sidebar_sel" 로 세션 상태와 직접 연결.
        # nav_to()에서 st.session_state["sidebar_sel"] = page 로 바꾸면
        # 다음 rerun 때 selectbox 가 자동으로 그 값을 보여줌.
        if "sidebar_sel" not in st.session_state:
            st.session_state["sidebar_sel"] = "🏠 홈"

        menu = st.selectbox(
            "메뉴",
            _PAGES,
            label_visibility="collapsed",
            key="sidebar_sel",
        )
        return menu


# ─── 홈 ───────────────────────────────────────────────────────────────────────
def show_home():
    st.title("🇨🇳 중국어 학습 프로그램에 오신 것을 환영합니다!")
    st.markdown("AI 기반 · 간격 반복 · 게임화 학습")

    # 오늘 학습 처리
    streak_result = get("gamification").update_streak()
    if not streak_result.get("already_done"):
        st.success(f"🔥 오늘도 학습 시작! 현재 연속: {streak_result.get('current_streak', 1)}일")

    stats = get("tracker").get_statistics()
    level_info = get("gamification").get_level_info()

    # 주요 지표
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("레벨", f"Lv.{level_info['level']}", delta=f"{level_info['total_xp']} XP")
    with c2:
        st.metric("마스터 단어", f"{stats['mastered_words']}개", delta=f"총 {stats['total_words_learned']}개")
    with c3:
        st.metric("연속 학습", f"{stats['current_streak']}일", delta=f"최고 {stats['longest_streak']}일")
    with c4:
        st.metric("평균 퀴즈", f"{stats['average_quiz_score']:.1f}점")

    # 학습 시작 버튼
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📚 단어 학습 시작", use_container_width=True, type="primary"):
            nav_to("📚 단어 학습")
    with c2:
        due = len(get("srs").get_due_cards(50))
        if st.button(f"🔄 복습하기 ({due}개 대기)", use_container_width=True):
            nav_to("🔄 간격 복습 (SRS)")
    with c3:
        if st.button("💬 AI와 대화하기", use_container_width=True):
            nav_to("💬 AI 회화")

    # 학습 곡선
    curve = get("tracker").get_learning_curve(30)
    if curve:
        import pandas as pd
        import plotly.express as px
        df = pd.DataFrame(curve, columns=["날짜", "세션수", "평균점수"])
        df["평균점수"] = df["평균점수"].fillna(0)
        fig = px.area(df, x="날짜", y="평균점수", title="최근 30일 학습 추이", markers=True,
                      color_discrete_sequence=["#764ba2"])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)


# ─── 단어 학습 ─────────────────────────────────────────────────────────────────
def show_vocabulary_lesson():
    st.header("📚 단어 학습")

    vocab = get("vocabulary")

    # ── 레슨이 진행 중이 아닐 때만 설정 UI 표시 ─────────────────────────────
    if "lesson_words" not in st.session_state:
        c1, c2 = st.columns([1, 2])
        with c1:
            words_per_lesson = st.select_slider("레슨당 단어 수", [10, 20, 30, 50, 100], value=30)
        with c2:
            total_lessons = max(1, len(vocab) // words_per_lesson)
            if total_lessons > 1:
                lesson_num = st.slider(
                    "레슨 선택", 0, total_lessons - 1, 0,
                    help=f"총 {total_lessons}개 레슨 (레슨당 {words_per_lesson}단어, 총 {len(vocab)}단어)"
                )
            else:
                lesson_num = 0
                st.info(f"📖 레슨 1 (전체 {len(vocab)}단어, {words_per_lesson}단어/레슨으로 1개 레슨)")

        if st.button("📖 레슨 시작", type="primary", use_container_width=True):
            words = get("lesson_manager").get_lesson(lesson_num, words_per_lesson)
            if not words:
                st.warning("이 레슨에 단어가 없습니다.")
                return
            # 이전 레슨 위젯 키 전부 정리
            if "lesson_words" in st.session_state:
                for j in range(len(st.session_state.lesson_words)):
                    for pfx in ("learned_", "show_def_", "tts_bytes_"):
                        st.session_state.pop(f"{pfx}{j}", None)
            session_id = get("tracker").start_session(lesson_num)
            st.session_state.lesson_words = words
            st.session_state.lesson_session_id = session_id
            st.session_state.lesson_learned = {}
            st.session_state.lesson_idx = 0   # ← 항상 0으로 리셋
            st.rerun()

        st.info("레슨 번호를 선택하고 시작 버튼을 누르세요.")
        return

    words = st.session_state.lesson_words
    total = len(words)

    # 현재 단어 인덱스
    if "lesson_idx" not in st.session_state:
        st.session_state.lesson_idx = 0

    idx = st.session_state.lesson_idx
    learned_count = sum(1 for v in st.session_state.lesson_learned.values() if v)

    # ── 상단 네비게이션 (항상 보임) ────────────────────────────────────────────
    nav_l, nav_mid, nav_r = st.columns([1, 6, 1])
    with nav_l:
        if idx > 0:
            if st.button("⬅️", use_container_width=True, help="이전 단어"):
                st.session_state.pop(f"tts_bytes_{idx}", None)
                st.session_state.pop(f"show_def_{idx}", None)
                st.session_state.lesson_idx = idx - 1
                st.rerun()
    with nav_mid:
        st.progress(idx / total, text=f"{idx + 1} / {total} 단어  |  외운 단어: {learned_count}개")
    with nav_r:
        if idx < total:
            if st.button("➡️", use_container_width=True, help="다음 단어"):
                st.session_state.pop(f"tts_bytes_{idx}", None)
                st.session_state.pop(f"show_def_{idx}", None)
                st.session_state.lesson_idx = min(idx + 1, total)
                st.rerun()

    # ── 완료 화면 ──────────────────────────────────────────────────────────────
    if idx >= total:
        st.success(f"🎉 모든 단어를 학습했습니다! (외운 단어: {learned_count}/{total}개)")
        if st.button("🎓 레슨 완료 및 저장", type="primary", use_container_width=True):
            get("tracker").end_session(
                st.session_state.lesson_session_id, learned_count, None
            )
            new_achievements = get("gamification").check_achievements()
            if new_achievements:
                for ach in new_achievements:
                    st.balloons()
                    st.success(f"🏆 업적: {ach['icon']} {ach['name']}")
            # 위젯 키 정리
            for j in range(total):
                st.session_state.pop(f"show_def_{j}", None)
            for k in ["lesson_words", "lesson_session_id", "lesson_learned", "lesson_idx"]:
                st.session_state.pop(k, None)
            st.rerun()
        if st.button("🔁 처음부터 다시", use_container_width=True):
            st.session_state.lesson_idx = 0
            st.rerun()
        return

    word = words[idx]
    defs = word.get("definitions", [])
    simplified = word["simplified"]
    traditional = word.get("traditional", simplified)
    is_same = (simplified == traditional)
    is_learned = st.session_state.lesson_learned.get(idx, False)

    # ── 병음 + 진행 표시 ────────────────────────────────────────────────────────
    st.markdown(
        f"<div style='text-align:center; font-size:1rem; opacity:0.6; margin-bottom:4px;'>"
        f"{word.get('pinyin', '')} &nbsp;|&nbsp; {idx+1}/{total}</div>",
        unsafe_allow_html=True,
    )

    # ── 한자 카드: Streamlit 컬럼으로 나란히 표시 ─────────────────────────────
    if is_same:
        # 간체자 = 번체자
        st.markdown(
            f"<div class='word-card' style='text-align:center;'>"
            f"<div style='font-size:4.5rem; font-weight:900; color:#fff; line-height:1;'>{simplified}</div>"
            f"<div style='font-size:0.78rem; color:#86efac; margin-top:10px; font-weight:600;'>"
            f"✅ 간체자 = 한자(漢字) 동일 — 중국·한국 모두 같은 형태</div></div>",
            unsafe_allow_html=True,
        )
    else:
        # 간체자 ≠ 번체자: 두 컬럼으로 분리
        col_s, col_arrow, col_t = st.columns([5, 1, 5])
        with col_s:
            st.markdown(
                f"<div class='word-card' style='text-align:center; border-color:rgba(147,197,253,0.5);'>"
                f"<div style='font-size:0.75rem; font-weight:700; color:#93c5fd; "
                f"letter-spacing:1px; margin-bottom:8px;'>간체자 简体字</div>"
                f"<div style='font-size:4rem; font-weight:900; color:#e0f2fe; line-height:1;'>{simplified}</div>"
                f"<div style='font-size:0.65rem; margin-top:8px; color:rgba(147,197,253,0.7);'>중국 본토 표준</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_arrow:
            st.markdown(
                "<div style='text-align:center; padding-top:45px; font-size:1.8rem; "
                "color:rgba(255,255,255,0.5);'>⇔</div>",
                unsafe_allow_html=True,
            )
        with col_t:
            st.markdown(
                f"<div class='word-card' style='text-align:center; border-color:rgba(251,191,36,0.5);'>"
                f"<div style='font-size:0.75rem; font-weight:700; color:#fbbf24; "
                f"letter-spacing:1px; margin-bottom:8px;'>한자(漢字) 繁體字</div>"
                f"<div style='font-size:4rem; font-weight:900; color:#fef3c7; line-height:1;'>{traditional}</div>"
                f"<div style='font-size:0.65rem; margin-top:8px; color:rgba(251,191,36,0.7);'>한국·대만·홍콩</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── 한자 설명 ──────────────────────────────────────────────────────────────
    if not is_same:
        char_pairs = [(s, t) for s, t in zip(simplified, traditional) if s != t]
        diff_note = "  ·  변환된 글자: " + "  ".join(f"{s}→{t}" for s, t in char_pairs) if char_pairs else ""
        st.info(
            f"📖 **간체자(简体字)** — 1950년대 중국이 획수를 줄여 만든 현대 표준 문자.  \n"
            f"**번체자(繁體字) = 한자(漢字)** — 수천 년 사용된 정자(正字). 한국·대만·홍콩 기준.{diff_note}"
        )
    else:
        st.success("✅ 간체자와 한자(번체자)가 동일한 글자입니다. 중국·한국 모두 같은 형태를 사용합니다.")

    # ── 뜻 보기 ────────────────────────────────────────────────────────────────
    show_key = f"show_def_{idx}"
    if show_key not in st.session_state:
        st.session_state[show_key] = False

    if not st.session_state[show_key]:
        if st.button("💡 뜻 보기", use_container_width=True):
            st.session_state[show_key] = True
            st.rerun()
    else:
        meaning = " / ".join(defs) if defs else ""
        st.markdown(
            f"<div style='text-align:center; padding:14px; font-size:1.3rem; font-weight:700; "
            f"color:#fde68a; background:rgba(255,255,255,0.12); border-radius:14px; "
            f"border:1px solid rgba(255,255,255,0.2); margin:4px 0;'>{meaning}</div>",
            unsafe_allow_html=True,
        )

    # ── TTS 발음 (base64 HTML audio — 가장 안정적) ────────────────────────────
    tts_key = f"tts_bytes_{idx}"
    if st.button("🔊 발음 듣기", use_container_width=True):
        with st.spinner("음성 생성 중..."):
            tts_data = get("speech").tts_bytes(simplified)
        if tts_data:
            st.session_state[tts_key] = tts_data
        else:
            st.warning(f"TTS 오류 — 병음: {word.get('pinyin', '')}")
    if tts_key in st.session_state:
        import base64
        audio_b64 = base64.b64encode(st.session_state[tts_key]).decode()
        st.markdown(
            f'<audio controls style="width:100%;height:54px;margin-top:6px;border-radius:12px;"'
            f' src="data:audio/mp3;base64,{audio_b64}"></audio>',
            unsafe_allow_html=True,
        )

    # ── 외웠어요 / 레슨 중단 ──────────────────────────────────────────────────
    st.markdown("")
    c_check, c_end = st.columns([3, 1])
    with c_check:
        if not is_learned:
            if st.button("✅ 외웠어요! (다음으로)", use_container_width=True, type="primary"):
                st.session_state.lesson_learned[idx] = True
                get("tracker").update_word_mastery(word, True)
                xp_result = get("gamification").award_xp("word_learned")
                if xp_result.get("leveled_up"):
                    st.balloons()
                    st.success(f"🎉 레벨업! Lv.{xp_result['level']}")
                else:
                    st.toast(f"+{xp_result['xp_gained']} XP")
                st.session_state.pop(f"tts_bytes_{idx}", None)
                st.session_state.pop(f"show_def_{idx}", None)
                st.session_state.lesson_idx = min(idx + 1, total)
                st.rerun()
        else:
            st.success("✅ 이 단어는 외웠어요!")
    with c_end:
        if st.button("🏁 중단", use_container_width=True, help="레슨 중단 및 저장"):
            get("tracker").end_session(
                st.session_state.lesson_session_id, learned_count, None
            )
            for j in range(total):
                st.session_state.pop(f"show_def_{j}", None)
                st.session_state.pop(f"tts_bytes_{j}", None)
            for k in ["lesson_words", "lesson_session_id", "lesson_learned", "lesson_idx"]:
                st.session_state.pop(k, None)
            st.rerun()


# ─── SRS 복습 ─────────────────────────────────────────────────────────────────
def show_srs_review():
    st.header("🔄 간격 반복 복습 (SM-2)")
    st.caption("과학적 간격 반복으로 최적 시점에 복습합니다.")

    due_cards = get("srs").get_due_cards(20)

    if not due_cards:
        st.success("🎉 오늘 복습할 단어가 없습니다! 내일 다시 확인해보세요.")
        srs_stats = get("srs").get_statistics()
        c1, c2 = st.columns(2)
        with c1:
            st.metric("전체 단어", srs_stats["total_words"])
        with c2:
            st.metric("마스터 완료", srs_stats["mastered"])
        return

    st.info(f"📋 오늘 복습할 단어: **{len(due_cards)}개**")

    if "srs_idx" not in st.session_state:
        st.session_state.srs_idx = 0
        st.session_state.srs_correct = 0
        st.session_state.srs_total = 0
        st.session_state.srs_show_answer = False

    idx = st.session_state.srs_idx
    if idx >= len(due_cards):
        st.success(f"🎉 복습 완료! {st.session_state.srs_correct}/{st.session_state.srs_total} 정답")
        get("gamification").award_xp("daily_goal_met")
        if st.button("복습 다시 시작"):
            for k in ["srs_idx", "srs_correct", "srs_total", "srs_show_answer"]:
                del st.session_state[k]
            st.rerun()
        return

    card = due_cards[idx]
    total = len(due_cards)

    st.progress((idx) / total, text=f"{idx+1}/{total}")

    # 단어 카드
    st.markdown(f"""
<div class="word-card" style="max-width:400px; margin:auto;">
  <div class="chinese">{card['simplified']}</div>
  <div class="pinyin">{card.get('pinyin', '')}</div>
</div>""", unsafe_allow_html=True)

    if not st.session_state.srs_show_answer:
        if st.button("💡 정답 보기", use_container_width=True):
            st.session_state.srs_show_answer = True
            st.rerun()
    else:
        defs = card.get("definitions", [])
        st.markdown(f"### 의미: {' / '.join(defs)}")
        st.markdown("**얼마나 기억했나요?**")

        cols = st.columns(4)
        quality_labels = [
            ("😫 완전 까먹음", 0, "red"),
            ("😕 어렵게 기억", 2, "orange"),
            ("🙂 약간 망설임", 4, "blue"),
            ("😄 완벽!", 5, "green"),
        ]
        for col, (label, quality, _) in zip(cols, quality_labels):
            with col:
                if st.button(label, use_container_width=True):
                    result = get("srs").process_review(card["simplified"], quality)
                    if quality >= 3:
                        st.session_state.srs_correct += 1
                        get("gamification").award_xp("quiz_correct")
                    st.session_state.srs_total += 1
                    st.session_state.srs_idx += 1
                    st.session_state.srs_show_answer = False
                    st.rerun()


# ─── AI 회화 ──────────────────────────────────────────────────────────────────
def show_conversation():
    st.header("💬 AI 회화 연습")
    st.caption("AI 튜터와 중국어로 대화하며 실력을 키우세요!")

    tutor = get("ai_tutor")

    # ── API 키 상태 표시 및 런타임 입력 ──────────────────────────────────────
    if not tutor.has_api:
        with st.expander("⚙️ Claude API 키 설정 (선택 — 없어도 기본 대화 가능)", expanded=True):
            st.markdown("API 키를 설정하면 **진짜 AI 선생님**과 자유로운 대화가 가능합니다.")
            api_input = st.text_input(
                "ANTHROPIC_API_KEY",
                type="password",
                placeholder="sk-ant-...",
                key="api_key_input",
            )
            if st.button("🔑 API 키 적용"):
                if api_input.startswith("sk-ant-"):
                    import anthropic as _anth
                    try:
                        tutor.client = _anth.Anthropic(api_key=api_input)
                        tutor.client.messages.create(
                            model="claude-haiku-4-5-20251001",
                            max_tokens=5,
                            messages=[{"role": "user", "content": "hi"}],
                        )
                        st.success("✅ API 키 확인 완료! 이제 실제 AI와 대화합니다.")
                        st.rerun()
                    except Exception as e:
                        tutor.client = None
                        st.error(f"❌ 키 오류: {e}")
                else:
                    st.warning("올바른 Anthropic API 키 형식이 아닙니다 (sk-ant-로 시작해야 합니다).")
        st.info("🤖 **기본 대화 모드** — 주요 패턴(인사·날씨·음식 등)으로 연습 중입니다. "
                "API 키 없이도 자유롭게 입력해보세요!")
    else:
        st.success("🟢 Claude AI 연결됨 — 실시간 AI 선생님과 대화 중!")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_corrections = []
        st.session_state.chat_session_id = get("tracker").start_session(0, "conversation")
        st.session_state.chat_turn = 0

    # 음성 모드 토글
    voice_mode = st.toggle("🎤 음성 모드", value=False, key="voice_mode_toggle",
                           help="켜면 AI 응답을 자동 재생하고, 마이크로 입력할 수 있습니다.")

    # 대화 기록 표시
    for i, msg in enumerate(st.session_state.chat_history):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant":
                # TTS 재생 버튼 (음성 모드면 최신 응답 자동 재생)
                ai_text_for_tts = msg["content"].split("\n")[0]
                is_latest = (i == len(st.session_state.chat_history) - 1)
                tts_col, _ = st.columns([1, 5])
                with tts_col:
                    if st.button("🔊", key=f"tts_btn_{i}", help="음성 재생"):
                        tts_data = get("speech").tts_bytes(ai_text_for_tts)
                        if tts_data:
                            st.audio(tts_data, format='audio/mp3', autoplay=True)
                        else:
                            st.caption("TTS를 사용할 수 없습니다.")
                # 음성 모드 + 최신 응답 → 자동 재생
                if voice_mode and is_latest and st.session_state.get("play_tts_latest", False):
                    tts_data = get("speech").tts_bytes(ai_text_for_tts)
                    if tts_data:
                        st.audio(tts_data, format='audio/mp3', autoplay=True)
                    st.session_state.play_tts_latest = False

                if i < len(st.session_state.chat_corrections):
                    correction = st.session_state.chat_corrections[i // 2]
                    if correction.get("corrections"):
                        with st.expander("📝 교정 사항"):
                            for c in correction["corrections"]:
                                st.markdown(f"""
<div class="correction-box">
  ❌ <b>원문:</b> {c.get('original', '')} → ✅ <b>교정:</b> {c.get('corrected', '')}<br>
  💡 {c.get('explanation', '')}
</div>""", unsafe_allow_html=True)
                    if correction.get("suggestions"):
                        for s in correction["suggestions"]:
                            st.markdown(f'<div class="suggestion-box">💡 {s}</div>', unsafe_allow_html=True)

    # ── 음성 입력 ────────────────────────────────────────────────────────────
    if voice_mode:
        st.markdown("---")
        v_col, info_col = st.columns([1, 2])
        with v_col:
            try:
                audio_value = st.audio_input("🎙️ 녹음하려면 클릭", key="voice_rec")
                if audio_value is not None:
                    raw_bytes = audio_value.read()
                    with st.spinner("🎙️ 음성 인식 중..."):
                        stt_result = get("speech").stt_from_bytes(raw_bytes, language="zh-CN")
                    if stt_result:
                        st.session_state.voice_transcribed = stt_result
                    elif stt_result == "":
                        st.warning("음성을 인식하지 못했습니다. 다시 시도해주세요.")
                    else:
                        st.error("음성 인식에 실패했습니다.")
            except Exception as e:
                st.caption(f"음성 입력 불가: {e}")

        with info_col:
            if "voice_transcribed" in st.session_state:
                vtxt = st.session_state.voice_transcribed
                st.info(f"🎙️ 인식 결과: **{vtxt}**")
                if st.button("📤 전송하기", key="send_voice_btn", type="primary"):
                    st.session_state.pending_voice_input = vtxt
                    del st.session_state.voice_transcribed
                    st.rerun()
            else:
                st.caption("중국어로 말하면 자동으로 텍스트로 변환됩니다.")

    # 사용자 입력 (텍스트)
    user_input = st.chat_input("중국어 또는 한국어로 입력하세요...")

    # 음성 입력 대기 처리
    if not user_input and "pending_voice_input" in st.session_state:
        user_input = st.session_state.pop("pending_voice_input")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.spinner("AI 튜터가 응답 중..."):
            response = get("ai_tutor").chat_practice(user_input)

        ai_text = response.get("response", "很好！继续加油！")
        pinyin = response.get("response_pinyin", "")
        translation = response.get("response_translation", "")

        display = ai_text
        if pinyin:
            display += f"\n*{pinyin}*"
        if translation:
            display += f"\n**{translation}**"

        st.session_state.chat_history.append({"role": "assistant", "content": display})
        st.session_state.chat_corrections.append(response)
        # 음성 모드: 최신 응답 자동 재생 플래그
        st.session_state.play_tts_latest = True

        # 저장
        st.session_state.chat_turn += 1
        get("tracker").save_conversation_turn(
            st.session_state.chat_session_id,
            st.session_state.chat_turn,
            user_input, ai_text,
            str(response.get("corrections", [])),
            str(response.get("suggestions", [])),
        )
        get("gamification").award_xp("conversation_turn")
        st.rerun()

    # 대화 초기화
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 대화 초기화"):
            for k in ["chat_history", "chat_corrections", "chat_session_id", "chat_turn"]:
                if k in st.session_state:
                    del st.session_state[k]
            get("ai_tutor").conversation_history = []
            st.rerun()
    with col2:
        if st.button("📖 문법 설명 요청"):
            if st.session_state.chat_history:
                last_user = next(
                    (m["content"] for m in reversed(st.session_state.chat_history) if m["role"] == "user"),
                    None
                )
                if last_user:
                    with st.spinner("문법 설명 생성 중..."):
                        explanation = get("orchestrator").tutor_agent.explain_grammar(last_user)
                    st.info(explanation.get("structure", ""))
                    for gp in explanation.get("grammar_points", []):
                        st.markdown(f"- **{gp.get('point', '')}**: {gp.get('explanation', '')}")


# ─── 퀴즈 ─────────────────────────────────────────────────────────────────────
def show_quiz():
    st.header("📝 퀴즈")

    vocab = get("vocabulary")
    stats = get("tracker").get_statistics()

    # 퀴즈 설정
    if "quiz_data" not in st.session_state:
        c1, c2, c3 = st.columns(3)
        with c1:
            count = st.slider("문제 수", 10, 200, 100)
        with c2:
            lesson_start = st.slider("레슨 시작", 0, max(0, len(vocab) // 10 - 1), 0)
        with c3:
            st.write("")  # spacer

        if st.button("🎯 퀴즈 시작", type="primary"):
            word_slice = vocab[lesson_start * 10: lesson_start * 10 + 500]
            if not word_slice:
                word_slice = vocab
            recent_scores = []
            # 최근 점수 기반 adaptive
            recent_scores = [stats.get("average_quiz_score", 70)] * 3

            questions = get("eval_agent").generate_adaptive_quiz(word_slice, recent_scores, count)
            session_id = get("tracker").start_session(lesson_start, "quiz")
            st.session_state.quiz_data = questions
            st.session_state.quiz_answers = {}
            st.session_state.quiz_session_id = session_id
            st.rerun()
        return

    questions = st.session_state.quiz_data
    st.info(f"총 {len(questions)}문제")

    with st.form("quiz_form"):
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}.** {q['question']}")
            q_type = q.get("type", "translation")

            if q_type == "fill_blank":
                answer = st.text_input(f"답 입력 #{i+1}", key=f"q_{i}", label_visibility="collapsed")
            else:
                options = q.get("options", [])
                if options:
                    answer = st.radio(f"선택 #{i+1}", options, key=f"q_{i}", label_visibility="collapsed")
                else:
                    answer = st.text_input(f"답 입력 #{i+1}", key=f"q_{i}", label_visibility="collapsed")

            st.session_state.quiz_answers[i] = answer
            st.markdown("---")

        submitted = st.form_submit_button("✅ 채점하기", type="primary")

    if submitted:
        score = 0
        total_points = 0
        results = []

        for i, q in enumerate(questions):
            user_answer = st.session_state.quiz_answers.get(i, "")
            eval_result = get("eval_agent").evaluate_answer(q, user_answer)
            results.append(eval_result)
            score += eval_result["score"]
            total_points += q.get("points", 5)

        percentage = (score / total_points * 100) if total_points > 0 else 0

        if percentage >= 100:
            st.balloons()
        get("tracker").end_session(
            st.session_state.quiz_session_id, 0, percentage
        )
        xp_gained = get("gamification").award_xp("quiz_correct", extra_multiplier=percentage / 100)
        if percentage >= 100:
            get("gamification").award_xp("quiz_perfect")

        # 결과 표시
        st.markdown(f"## 결과: {score}/{total_points}점 ({percentage:.1f}%)")
        if percentage >= 80:
            st.success("🎉 훌륭해요!")
        elif percentage >= 60:
            st.warning("💪 조금 더 연습해봐요!")
        else:
            st.error("📚 단어를 더 복습해보세요!")

        st.info(f"+{xp_gained['xp_gained']} XP 획득!")

        for i, (q, r) in enumerate(zip(questions, results)):
            if r["is_correct"]:
                st.success(f"Q{i+1} ✓ {r['feedback']}")
            else:
                st.error(f"Q{i+1} ✗ {r['feedback']}")
            if r.get("explanation"):
                st.caption(r["explanation"])

        # 새 퀴즈
        if st.button("🔄 새 퀴즈"):
            for k in ["quiz_data", "quiz_answers", "quiz_session_id"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()


# ─── 진도 확인 ─────────────────────────────────────────────────────────────────
def show_progress():
    st.header("📊 학습 진도")

    stats = get("tracker").get_statistics()
    level_info = get("gamification").get_level_info()

    # 주요 지표
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("레벨", f"Lv.{level_info['level']}")
    with c2:
        st.metric("총 XP", f"{level_info['total_xp']}")
    with c3:
        st.metric("학습 시간", f"{stats['total_study_hours']:.1f}시간")
    with c4:
        st.metric("마스터 단어", f"{stats['mastered_words']}개")

    # XP 진행바
    st.markdown(f"**다음 레벨까지**: {level_info['current_in_level']} / {level_info['xp_for_next_level']} XP")
    st.progress(level_info["progress_percent"] / 100)

    st.markdown("---")

    # 단어 마스터리 분포
    col_chart, col_review = st.columns([2, 1])

    with col_chart:
        curve = get("tracker").get_learning_curve(30)
        if curve:
            import pandas as pd
            import plotly.express as px
            df = pd.DataFrame(curve, columns=["날짜", "세션수", "평균점수"])
            df["평균점수"] = df["평균점수"].fillna(0)
            fig = px.bar(df, x="날짜", y="세션수", title="30일 학습 세션",
                         color_discrete_sequence=["#764ba2"])
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("아직 데이터가 없습니다. 학습을 시작해보세요!")

    with col_review:
        st.subheader("복습 대기 단어")
        review_words = get("tracker").get_words_for_review(8)
        if review_words:
            for w in review_words:
                st.markdown(f"- **{w[0]}** ({w[2]}) — *{w[1]}*")
        else:
            st.success("복습할 단어가 없습니다! 🎉")

    # 데이터 에이전트 인사이트
    st.markdown("---")
    st.subheader("💡 학습 인사이트")
    data_agent = get("orchestrator").data_agent
    if data_agent:
        analysis = data_agent.analyze_progress()
        for insight in analysis.get("insights", []):
            st.info(insight)
        st.subheader("📋 추천 사항")
        for rec in analysis.get("recommendations", []):
            st.markdown(f"- {rec}")


# ─── 업적 ─────────────────────────────────────────────────────────────────────
def show_achievements():
    st.header("🏆 업적")

    achievements = get("gamification").get_all_achievements()

    if not achievements:
        st.info("아직 업적이 없습니다. 학습을 시작하면 업적을 달성할 수 있어요!")
        return

    # 카테고리별 분류
    categories = {"words": "📖 단어", "streak": "🔥 연속", "score": "🎯 점수",
                  "time": "⏱️ 시간", "special": "⭐ 특별"}

    for cat_key, cat_name in categories.items():
        cat_achievements = [a for a in achievements if a.get("category") == cat_key]
        if not cat_achievements:
            continue

        st.subheader(cat_name)
        cols = st.columns(min(4, len(cat_achievements)))
        for i, ach in enumerate(cat_achievements):
            with cols[i % len(cols)]:
                css_class = "badge-unlocked" if ach["unlocked"] else "badge-locked"
                icon = ach.get("icon", "🏅")
                st.markdown(f"""
<div class="{css_class}" style="text-align:center; width:100%;">
  <div style="font-size:2rem;">{icon}</div>
  <b>{ach['name']}</b><br>
  <small>{ach['description']}</small>
  {'<br><small>✅ 달성!</small>' if ach['unlocked'] else ''}
</div>""", unsafe_allow_html=True)

    unlocked = sum(1 for a in achievements if a["unlocked"])
    st.markdown("---")
    st.metric("달성한 업적", f"{unlocked} / {len(achievements)}")
    st.progress(unlocked / len(achievements) if achievements else 0)


# ─── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    menu = render_sidebar()

    if menu == "🏠 홈":
        show_home()
    elif menu == "📚 단어 학습":
        show_vocabulary_lesson()
    elif menu == "🔄 간격 복습 (SRS)":
        show_srs_review()
    elif menu == "💬 AI 회화":
        show_conversation()
    elif menu == "📝 퀴즈":
        show_quiz()
    elif menu == "📊 진도 확인":
        show_progress()
    elif menu == "🏆 업적":
        show_achievements()


if __name__ == "__main__":
    main()
