# buoc.dau

**Bước đầu** (*first step*). Count Vietnamese, Chinese, Japanese and Korean text correctly. Dependency free Python 3.10+.

**Bước đầu.** Đếm đúng văn bản tiếng Việt, tiếng Trung, tiếng Nhật và tiếng Hàn. Chỉ dùng thư viện chuẩn của Python.

[![CI](https://github.com/AndMaverick/buoc.dau/actions/workflows/ci.yml/badge.svg)](https://github.com/AndMaverick/buoc.dau/actions/workflows/ci.yml)

This repository began as `myfirst-project`, a sandbox whose first script split a file on spaces and called the pieces words.
That is right for English and wrong for most of Asia. Vietnamese puts a space between every syllable, Chinese and Japanese use none,
and one accented letter can be stored two ways. `buoc.dau` is that first step done properly.

Repo này khởi đầu là `myfirst-project`, nơi script đầu tiên chỉ tách theo dấu cách rồi gọi đó là "từ".
Cách đó đúng với tiếng Anh nhưng sai với tiếng Việt (mỗi dấu cách là một âm tiết), tiếng Trung và tiếng Nhật (không có dấu cách),
và một chữ có dấu có thể được lưu theo hai cách khác nhau.

## Use / Cách dùng

```
python -m buoc_dau examples/mixed.txt --lexicon examples/vi_words.txt --top 3
```

```
examples/mixed.txt
  Lines                                      6
  Characters                               182
  Latin words or syllables                  33
  Numbers                                    2
  Vietnamese syllables                      33
  Vietnamese words (with lexicon)           22
  Han characters                            17
  Kana                                      17
  Hangul syllables                          15
  Hangul words (eojeol)                      4
  Most frequent: chào (1), chí (1), chăm (1)
```

Add `--lang vi` for Vietnamese labels, `--json` for machine output, `-` to read standard input, `--encoding gb18030` for other encodings.
Exit codes: `0` counted, `2` a file could not be read or decoded (nothing is printed to stdout in that case).

Thêm `--lang vi` để hiện nhãn tiếng Việt, `--json` cho đầu ra máy đọc, `-` để đọc từ stdin.

```python
from buoc_dau import analyse, load_lexicon

c = analyse("Sinh viên Việt Nam học lập trình", load_lexicon(open("examples/vi_words.txt", encoding="utf-8").read()))
c.syllables, c.words      # (7, 4)
```

## What it does differently / Điểm khác biệt

| Script | Unit counted | Why |
|---|---|---|
| Vietnamese | syllables (always); words (with a lexicon) | a space separates syllables, not words: "sinh viên" is one word |
| Chinese (Han) | characters | no spaces between words |
| Japanese | Han characters and kana, separately | no spaces; kana and kanji are different questions |
| Korean | Hangul syllables, and eojeol (separated by spaces units) | Korean does use spaces, but around phrases, not single syllables |
| Thai | characters | no spaces between words, and no word segmenter here |

- **NFC first.** `ệ` can be one code point or `e` plus two combining marks. Text is normalised before counting, so both give the same answer.
- **Line breaks end words.** A lexicon word never spans two lines.
- **Words by forward maximum matching.** Given a word list, the longest entry that fits at each position wins. Anything not in the list stays a single syllable.

## Measured / Số liệu đo được

`python examples/evaluate.py` recomputes these from scratch and exits 1 if a check fails. CI runs it.

```
script and character counts vs the Unicode-name oracle: 5000/5000
identical counts for precomposed and decomposed Vietnamese: 5000/5000
6 sentences: whitespace split 49 tokens = 49 syllables, but 30 words by hand
original word_counter.count_words on examples/mixed.txt: 41
word count with the 18-word sample lexicon: 36 vs 30 by hand (error +6)
word count with a lexicon holding the gold multi-syllable words: 30 vs 30 by hand (error +0)
```

The oracle in `tests/oracles.py` reads the Unicode character *names* (`unicodedata.name`), so it shares no tables or code with the library.
The 6 gold sentences were segmented by hand.

## Honest limits / Giới hạn

- **Maximum matching is a baseline, not a state of the art segmenter.** It cannot resolve ambiguity from context. The last line above is a
  ceiling (the lexicon was built from the answers), not an accuracy figure. With the 18-word sample list the count is off by +6 on 30 words,
  because unknown compounds stay split. Bring a real lexicon for real work.
- **The Vietnamese flag is a text level heuristic.** Text is treated as Vietnamese when at least 1 token in 10 carries a specific to Vietnamese
  letter or tone mark (and at least 2 tokens do). English sentences inside a Vietnamese file are therefore counted as syllables too.
  Vietnamese typed without diacritics is not detected.
- **Characters are code points after NFC**, not perceived by the user characters. Emoji sequences and Indic or Thai combining marks count each part.
- **Thai is counted, not segmented.**
- **Hangul words are eojeol**, which are not dictionary words.
- The 6-sentence gold set is small. It shows the effect, it is not a benchmark.

## The original script / Script gốc

`word_counter.py` is kept as it was, plus `encoding='utf-8'` (the default encoding breaks on Vietnamese text on Windows).

## Develop / Phát triển

```
python -m unittest discover -s tests -t . -v
ruff check . && mypy
```

MIT. AndMaverick LLC.
