"""
성조 추출 및 다이어그램 유닛 테스트
"""

import pytest
from unittest.mock import patch


# ─── data_parser 성조 메서드 ─────────────────────────────────────────────────

class TestGetToneNumbers:
    def test_single_char_tones(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        # 妈 = 1성
        assert parser.get_tone_numbers("妈")[0] == 1
        # 麻 = 2성
        assert parser.get_tone_numbers("麻")[0] == 2
        # 马 = 3성
        assert parser.get_tone_numbers("马")[0] == 3
        # 骂 = 4성
        assert parser.get_tone_numbers("骂")[0] == 4

    def test_multi_char_word(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        # 你好 = [3, 3]
        tones = parser.get_tone_numbers("你好")
        assert len(tones) == 2
        assert tones[0] == 3
        assert tones[1] == 3

    def test_mixed_tones(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        # 中国 = [1, 2]
        tones = parser.get_tone_numbers("中国")
        assert len(tones) == 2
        assert tones[0] == 1
        assert tones[1] == 2

    def test_returns_list_of_ints(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        tones = parser.get_tone_numbers("学习")
        assert isinstance(tones, list)
        assert all(isinstance(t, int) for t in tones)
        assert all(1 <= t <= 5 for t in tones)

    def test_empty_string(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        tones = parser.get_tone_numbers("")
        assert tones == []


class TestGetPinyinWithTones:
    def test_returns_list_of_dicts(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        result = parser.get_pinyin_with_tones("你好")
        assert isinstance(result, list)
        assert len(result) == 2
        for item in result:
            assert "syllable" in item
            assert "tone_number" in item
            assert "tone3" in item

    def test_tone_number_matches(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        result = parser.get_pinyin_with_tones("妈")
        assert result[0]["tone_number"] == 1

    def test_syllable_has_tone_mark(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        result = parser.get_pinyin_with_tones("好")
        # syllable should be the tone-marked pinyin (e.g. "hǎo")
        assert result[0]["syllable"] != ""

    def test_tone3_has_number(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        result = parser.get_pinyin_with_tones("好")
        # tone3 format should end with a digit
        assert result[0]["tone3"][-1].isdigit()

    def test_empty_string(self):
        from src.core.data_parser import ChineseDataParser
        parser = ChineseDataParser()

        result = parser.get_pinyin_with_tones("")
        assert result == []


# ─── tone_diagram 모듈 ──────────────────────────────────────────────────────

class TestToneIndicatorHtml:
    def test_returns_html_string(self):
        from src.ui.tone_diagram import tone_indicator_html
        html = tone_indicator_html(1)
        assert isinstance(html, str)
        assert "<span" in html

    def test_contains_tone_number(self):
        from src.ui.tone_diagram import tone_indicator_html
        html = tone_indicator_html(2)
        assert "2" in html

    def test_neutral_tone_label(self):
        from src.ui.tone_diagram import tone_indicator_html
        html = tone_indicator_html(5)
        # 경성은 "轻" 표시
        assert "轻" in html

    def test_color_applied(self):
        from src.ui.tone_diagram import tone_indicator_html, TONE_COLORS
        for tone, color in TONE_COLORS.items():
            html = tone_indicator_html(tone)
            assert color.lower() in html.lower()


class TestRenderAllTonesChart:
    def test_returns_bytes(self):
        from src.ui.tone_diagram import render_all_tones_chart, HAS_MPL
        result = render_all_tones_chart()
        if HAS_MPL:
            assert isinstance(result, bytes)
            assert len(result) > 0
            # PNG header check
            assert result[:4] == b"\x89PNG"
        else:
            assert result == b""


class TestRenderWordToneDiagram:
    def test_returns_bytes_for_valid_input(self):
        from src.ui.tone_diagram import render_word_tone_diagram, HAS_MPL
        syllables = [
            {"syllable": "nǐ", "tone_number": 3, "tone3": "ni3"},
            {"syllable": "hǎo", "tone_number": 3, "tone3": "hao3"},
        ]
        result = render_word_tone_diagram(syllables)
        if HAS_MPL:
            assert isinstance(result, bytes)
            assert len(result) > 0
            assert result[:4] == b"\x89PNG"
        else:
            assert result == b""

    def test_empty_input(self):
        from src.ui.tone_diagram import render_word_tone_diagram
        result = render_word_tone_diagram([])
        assert result == b""
