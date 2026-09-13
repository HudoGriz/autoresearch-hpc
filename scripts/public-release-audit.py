#!/usr/bin/env python3
"""Audit a repository before a public release.

The default scan checks the current tracked tree. ``--history`` additionally
scans commit messages, author metadata and historical text blobs. The history
mode is intentionally stricter and is expected to fail until any sensitive
history has been rewritten.

This is a lightweight publication-safety check, not a replacement for a full
secret scanner such as Gitleaks/TruffleHog. Findings that may themselves contain
credentials, session identifiers, private addresses or personal email are
redacted in terminal and JSON output.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


TEXT_EXTENSIONS = {
    "", ".md", ".txt", ".py", ".sh", ".bash", ".zsh", ".yml", ".yaml",
    ".json", ".toml", ".ini", ".cfg", ".conf", ".cff", ".nf", ".groovy",
    ".tsv", ".csv", ".xml", ".html", ".rst", ".lock",
}
SELF_PATH = "scripts/public-release-audit.py"

# Patterns that should never be committed to a public source release.
ERROR_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("OpenAI-style secret", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b")),
    ("Anthropic secret", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b")),
    ("Claude session URL", re.compile(r"https://claude\.ai/code/session_[A-Za-z0-9_-]+")),
)

# Known project-specific material that should not ship in the public tree. These
# are warnings so the script can be introduced before the final history rewrite;
# release candidates should use --fail-on-warnings.
WARNING_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
)

PRIVATE_IP = re.compile(
    r"(?<!\d)(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
    r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(?!\d)"
)

REDACT_KINDS = {
    "private key",
    "GitHub token",
    "AWS access key",
    "OpenAI-style secret",
    "Anthropic secret",
    "Slack token",
    "Claude session URL",
    "private-network address",
    "public author email",
    "public committer email",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    kind: str
    location: str
    excerpt: str


def run_git(*args: str, text: bool = True) -> str | bytes:
    proc = subprocess.run(
        ["git", *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=text,
    )
    return proc.stdout


def repo_root() -> Path:
    try:
        return Path(str(run_git("rev-parse", "--show-toplevel")).strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise SystemExit("error: run this inside a Git working tree")


def safe_excerpt(text: str, start: int, width: int = 100) -> str:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end].strip()
    if len(line) > width:
        line = line[: width - 1] + "…"
    return line


def finding_excerpt(kind: str, text: str, start: int) -> str:
    if kind in REDACT_KINDS:
        return "<redacted; inspect the named source locally>"
    return safe_excerpt(text, start)


def scan_text(text: str, location: str) -> list[Finding]:
    findings: list[Finding] = []
    for kind, pattern in ERROR_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(Finding("error", kind, location, finding_excerpt(kind, text, match.start())))
    for kind, pattern in WARNING_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(Finding("warning", kind, location, finding_excerpt(kind, text, match.start())))
    for match in PRIVATE_IP.finditer(text):
        kind = "private-network address"
        findings.append(Finding("warning", kind, location, finding_excerpt(kind, text, match.start())))
    return findings


def tracked_files(root: Path) -> Iterable[Path]:
    raw = run_git("ls-files", "-z", text=False)
    assert isinstance(raw, bytes)
    for item in raw.split(b"\0"):
        if not item:
            continue
        path = root / os.fsdecode(item)
        if path.is_file() or path.is_symlink():
            yield path


def read_text_file(path: Path, max_bytes: int) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > max_bytes or b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_tree(root: Path, max_bytes: int) -> list[Finding]:
    findings: list[Finding] = []
    for path in tracked_files(root):
        rel = path.relative_to(root).as_posix()
        # The scanner necessarily contains the signatures it searches for.
        if rel == SELF_PATH:
            continue
        text = read_text_file(path, max_bytes)
        if text is None:
            continue
        findings.extend(scan_text(text, rel))
    return findings


def commit_history_findings() -> list[Finding]:
    findings: list[Finding] = []
    fmt = "%H%x00%an%x00%ae%x00%cn%x00%ce%x00%B%x1e"
    raw = str(run_git("log", "--all", f"--format={fmt}"))
    for record in raw.split("\x1e"):
        if not record.strip():
            continue
        parts = record.strip("\n\x00").split("\x00", 5)
        if len(parts) != 6:
            continue
        sha, _author_name, author_email, _committer_name, committer_email, message = parts
        loc = f"commit {sha[:12]}"
        findings.extend(scan_text(message, f"{loc} message"))
        for role, email in (("author", author_email), ("committer", committer_email)):
            if email and "@users.noreply.github.com" not in email and email != "noreply@github.com":
                findings.append(
                    Finding(
                        "warning",
                        f"public {role} email",
                        loc,
                        "<redacted email; inspect commit metadata locally>",
                    )
                )
    return findings


def historical_blob_findings(max_bytes: int) -> list[Finding]:
    findings: list[Finding] = []
    raw = str(run_git("rev-list", "--objects", "--all"))
    seen: set[str] = set()
    for line in raw.splitlines():
        if not line.strip():
            continue
        fields = line.split(" ", 1)
        sha = fields[0]
        path = fields[1] if len(fields) == 2 else ""
        if sha in seen:
            continue
        seen.add(sha)
        if path == SELF_PATH:
            continue
        suffix = Path(path).suffix.lower()
        if suffix not in TEXT_EXTENSIONS:
            continue
        try:
            size = int(str(run_git("cat-file", "-s", sha)).strip())
            typ = str(run_git("cat-file", "-t", sha)).strip()
        except subprocess.CalledProcessError:
            continue
        if typ != "blob" or size > max_bytes:
            continue
        try:
            data = run_git("cat-file", "blob", sha, text=False)
            assert isinstance(data, bytes)
            if b"\0" in data[:8192]:
                continue
            text = data.decode("utf-8")
        except (UnicodeDecodeError, subprocess.CalledProcessError):
            continue
        findings.extend(scan_text(text, f"historical blob {sha[:12]} {path}".strip()))
    return findings


def deduplicate(findings: Iterable[Finding]) -> list[Finding]:
    unique: dict[tuple[str, str, str, str], Finding] = {}
    for finding in findings:
        key = (finding.severity, finding.kind, finding.location, finding.excerpt)
        unique[key] = finding
    return sorted(unique.values(), key=lambda f: (f.severity, f.kind, f.location, f.excerpt))


def print_report(findings: list[Finding]) -> None:
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    if not findings:
        print("public-release audit: no findings")
        return
    print(f"public-release audit: {len(errors)} error(s), {len(warnings)} warning(s)")
    for f in findings:
        print(f"[{f.severity.upper():7}] {f.kind}: {f.location}")
        print(f"          {f.excerpt}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", action="store_true", help="scan the current tracked tree (default)")
    parser.add_argument("--history", action="store_true", help="also scan commit metadata/messages and historical text blobs")
    parser.add_argument("--fail-on-warnings", action="store_true", help="treat warnings as release-blocking")
    parser.add_argument("--json", metavar="PATH", help="write machine-readable findings")
    parser.add_argument("--max-bytes", type=int, default=1_000_000, help="maximum text blob size to inspect")
    args = parser.parse_args()

    root = repo_root()
    findings = scan_tree(root, args.max_bytes)
    if args.history:
        findings.extend(commit_history_findings())
        findings.extend(historical_blob_findings(args.max_bytes))
    findings = deduplicate(findings)
    print_report(findings)

    if args.json:
        payload = {
            "scope": "history" if args.history else "tree",
            "errors": sum(f.severity == "error" for f in findings),
            "warnings": sum(f.severity == "warning" for f in findings),
            "findings": [asdict(f) for f in findings],
        }
        Path(args.json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    has_error = any(f.severity == "error" for f in findings)
    has_warning = any(f.severity == "warning" for f in findings)
    if has_error or (args.fail_on_warnings and has_warning):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
