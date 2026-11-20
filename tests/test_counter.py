import random
import tempfile
import unicodedata
import unittest
from pathlib import Path

import word_counter
from buoc_dau import analyse, load_lexicon, normalise, segment
from buoc_dau.counter import looks_vietnamese
from tests import oracles

VI = ["sinh", "viên", "Việt", "Nam", "học", "lập", "trình", "rất", "chăm", "chỉ", "ở", "thành", "phố", "Hồ", "Chí", "Minh", "đại", "học", "công", "nghệ", "kỹ", "sư", "phần", "mềm", "ngày", "xuân", "mùa", "bạn", "bè", "gia", "đình"]
HAN = [chr(c) for c in (0x4E2D, 0x6587, 0x7F16, 0x7A0B, 0x3400, 0x4DBF, 0x20000, 0x2A6DF, 0xF900, 0x9FFF)]
KANA = [chr(c) for c in (0x3042, 0x30A2, 0x3093, 0x30F3, 0x30FC, 0x31F0, 0xFF76)]
HANGUL = [chr(c) for c in (0xAC00, 0xD55C, 0xAE00, 0xD7A3)]
THAI = [chr(c) for c in (0x0E01, 0x0E2D, 0x0E31, 0x0E48, 0x0E50)]
OTHER = ["😀", "。", "，", "!", chr(0x2014), "​", "\t", "42", "3.14", "é", "ß"]


def random_text(rng, n=60):
    pools = [VI, HAN, KANA, HANGUL, THAI, OTHER]
    parts = []
    for _ in range(n):
        pool = rng.choice(pools)
        parts.append(rng.choice(pool))
        parts.append(rng.choice([" ", "", "\n", " "]))
    return "".join(parts)


class TestUnicodeCounting(unittest.TestCase):
    def test_script_counts_match_the_unicode_character_names(self):
        rng = random.Random(1)
        for _ in range(300):
            t = random_text(rng)
            c = analyse(t)
            self.assertEqual((c.han, c.kana, c.hangul_syllables, c.thai_characters), (oracles.han(t), oracles.kana(t), oracles.hangul(t), oracles.thai(t)), t)
            self.assertEqual(c.characters, oracles.visible(t), t)

    def test_precomposed_and_decomposed_text_count_the_same(self):
        rng = random.Random(2)
        for _ in range(200):
            t = " ".join(rng.choice(VI) for _ in range(rng.randint(3, 30))) + rng.choice(["", ".", " 2026"])
            nfd = unicodedata.normalize("NFD", t)
            self.assertNotEqual(t, nfd) if any(ord(c) > 127 for c in t) else None
            self.assertEqual(analyse(t), analyse(nfd))
            self.assertEqual(analyse(t), analyse(unicodedata.normalize("NFC", nfd)))

    def test_a_decomposed_letter_is_one_character(self):
        self.assertEqual(analyse("ệ").characters, 1)
        self.assertEqual(analyse(unicodedata.normalize("NFD", "ệ")).characters, 1)

    def test_vietnamese_syllables_are_the_space_separated_tokens(self):
        rng = random.Random(3)
        for _ in range(100):
            t = " ".join(rng.choice(VI) for _ in range(rng.randint(5, 40)))
            c = analyse(t)
            self.assertTrue(c.vietnamese)
            self.assertEqual(c.syllables, len(t.split()))

    def test_english_is_not_called_vietnamese(self):
        c = analyse("The quick brown fox jumps over the lazy dog, and then it went home.")
        self.assertFalse(c.vietnamese)
        self.assertIsNone(c.syllables)
        self.assertEqual(c.latin_tokens, 14)

    def test_plain_syllables_alone_give_no_signal(self):
        self.assertFalse(looks_vietnamese(["an", "ba", "cho"]))
        self.assertFalse(looks_vietnamese(["học"]))
        self.assertTrue(looks_vietnamese(["tôi", "đi", "học", "ở", "trường"]))

    def test_numbers_are_not_words(self):
        c = analyse("Năm 2026 có 365 ngày và 12 tháng")
        self.assertEqual(c.numbers, 3)
        self.assertEqual(c.latin_tokens, 5)

    def test_korean_words_and_syllables(self):
        c = analyse("안녕하세요 세계 hello")
        self.assertEqual((c.hangul_syllables, c.hangul_words, c.latin_tokens), (7, 2, 1))

    def test_chinese_and_japanese_without_spaces(self):
        c = analyse("我喜欢编程。こんにちは世界。")
        self.assertEqual((c.han, c.kana), (7, 5))

    def test_lines_and_bom(self):
        self.assertEqual(analyse("a\nb\nc").lines, 3)
        self.assertEqual(analyse("a\nb\n").lines, 2)
        self.assertEqual(analyse("").lines, 0)
        self.assertEqual(normalise("﻿xin chào"), "xin chào")

    def test_top_is_deterministic_and_case_folded(self):
        c = analyse("Học học HỌC sinh sinh viên", top=2)
        self.assertEqual(c.top, (("học", 3), ("sinh", 2)))

    def test_empty_and_symbols_only(self):
        c = analyse("   \n\t ")
        self.assertEqual((c.characters, c.latin_tokens, c.han), (0, 0, 0))
        self.assertEqual(analyse("😀😀").latin_tokens, 0)


