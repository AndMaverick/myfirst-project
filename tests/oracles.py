"""Independent counting from the Unicode character names, which share no code or tables with buoc_dau."""
from __future__ import annotations

import unicodedata


def _name(c: str) -> str:
    return unicodedata.name(c, "")


def han(text: str) -> int:
    return sum(_name(c).startswith(("CJK UNIFIED IDEOGRAPH", "CJK COMPATIBILITY IDEOGRAPH")) for c in text)


def kana(text: str) -> int:
    return sum(_name(c).startswith(("HIRAGANA", "KATAKANA", "HALFWIDTH KATAKANA")) for c in text)


def hangul(text: str) -> int:
    return sum(_name(c).startswith("HANGUL SYLLABLE") for c in text)


def thai(text: str) -> int:
    return sum(_name(c).startswith(("THAI CHARACTER", "THAI DIGIT")) for c in text)


def visible(text: str) -> int:
    t = unicodedata.normalize("NFC", text)
    return sum(1 for c in t if not c.isspace() and unicodedata.category(c)[0] != "C")


def all_segmentations(syllables: list[str]):
    """Every way to cut a syllable list into consecutive pieces (for tiny inputs)."""
    if not syllables:
        yield []
        return
    for i in range(1, len(syllables) + 1):
        for rest in all_segmentations(syllables[i:]):
            yield [tuple(syllables[:i])] + rest
