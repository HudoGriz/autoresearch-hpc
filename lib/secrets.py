"""Refuse to send text that looks like a credential to an external model service (stdlib only).

`arh ask`, `arh delegate` and `arh evoke` send a pre-declaration, a report or a task to a provider.
A credential pasted into any of them leaves the site with it, and a provider may log or retain the
request. A 2026 measurement of agents on a production cluster counted 127 exposed API keys in three
weeks. The patterns are high-precision token shapes; a false positive is cleared by removing the
text or, for a project that has a reason, with `secret_scan = off` in harnesses.md.

  secrets.py scan FILE...     one line per finding (file:line: kind: redacted match); exit 1 if any
"""
import re
import sys

PATTERNS = (
    ('private key', re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----')),
    ('AWS access key', re.compile(r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b')),
    ('GitHub token', re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b')),
    ('Anthropic API key', re.compile(r'\bsk-ant-[A-Za-z0-9_\-]{20,}')),
    ('OpenAI-style API key', re.compile(r'\bsk-(?!ant-)(?:proj-|svcacct-)?[A-Za-z0-9_\-]{32,}')),
    ('Google API key', re.compile(r'\bAIza[0-9A-Za-z_\-]{35}\b')),
    ('Slack token', re.compile(r'\bxox[abposr]-[A-Za-z0-9-]{10,}')),
    ('Hugging Face token', re.compile(r'\bhf_[A-Za-z0-9]{30,}\b')),
    ('JSON web token', re.compile(r'\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}')),
    ('assigned secret', re.compile(r'(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)'
                                   r'\b["\']?\s*[:=]\s*["\'][^"\'\s]{12,}["\']')),
)


def redact(text):
    return text[:6] + '…' + f'({len(text)} chars)'


def scan(path):
    found = []
    try:
        lines = open(path, errors='replace').read().splitlines()
    except OSError:
        return found
    for number, line in enumerate(lines, 1):
        for kind, pattern in PATTERNS:
            match = pattern.search(line)
            if match:
                found.append(f'{path}:{number}: {kind}: {redact(match.group(0))}')
                break
    return found


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'scan':
        sys.exit(__doc__)
    hits = [hit for path in sys.argv[2:] for hit in scan(path)]
    print('\n'.join(hits))
    sys.exit(1 if hits else 0)
