"""Measured claims for the README. Every number printed here is recomputed from scratch; the script exits 1 if any check fails.

Run:  python examples/evaluate.py
"""
from __future__ import annotations

import random
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import word_counter  # noqa: E402
from buoc_dau import analyse, load_lexicon  # noqa: E402
from tests import oracles  # noqa: E402

VI = ["sinh", "viên", "Việt", "Nam", "học", "lập", "trình", "rất", "chăm", "chỉ", "ở", "thành", "phố", "Hồ", "Chí", "Minh", "đại", "học", "công", "nghệ", "kỹ", "sư", "phần", "mềm", "ngày", "xuân", "mùa", "bạn", "bè", "gia", "đình"]
HAN = [chr(c) for c in (0x4E2D, 0x6587, 0x7F16, 0x7A0B, 0x3400, 0x4DBF, 0x20000, 0xF900, 0x9FFF)]
KANA = [chr(c) for c in (0x3042, 0x30A2, 0x3093, 0x30F3, 0x30FC, 0x31F0, 0xFF76)]
HANGUL = [chr(c) for c in (0xAC00, 0xD55C, 0xAE00, 0xD7A3)]
THAI = [chr(c) for c in (0x0E01, 0x0E2D, 0x0E31, 0x0E48, 0x0E50)]
OTHER = ["😀", "。", "!", "\t", "42", "3.14", "é", "ß"]

# Hand-segmented Vietnamese, one sentence per row: the gold standard for the word-count check.
GOLD = [
    ("Sinh viên Việt Nam học lập trình", ["Sinh viên", "Việt Nam", "học", "lập trình"]),
    ("Kỹ sư phần mềm làm việc ở thành phố Hồ Chí Minh", ["Kỹ sư", "phần mềm", "làm việc", "ở", "thành phố", "Hồ Chí Minh"]),
    ("Tôi rất thích học công nghệ", ["Tôi", "rất", "thích", "học", "công nghệ"]),
    ("Gia đình tôi ở Hà Nội", ["Gia đình", "tôi", "ở", "Hà Nội"]),
    ("Bạn bè đến thăm vào mùa xuân", ["Bạn bè", "đến", "thăm", "vào", "mùa xuân"]),
    ("Đại học tổ chức hội nghị về trí tuệ nhân tạo", ["Đại học", "tổ chức", "hội nghị", "về", "trí tuệ", "nhân tạo"]),
]


def random_text(rng: random.Random, n: int = 60) -> str:
    parts = []
    for _ in range(n):
        parts.append(rng.choice(rng.choice([VI, HAN, KANA, HANGUL, THAI, OTHER])))
        parts.append(rng.choice([" ", "", "\n", " "]))
    return "".join(parts)


def main() -> int:
    ok = True
    rng = random.Random(2026)

    n = 5000
    agree = 0
    for _ in range(n):
        t = random_text(rng)
        c = analyse(t)
        agree += (c.han, c.kana, c.hangul_syllables, c.thai_characters, c.characters) == (
            oracles.han(t), oracles.kana(t), oracles.hangul(t), oracles.thai(t), oracles.visible(t))
    print(f"script and character counts vs the Unicode-name oracle: {agree}/{n}")
    ok &= agree == n

    same = 0
    for _ in range(n):
        t = " ".join(rng.choice(VI) for _ in range(rng.randint(3, 30)))
        same += analyse(t) == analyse(unicodedata.normalize("NFD", t))
    print(f"identical counts for precomposed and decomposed Vietnamese: {same}/{n}")
    ok &= same == n

    # The point of the library, in one number: what a whitespace split says about Vietnamese.
    tokens = syll = 0
    for s, _ in GOLD:
        tokens += len(s.split())
        syll += analyse(s).syllables or 0
    gold_words = sum(len(w) for _, w in GOLD)
    print(f"6 sentences: whitespace split {tokens} tokens = {syll} syllables, but {gold_words} words by hand")
    ok &= tokens == syll
    print(f"original word_counter.count_words on examples/mixed.txt: {word_counter.count_words(str(ROOT / 'examples' / 'mixed.txt'))}")

    # Word segmentation: forward maximum matching against two lexicons, scored on the gold standard.
    def words_of(lex_text: str) -> tuple[int, int, int]:
        lex = load_lexicon(lex_text)
        right = pred = 0
        for s, gold in GOLD:
            got = analyse(s, lex).words or 0
            pred += got
            right += min(got, len(gold))
        return pred, gold_words, right

    sample = (ROOT / "examples" / "vi_words.txt").read_text(encoding="utf-8")
    full = "\n".join(w for _, ws in GOLD for w in ws if " " in w)
    for name, lex in (("the 18-word sample lexicon", sample), ("a lexicon holding the gold multi-syllable words", full)):
        pred, gold, _ = words_of(lex)
        print(f"word count with {name}: {pred} vs {gold} by hand (error {pred - gold:+d})")
    pred_full, gold, _ = words_of(full)
    ok &= pred_full == gold

    print("pass" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
