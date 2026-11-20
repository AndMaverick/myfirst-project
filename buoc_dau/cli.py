"""python -m buoc_dau FILE... : count text in Vietnamese, Chinese, Japanese, Korean and Latin scripts.

Exit codes: 0 counted, 2 a file could not be read or decoded.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import counter
from ._version import __version__

LABELS = {
    "en": {"lines": "Lines", "characters": "Characters", "latin_tokens": "Latin words or syllables", "numbers": "Numbers", "han": "Han characters",
           "kana": "Kana", "hangul_syllables": "Hangul syllables", "hangul_words": "Hangul words (eojeol)", "thai_characters": "Thai characters",
           "syllables": "Vietnamese syllables", "words": "Vietnamese words (with lexicon)", "top": "Most frequent"},
    "vi": {"lines": "Dòng", "characters": "Ký tự", "latin_tokens": "Từ hoặc âm tiết (chữ Latin)", "numbers": "Số", "han": "Chữ Hán",
           "kana": "Kana", "hangul_syllables": "Âm tiết Hangul", "hangul_words": "Từ Hangul (eojeol)", "thai_characters": "Ký tự Thái",
           "syllables": "Âm tiết tiếng Việt", "words": "Từ tiếng Việt (có từ điển)", "top": "Phổ biến nhất"},
}


class CountError(ValueError):
    pass


def read(path: str, encoding: str) -> str:
    try:
        raw = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    except OSError as e:
        raise CountError(f"cannot read {path}: {e.strerror or e}") from None
    try:
        return raw.decode(encoding)
    except UnicodeDecodeError as e:
        raise CountError(f"{path} is not valid {encoding} (byte {e.start}); pass --encoding for another one") from None


def render(name: str, c: counter.Counts, lang: str) -> str:
    lab = LABELS[lang]
    rows: list[tuple[str, int | None]] = [("lines", c.lines), ("characters", c.characters), ("latin_tokens", c.latin_tokens), ("numbers", c.numbers)]
    if c.vietnamese:
        rows.append(("syllables", c.syllables))
        if c.words is not None:
            rows.append(("words", c.words))
    rows += [("han", c.han), ("kana", c.kana), ("hangul_syllables", c.hangul_syllables), ("hangul_words", c.hangul_words), ("thai_characters", c.thai_characters)]
    out = [name] + [f"  {lab[k]:<34}{v:>10,}" for k, v in rows if v]
    if c.top:
        out.append(f"  {lab['top']}: " + ", ".join(f"{w} ({n})" for w, n in c.top))
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="buoc-dau", description="Count text in Vietnamese, Chinese, Japanese, Korean and Latin scripts.")
    p.add_argument("files", nargs="+", help="text files, or - for standard input")
    p.add_argument("--version", action="version", version=f"buoc.dau {__version__}")
    p.add_argument("--json", action="store_true")
    p.add_argument("--lexicon", help="Vietnamese word list, one word per line, for word counts")
    p.add_argument("--top", type=int, default=0, help="also list the N most frequent words")
    p.add_argument("--encoding", default="utf-8-sig")
    p.add_argument("--lang", choices=["en", "vi"], default="vi" if os.environ.get("LANG", "").startswith("vi") else "en")
    args = p.parse_args(argv)
    try:
        lex = counter.load_lexicon(read(args.lexicon, args.encoding)) if args.lexicon else None
        results = {f: counter.analyse(read(f, args.encoding), lex, args.top) for f in args.files}
    except CountError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({f: c.to_dict() for f, c in results.items()}, ensure_ascii=False, indent=1, sort_keys=True))
    else:
        for f, c in results.items():
            sys.stdout.write(render(f, c, args.lang))
    return 0
