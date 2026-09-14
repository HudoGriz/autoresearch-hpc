#!/usr/bin/env python3
"""Tests for scripts/public-release-audit.py.

The important invariant is not merely finding a secret-like value: the audit
must not echo the matched value into CI logs or JSON output.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "scripts/public-release-audit.py"


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, check=check, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )


class PublicReleaseAuditTests(unittest.TestCase):
    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory(prefix="arh-audit-test-")
        root = Path(temp.name)
        run("git", "init", "-q", cwd=root)
        run("git", "config", "user.name", "Audit Test", cwd=root)
        run("git", "config", "user.email", "audit@example.invalid", cwd=root)
        return temp, root

    def test_secret_is_detected_but_redacted(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        # Construct the signature so this repository does not itself contain a
        # token-shaped literal that its own audit would match.
        secret = "gh" + "p_" + ("A" * 30)
        (root / "config.txt").write_text(f"token={secret}\n", encoding="utf-8")
        run("git", "add", "config.txt", cwd=root)
        out_json = root / "audit.json"
        proc = run(
            "python3", str(AUDIT), "--tree", "--json", str(out_json),
            cwd=root, check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("GitHub token", proc.stdout)
        self.assertNotIn(secret, proc.stdout)
        payload_text = out_json.read_text(encoding="utf-8")
        self.assertNotIn(secret, payload_text)
        payload = json.loads(payload_text)
        self.assertEqual(payload["errors"], 1)
        self.assertEqual(payload["findings"][0]["excerpt"], "<redacted; inspect the named source locally>")

    def test_history_email_is_warning_and_redacted(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        personal = "person@example.invalid"
        run("git", "config", "user.email", personal, cwd=root)
        (root / "README.md").write_text("safe\n", encoding="utf-8")
        run("git", "add", "README.md", cwd=root)
        run("git", "commit", "-q", "-m", "safe commit", cwd=root)
        proc = run("python3", str(AUDIT), "--history", cwd=root, check=False)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("public author email", proc.stdout)
        self.assertNotIn(personal, proc.stdout)

    def test_fail_on_warnings_is_release_blocking(self) -> None:
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        marker = "synthetic " + "private " + "marker"
        (root / ".release-audit-markers").write_text(
            f"private-study fixture\t{marker}\n", encoding="utf-8",
        )
        (root / "notes.md").write_text(marker + "\n", encoding="utf-8")
        run("git", "add", "notes.md", cwd=root)
        proc = run(
            "python3", str(AUDIT), "--tree", "--fail-on-warnings",
            cwd=root, check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("private-study fixture", proc.stdout)


if __name__ == "__main__":
    unittest.main()
