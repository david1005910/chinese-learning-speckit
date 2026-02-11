"""
AI 튜터 모듈
Claude API를 활용한 대화 생성 및 학습 지원
API 키 없을 때는 내장 폴백 모드로 동작
"""

import os
import random
from typing import List, Dict, Optional

try:
    import anthropic
except ImportError:
    anthropic = None

MODEL = "claude-sonnet-4-5-20250929"

# ── 폴백용 내장 대화 패턴 ────────────────────────────────────────────────────
_FALLBACK_RESPONSES = [
    {
        "triggers": ["你好", "안녕", "hello", "hi"],
        "response": "你好！很高兴认识你！(Nǐ hǎo! Hěn gāoxìng rènshi nǐ!)\n**안녕하세요! 만나서 반가워요!**\n\n중국어 연습을 시작해봐요. 오늘 날씨 이야기를 해볼까요? 试着说：今天天气怎么样？(Jīntiān tiānqì zěnmeyàng?) — 오늘 날씨 어때요?",
    },
    {
        "triggers": ["谢谢", "감사", "고마워"],
        "response": "不客气！(Bú kèqi!) **천만에요!**\n\n아주 자연스러운 표현이에요! 비슷한 표현: 不用谢 (Bùyòng xiè) — 감사할 것 없어요.",
    },
    {
        "triggers": ["再见", "바이", "bye", "안녕히"],
        "response": "再见！(Zàijiàn!) **안녕히 가세요!**\n\n오늘 연습 정말 잘 하셨어요! 내일 또 만나요~ 明天见！(Míngtiān jiàn!)",
    },
    {
        "triggers": ["我", "나는", "저는"],
        "response": "很好！(Hěn hǎo!) **잘했어요!**\n\n'我'(Wǒ)는 '나/저'라는 뜻이에요. 자기소개를 해보세요:\n我叫___。(Wǒ jiào ___.) — 제 이름은 ___입니다.\n我是学生。(Wǒ shì xuéshēng.) — 저는 학생입니다.",
    },
    {
        "triggers": ["吃", "먹", "food", "음식"],
        "response": "你喜欢吃什么？(Nǐ xǐhuān chī shénme?) **어떤 음식을 좋아하세요?**\n\n食物 단어:\n- 米饭 (mǐfàn) — 밥\n- 面条 (miàntiáo) — 국수\n- 水果 (shuǐguǒ) — 과일\n\n我喜欢吃___。(Wǒ xǐhuān chī ___.) 라고 말해보세요!",
    },
    {
        "triggers": ["学习", "공부", "배우", "study"],
        "response": "学中文很有趣！(Xué Zhōngwén hěn yǒuqù!) **중국어 공부는 재미있어요!**\n\n학습 팁:\n1. 매일 조금씩 꾸준히\n2. 발음(声调 shēngdiào)에 집중\n3. 실생활 표현부터 시작\n\n오늘도 화이팅! 加油！(Jiāyóu!)",
    },
    {
        "triggers": ["天气", "날씨", "weather"],
        "response": "今天天气怎么样？(Jīntiān tiānqì zěnmeyàng?) **오늘 날씨 어때요?**\n\n날씨 표현:\n- 晴天 (qíngtiān) — 맑은 날\n- 下雨 (xià yǔ) — 비가 옵니다\n- 很热 (hěn rè) — 매우 덥습니다\n- 很冷 (hěn lěng) — 매우 춥습니다",
    },
    {
        "triggers": ["多少", "얼마", "가격", "price"],
        "response": "这个多少钱？(Zhège duōshao qián?) **이것은 얼마예요?**\n\n쇼핑 표현:\n- 贵 (guì) — 비싸다\n- 便宜 (piányí) — 싸다\n- 打折 (dǎzhé) — 할인하다\n\n숫자 연습: 一二三四五 (yī èr sān sì wǔ)",
    },
]

_DEFAULT_RESPONSES = [
    "很好！(Hěn hǎo!) **잘했어요!** 계속 연습해봐요.\n\n중국어로 한 문장 더 말해보세요. 예를 들어:\n- 我今天很高兴。(Wǒ jīntiān hěn gāoxìng.) — 오늘 기분이 좋아요.\n- 中文很有意思。(Zhōngwén hěn yǒu yìsi.) — 중국어는 재미있어요.",
    "你说得很好！(Nǐ shuō de hěn hǎo!) **아주 잘 말했어요!**\n\n더 연습해볼까요? 오늘 배운 단어를 사용해서 문장을 만들어보세요!",
    "继续加油！(Jìxù jiāyóu!) **계속 화이팅!**\n\n궁금한 표현이 있으면 한국어로 물어봐도 돼요. 제가 중국어 표현을 알려드릴게요!",
    "不错！(Búcuò!) **나쁘지 않아요 (잘했어요)!**\n\n팁: 큰 소리로 따라 읽으면 발음이 빨리 늘어요. 声调(성조)에 주의하면서 연습해보세요!",
]


