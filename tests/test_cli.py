import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

from buoc_dau import analyse
from buoc_dau.cli import main

ROOT = Path(__file__).resolve().parent.parent
EM = chr(0x2014)
TEXT = "Tôi là sinh viên Việt Nam. 我喜欢编程。こんにちは。안녕하세요 세계. 2026\n"


def run(*argv, stdin=None):
    out, err = io.StringIO(), io.StringIO()
    old = sys.stdin
    if stdin is not None:
        sys.stdin = io.TextIOWrapper(io.BytesIO(stdin), encoding="utf-8")
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main(list(argv))
            except SystemExit as e:
                code = int(e.code or 0)
    finally:
        sys.stdin = old
    return code, out.getvalue(), err.getvalue()


class TestCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write(self, name, data):
        p = self.dir / name
        p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return str(p)

    def test_json_matches_the_library(self):
        f = self.write("a.txt", TEXT)
        code, out, _ = run(f, "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[f], analyse(TEXT).to_dict())

    def test_text_output_has_the_counts_in_english_and_vietnamese(self):
        f = self.write("a.txt", TEXT)
        c = analyse(TEXT)
        _, en, _ = run(f, "--lang", "en")
        _, vi, _ = run(f, "--lang", "vi")
        self.assertIn("Vietnamese syllables", en)
        self.assertIn("Âm tiết tiếng Việt", vi)
        self.assertIn("Chữ Hán", vi)
        self.assertRegex(en, rf"Han characters\s+{c.han}\n")

    def test_stdin_dash(self):
        code, out, _ = run("-", "--json", stdin=TEXT.encode("utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["-"]["han"], analyse(TEXT).han)

    def test_bom_is_ignored(self):
        f = self.write("bom.txt", b"\xef\xbb\xbf" + TEXT.encode("utf-8"))
        _, out, _ = run(f, "--json")
        self.assertEqual(json.loads(out)[f], analyse(TEXT).to_dict())

    def test_decomposed_file_gives_the_same_counts(self):
        a = self.write("nfc.txt", unicodedata.normalize("NFC", TEXT))
        b = self.write("nfd.txt", unicodedata.normalize("NFD", TEXT))
        ra, rb = json.loads(run(a, "--json")[1])[a], json.loads(run(b, "--json")[1])[b]
        self.assertEqual(ra, rb)

    def test_missing_file_exits_2(self):
        code, out, err = run(str(self.dir / "nope.txt"))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("cannot read", err)

    def test_bad_utf8_exits_2_and_names_the_byte(self):
        f = self.write("bad.txt", b"xin ch\xe0o")
        code, _, err = run(f)
        self.assertEqual(code, 2)
        self.assertIn("not valid utf-8-sig", err)
        self.assertIn("--encoding", err)

    def test_other_encoding(self):
        f = self.write("gbk.txt", "我喜欢编程".encode("gb18030"))
        code, out, _ = run(f, "--encoding", "gb18030", "--json")
        self.assertEqual((code, json.loads(out)[f]["han"]), (0, 5))

    def test_lexicon_adds_a_word_count_and_a_bad_lexicon_exits_2(self):
        lex = self.write("lex.txt", "sinh viên\nviệt nam\n")
        f = self.write("a.txt", "Tôi là sinh viên Việt Nam")
        code, out, _ = run(f, "--lexicon", lex, "--json")
        self.assertEqual((code, json.loads(out)[f]["words"]), (0, 4))
        self.assertEqual(run(f, "--lexicon", str(self.dir / "none.txt"))[0], 2)

    def test_top(self):
        f = self.write("a.txt", "học học học sinh sinh viên")
        _, out, _ = run(f, "--top", "2")
        self.assertIn("học (3), sinh (2)", out)

    def test_several_files_in_one_run(self):
        a, b = self.write("a.txt", "xin chào"), self.write("b.txt", "你好")
        out = json.loads(run(a, b, "--json")[1])
        self.assertEqual(set(out), {a, b})

    def test_one_bad_file_among_good_ones_still_exits_2_with_no_partial_output(self):
        a = self.write("a.txt", "xin chào")
        code, out, _ = run(a, str(self.dir / "nope.txt"))
        self.assertEqual((code, out), (2, ""))

    def test_no_em_dash_in_any_output(self):
        f = self.write("a.txt", TEXT)
        for args in ([f], [f, "--lang", "vi"], [f, "--json"], ["--help"]):
            out = run(*args)[1]
            self.assertNotIn(EM, out)

    def test_module_entry_point_and_hash_seed_determinism(self):
        f = self.write("a.txt", TEXT * 3 + "học sinh học")
        outs = set()
        for seed in ("0", "1", "12345"):
            env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT))
            r = subprocess.run([sys.executable, "-m", "buoc_dau", f, "--json", "--top", "5"], capture_output=True, env=env, cwd=ROOT, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.add(r.stdout)
        self.assertEqual(len(outs), 1)


class TestRepository(unittest.TestCase):
    def test_no_em_dash_anywhere_in_the_repository(self):
        kinds = {".py", ".md", ".txt", ".toml", ".yml"}
        files = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix in kinds and ".git" not in p.parts and "__pycache__" not in p.parts]
        bad = [str(p.relative_to(ROOT)) for p in files if EM in p.read_text(encoding="utf-8")]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