class TestSegmentation(unittest.TestCase):
    LEX = load_lexicon("sinh viên\nviệt nam\nlập trình\nhồ chí minh\nchí\nthành phố hồ chí minh\n")

    def test_lexicon_loading(self):
        entries, longest = load_lexicon("# comment\n\nSinh Viên\nxin chào\n")
        self.assertEqual(entries, frozenset({("sinh", "viên"), ("xin", "chào")}))
        self.assertEqual(longest, 2)

    def test_segments_rebuild_the_input(self):
        rng = random.Random(4)
        for _ in range(200):
            syl = [rng.choice(["sinh", "viên", "việt", "nam", "lập", "trình", "hồ", "chí", "minh", "thành", "phố", "học"]) for _ in range(rng.randint(1, 14))]
            parts = segment(syl, *self.LEX)
            self.assertEqual([s for p in parts for s in p], syl)
            for p in parts:
                self.assertTrue(len(p) == 1 or p in self.LEX[0])

    def test_always_takes_the_longest_word_available(self):
        rng = random.Random(5)
        entries, longest = self.LEX
        for _ in range(200):
            syl = [rng.choice(["sinh", "viên", "hồ", "chí", "minh", "thành", "phố", "học"]) for _ in range(rng.randint(1, 10))]
            i = 0
            for p in segment(syl, entries, longest):
                for n in range(len(p) + 1, min(longest, len(syl) - i) + 1):     # nothing longer starting here is in the lexicon
                    self.assertNotIn(tuple(syl[i:i + n]), entries)
                i += len(p)

    def test_a_longer_match_beats_a_shorter_one(self):
        syl = ["thành", "phố", "hồ", "chí", "minh"]
        self.assertEqual(segment(syl, *self.LEX), [("thành", "phố", "hồ", "chí", "minh")])

    def test_no_lexicon_entry_means_no_merging(self):
        syl = ["sinh", "viên"]
        self.assertEqual(segment(syl, frozenset(), 1), [("sinh",), ("viên",)])

    def test_the_result_is_one_of_the_possible_segmentations(self):
        syl = ["sinh", "viên", "việt", "nam"]
        parts = segment(syl, *self.LEX)
        self.assertIn(parts, list(oracles.all_segmentations(syl)))

    def test_words_never_exceed_syllables_and_a_bigger_lexicon_never_adds_words(self):
        text = "Sinh viên Việt Nam học lập trình ở thành phố Hồ Chí Minh\nSinh viên học"
        small = analyse(text, load_lexicon("sinh viên\n"))
        large = analyse(text, load_lexicon("sinh viên\nviệt nam\nlập trình\nhồ chí minh\n"))
        self.assertLessEqual(large.words, small.words)
        self.assertLessEqual(small.words, small.syllables)

    def test_words_are_counted_per_line(self):
        c = analyse("xin\nchào bạn", load_lexicon("xin chào\n"))
        self.assertEqual(c.words, 3)                       # a word does not span a line break

    def test_english_text_gets_no_word_count(self):
        self.assertIsNone(analyse("plain english words here", load_lexicon("sinh viên\n")).words)


class TestLegacy(unittest.TestCase):
    def test_original_function_still_splits_on_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.txt"
            p.write_text("sinh viên Việt Nam học", encoding="utf-8")
            self.assertEqual(word_counter.count_words(str(p)), 5)
            self.assertEqual(analyse(p.read_text(encoding="utf-8")).syllables, 5)


if __name__ == "__main__":
    unittest.main()