def _fallback_chat(user_input: str) -> Dict:
    """API 없이 동작하는 내장 폴백 대화"""
    lower = user_input.lower()
    for pattern in _FALLBACK_RESPONSES:
        if any(t in lower for t in pattern["triggers"]):
            return {
                "response": pattern["response"],
                "suggestions": ["더 많은 표현을 연습해보세요!"],
                "corrections": [],
                "fallback": True,
            }
    return {
        "response": random.choice(_DEFAULT_RESPONSES),
        "suggestions": [],
        "corrections": [],
        "fallback": True,
    }


class ChineseAITutor:
    """중국어 AI 튜터"""

    def __init__(self, api_key: Optional[str] = None):
        self.conversation_history: List[Dict] = []
        self.client = None

        if anthropic is None:
            return

        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            return

        try:
            self.client = anthropic.Anthropic(api_key=key)
        except Exception:
            self.client = None

    @property
    def has_api(self) -> bool:
        return self.client is not None

    def chat_practice(self, user_input: str, context: str = "") -> Dict:
        """대화 연습 - API 없으면 폴백 모드"""
        if not self.has_api:
            return _fallback_chat(user_input)

        self.conversation_history.append({"role": "user", "content": user_input})

        system_prompt = """당신은 친절한 중국어 회화 선생님입니다.
학생과 중국어로 대화하면서 자연스럽게 교정해주세요.

규칙:
1. 학생의 중국어에 문법 오류가 있으면 정중하게 고쳐주세요
2. 더 자연스러운 표현을 제안해주세요
3. 중국어로 대화하되 병음과 한국어 번역을 함께 제공하세요
4. 격려하고 긍정적인 피드백을 주세요
5. 응답은 200자 이내로 간결하게 해주세요

""" + context

        try:
            messages = self.conversation_history[-6:]
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=800,
                system=system_prompt,
                messages=messages,
            )
            text = response.content[0].text
            self.conversation_history.append({"role": "assistant", "content": text})
            return {
                "response": text,
                "suggestions": [],
                "corrections": [],
                "fallback": False,
            }
        except anthropic.AuthenticationError:
            self.client = None          # 이후 요청도 폴백으로
            return _fallback_chat(user_input)
        except Exception as e:
            print(f"API Error: {e}")
            return _fallback_chat(user_input)

    def generate_dialogue(self, vocabulary: List[str],
                          level: str = "beginner", situation: str = "일상") -> List[Dict]:
        if not self.has_api:
            return self._generate_simple_dialogue(vocabulary)

        prompt = f"""단어 목록: {', '.join(vocabulary)}
난이도: {level}, 상황: {situation}

다음 형식으로 대화 3개를 JSON 배열로 만들어주세요:
[{{"context":"상황설명","chinese":"중국어","pinyin":"병음","korean":"번역","grammar_note":"문법"}}]
JSON만 출력하세요."""

        try:
            msg = self.client.messages.create(
                model=MODEL, max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            import json, re
            raw = msg.content[0].text
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            print(f"API Error: {e}")
        return self._generate_simple_dialogue(vocabulary)

    def explain_grammar(self, sentence: str) -> str:
        if not self.has_api:
            return f"**'{sentence}'** 문장 분석\n\nAI 문법 설명은 ANTHROPIC_API_KEY 설정 후 이용할 수 있습니다.\n\n기본 팁: 중국어 어순은 주어+동사+목적어(SVO)입니다."

        prompt = f"""중국어 문장 '{sentence}'의 문법을 초보자 수준으로 한국어로 설명해주세요.
문장구조, 주요 문법포인트, 예문 2개, 흔한 실수를 포함해주세요. 300자 이내로."""

        try:
            msg = self.client.messages.create(
                model=MODEL, max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text
        except Exception as e:
            print(f"API Error: {e}")
            return "문법 설명을 생성할 수 없습니다."

    def generate_exercises(self, grammar_point: str, count: int = 5) -> List[Dict]:
        if not self.has_api:
            return []
        try:
            msg = self.client.messages.create(
                model=MODEL, max_tokens=1500,
                messages=[{"role": "user", "content":
                    f"'{grammar_point}' 문법 연습문제 {count}개를 JSON으로 만들어주세요. "
                    f'[{{"type":"","question":"","choices":[],"answer":"","explanation":""}}] 형식으로.'}]
            )
            import json, re
            raw = msg.content[0].text
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            print(f"API Error: {e}")
        return []

    def _generate_simple_dialogue(self, vocabulary: List[str]) -> List[Dict]:
        patterns = [
            {"context": "인사", "chinese": "你好！", "pinyin": "Nǐ hǎo!", "korean": "안녕하세요!", "grammar_note": "기본 인사"},
            {"context": "감사", "chinese": "谢谢。", "pinyin": "Xièxie.", "korean": "감사합니다.", "grammar_note": "감사 표현"},
            {"context": "작별", "chinese": "再见！", "pinyin": "Zàijiàn!", "korean": "안녕히 가세요!", "grammar_note": "작별 인사"},
        ]
        return patterns[:max(1, min(3, len(vocabulary)))]
