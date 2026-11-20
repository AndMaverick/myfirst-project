"""Count text the way people write it in Asian languages.

Splitting on spaces is right for English and wrong almost everywhere else:

- Vietnamese puts a space between every syllable, so "sinh viên" (student) is one word and two syllables. Without a lexicon the honest
  count is syllables; with one, words are found by forward maximum matching.
- Chinese and Japanese have no spaces. Each Han character is counted, and kana separately.
- Korean separates eojeol (word units) with spaces, and each Hangul block is a syllable.
- Vietnamese text arrives either precomposed (NFC) or with separate combining marks (NFD). Text is normalised to NFC first, so both
  forms give the same answer.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Unicode blocks, written as code point ranges.
HAN = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF), (0x20000, 0x2A6DF), (0x2A700, 0x2EBEF), (0x30000, 0x323AF))
KANA = ((0x3040, 0x309F), (0x30A0, 0x30FF), (0x31F0, 0x31FF), (0xFF66, 0xFF9F))
HANGUL = ((0xAC00, 0xD7A3),)
THAI = ((0x0E01, 0x0E3A), (0x0E40, 0x0E5B))
VI_LETTERS = frozenset("ăâđêôơư")
_LATIN_WORD = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*")


def _in(cp: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(lo <= cp <= hi for lo, hi in ranges)


def _is_vi_mark(ch: str) -> bool:
    """True for a Vietnamese-specific letter (ă â đ ê ô ơ ư) or a plain vowel carrying a tone mark."""
    base = ch.casefold()
    if base in VI_LETTERS:
        return True
    decomposed = unicodedata.normalize("NFD", base)
    return len(decomposed) > 1 and decomposed[0] in "aeiouy" and any(c in decomposed[1:] for c in "̣̀́̃̉")


@dataclass(frozen=True)
class Counts:
    lines: int
    characters: int                  # visible code points after NFC: not spaces, not controls
    latin_tokens: int                # words and syllables written with Latin letters
    numbers: int
    han: int
    kana: int
    hangul_syllables: int
    hangul_words: int                # eojeol: space-separated runs that contain Hangul
    thai_characters: int
    vietnamese: bool                 # the text looks Vietnamese, so Latin tokens are syllables
    syllables: int | None            # Vietnamese syllables (Latin tokens) when the text looks Vietnamese
    words: int | None = None         # Vietnamese words, only with a lexicon
    top: tuple[tuple[str, int], ...] = field(default=())

    def to_dict(self) -> dict[str, object]:
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in self.__dict__.items()}


def normalise(text: str) -> str:
    return unicodedata.normalize("NFC", text.lstrip("﻿"))


def looks_vietnamese(tokens: list[str]) -> bool:
    """At least one token in ten carries a Vietnamese-specific letter or tone mark. Plain words such as "an" or "ba" give no signal alone."""
    if len(tokens) < 3:
        return False
    marked = sum(any(_is_vi_mark(c) for c in t) for t in tokens)
    return marked * 10 >= len(tokens) and marked >= 2


def load_lexicon(text: str) -> tuple[frozenset[tuple[str, ...]], int]:
    """Words of one or more syllables, one per line (blank lines and lines starting with # ignored)."""
    entries = set()
    longest = 1
    for raw in text.splitlines():
        line = normalise(raw).strip()
        if not line or line.startswith("#"):
            continue
        syl = tuple(s.casefold() for s in line.split())
        entries.add(syl)
        longest = max(longest, len(syl))
    return frozenset(entries), longest


def segment(syllables: list[str], lexicon: frozenset[tuple[str, ...]], longest: int) -> list[tuple[str, ...]]:
    """Forward maximum matching: at each position take the longest lexicon word, else the single syllable."""
    out: list[tuple[str, ...]] = []
    i = 0
    while i < len(syllables):
        for n in range(min(longest, len(syllables) - i), 0, -1):
            cand = tuple(s.casefold() for s in syllables[i:i + n])
            if n == 1 or cand in lexicon:
                out.append(cand)
                i += n
                break
    return out


def analyse(text: str, lexicon: tuple[frozenset[tuple[str, ...]], int] | None = None, top: int = 0) -> Counts:
    text = normalise(text)
    lines = len(text.splitlines())
    chars = han = kana = hangul = thai = 0
    for ch in text:
        if ch.isspace() or unicodedata.category(ch).startswith("C"):
            continue
        chars += 1
        cp = ord(ch)
        han += _in(cp, HAN)
        kana += _in(cp, KANA)
        hangul += _in(cp, HANGUL)
        thai += _in(cp, THAI)
    tokens = [t for t in _LATIN_WORD.findall(text) if all(_latin_or_digit(c) for c in t)]
    numbers = sum(t.isdigit() for t in tokens)
    latin = [t for t in tokens if not t.isdigit()]
    hangul_words = sum(any(_in(ord(c), HANGUL) for c in w) for w in text.split())
    vi = looks_vietnamese(latin)
    words = None
    if vi and lexicon is not None:
        words = 0
        for line in text.splitlines():
            run = [t for t in _LATIN_WORD.findall(line) if all(_latin_or_digit(c) for c in t) and not t.isdigit()]
            words += len(segment(run, *lexicon))
    ranked: tuple[tuple[str, int], ...] = ()
    if top:
        freq: dict[str, int] = {}
        for t in latin:
            freq[t.casefold()] = freq.get(t.casefold(), 0) + 1
        ranked = tuple(sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:top])
    return Counts(lines, chars, len(latin), numbers, han, kana, hangul, hangul_words, thai, vi, len(latin) if vi else None, words, ranked)


def _latin_or_digit(c: str) -> bool:
    if c in "'’-":
        return True
    if c.isdigit():
        return True
    return unicodedata.name(c, "").startswith(("LATIN", "COMBINING"))
