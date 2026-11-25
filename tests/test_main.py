"""Tests for main.py — Weirdest Job Title entry.

Covers the gate (1-60 characters, UTF-8, not whitespace-only), the output
contract (exact bytes, no trailing newline, deterministic), and the edge
cases from Fase 2: missing/unset output dir, pre-existing file, trailing
slash, output path as a file, unwritable directory, multibyte counting.
"""

import importlib.util
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent


def load_main():
    spec = importlib.util.spec_from_file_location("entry_main", REPO / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


main = load_main()


class TestTitle(unittest.TestCase):
    def test_title_is_the_chosen_one(self):
        self.assertEqual(main.TITLE, "Coffin Parking Attendant")

    def test_title_length_within_gate(self):
        self.assertGreaterEqual(len(main.TITLE), 1)
        self.assertLessEqual(len(main.TITLE), 60)

    def test_validate_accepts_title(self):
        main.validate(main.TITLE)  # must not raise

    def test_validate_rejects_empty(self):
        with self.assertRaises(ValueError):
            main.validate("")

    def test_validate_rejects_whitespace_only(self):
        with self.assertRaises(ValueError):
            main.validate("     ")

    def test_validate_rejects_too_long(self):
        with self.assertRaises(ValueError):
            main.validate("x" * 61)

    def test_validate_accepts_exactly_60(self):
        main.validate("x" * 60)

    def test_validate_rejects_leading_trailing_space(self):
        with self.assertRaises(ValueError):
            main.validate(" Coffin Parking Attendant")
        with self.assertRaises(ValueError):
            main.validate("Coffin Parking Attendant ")

    def test_validate_counts_characters_not_bytes(self):
        # 60 multibyte characters are legal; 61 are not.
        main.validate("é" * 60)
        with self.assertRaises(ValueError):
            main.validate("é" * 61)


class TestOutputDir(unittest.TestCase):
    def test_env_var_used(self):
        with mock.patch.dict(os.environ, {"MAKEFUN_OUTPUT_DIR": "/tmp/out"}):
            self.assertEqual(main.output_dir(), "/tmp/out")

    def test_env_var_trailing_slash_stripped(self):
        with mock.patch.dict(os.environ, {"MAKEFUN_OUTPUT_DIR": "/tmp/out/"}):
            self.assertEqual(main.output_dir(), "/tmp/out")

    def test_unset_env_falls_back_to_output(self):
        env = {k: v for k, v in os.environ.items() if k != "MAKEFUN_OUTPUT_DIR"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(main.output_dir(), "/output")

    def test_empty_env_falls_back_to_output(self):
        with mock.patch.dict(os.environ, {"MAKEFUN_OUTPUT_DIR": ""}):
            self.assertEqual(main.output_dir(), "/output")


class TestWriteEntry(unittest.TestCase):
    def test_writes_exact_bytes_no_trailing_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = main.write_entry(main.TITLE, tmp)
            raw = Path(path).read_bytes()
            self.assertEqual(raw, b"Coffin Parking Attendant")
            self.assertEqual(len(raw), 24)

    def test_deterministic_repeated_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(main.write_entry(main.TITLE, tmp)).read_bytes()
            second = Path(main.write_entry(main.TITLE, tmp)).read_bytes()
            self.assertEqual(first, second)

    def test_creates_missing_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            nested = os.path.join(tmp, "a", "b")
            self.assertFalse(os.path.exists(nested))
            main.write_entry(main.TITLE, nested)
            self.assertEqual(
                Path(nested, "entry.txt").read_text(encoding="utf-8"),
                main.TITLE,
            )

    def test_overwrites_pre_existing_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "entry.txt").write_text("junk junk junk", encoding="utf-8")
            main.write_entry(main.TITLE, tmp)
            self.assertEqual(
                Path(tmp, "entry.txt").read_text(encoding="utf-8"),
                main.TITLE,
            )

    def test_entry_path_is_a_directory_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.mkdir(os.path.join(tmp, "entry.txt"))
            with self.assertRaises(OSError):
                main.write_entry(main.TITLE, tmp)

    def test_output_dir_is_a_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp, "blocker")
            blocker.write_text("x", encoding="utf-8")
            with self.assertRaises(OSError):
                main.write_entry(main.TITLE, str(blocker))

    def test_unwritable_directory_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("builtins.open", side_effect=PermissionError("denied")):
                with self.assertRaises(OSError):
                    main.write_entry(main.TITLE, tmp)


class TestMainEndToEnd(unittest.TestCase):
    def test_main_returns_zero_and_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"MAKEFUN_OUTPUT_DIR": tmp}):
                self.assertEqual(main.main(), 0)
            self.assertEqual(
                Path(tmp, "entry.txt").read_bytes(),
                b"Coffin Parking Attendant",
            )

    def test_main_returns_one_on_gate_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"MAKEFUN_OUTPUT_DIR": tmp}):
                with mock.patch.object(main, "TITLE", "x" * 61):
                    self.assertEqual(main.main(), 1)

    def test_main_returns_one_on_io_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"MAKEFUN_OUTPUT_DIR": tmp}):
                with mock.patch("builtins.open", side_effect=OSError("boom")):
                    self.assertEqual(main.main(), 1)


if __name__ == "__main__":
    unittest.main()
