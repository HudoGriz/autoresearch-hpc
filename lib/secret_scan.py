"""Refuse to send text that looks like a credential to an external model service (stdlib only).

`arh ask` sends a pre-declaration and a report to a provider, and a dispatched session's log and
brief are kept in the record. A credential in any of them leaves the site with it, and a provider
may log or retain the request. A 2026 measurement of agents on a production cluster counted 127
exposed API keys in three weeks. The scanning is gitleaks's (https://github.com/gitleaks/gitleaks):
its maintained rules plus the shapes in config/gitleaks.toml. Without gitleaks nothing is sent
(exit 2); a project with a reason sets `secret_scan = off` in harnesses.md.

  secret_scan.py scan FILE...     one line per finding (file:line: rule: redacted match); exit 1 if any
  secret_scan.py redact FILE...   replace every finding in place with [REDACTED rule]; print the count
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

CONFIG = Path(__file__).resolve().parent.parent / 'config/gitleaks.toml'


def findings(path):
    """[(line, rule, secret)] that gitleaks finds in PATH ([] with secret_scan = off). Exits 2 when
    gitleaks cannot run."""
    if os.environ.get('ARH_SECRET_SCAN') == 'off':
        return []
    exe = shutil.which('gitleaks')
    if not exe:
        print('arh: the secret scan needs gitleaks on PATH (scripts/setup-tools.sh installs it; '
              'secret_scan = off in harnesses.md turns it off, for a recorded reason)', file=sys.stderr)
        sys.exit(2)
    with tempfile.TemporaryDirectory() as work:
        report = os.path.join(work, 'report.json')
        try:
            subprocess.run([exe, 'dir', str(path), '--config', str(CONFIG), '--no-banner', '--report-format', 'json',
                            '--report-path', report, '--exit-code', '0'], capture_output=True, timeout=120, check=True)
            data = json.load(open(report))
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            print(f'arh: gitleaks failed on {path}: {error}', file=sys.stderr)
            sys.exit(2)
    found = {}
    for f in data or []:                    # one finding per secret; the most specific (arh-*) rule names it
        if f.get('Secret'):
            key = (f.get('StartLine'), f['Secret'])
            found[key] = min(found.get(key, '~'), f.get('RuleID', 'gitleaks'))
    return sorted(((line, rule, secret) for (line, secret), rule in found.items()), key=lambda f: f[0] or 0)


def scanner():
    """What scanned a review request, for its receipt: None with secret_scan = off, else gitleaks's
    version and the rules' digest. A receipt exists only when the scan found nothing."""
    if os.environ.get('ARH_SECRET_SCAN') == 'off' or not shutil.which('gitleaks'):
        return None
    try:
        version = subprocess.run(['gitleaks', 'version'], capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        version = ''
    return dict(tool='gitleaks', version=version or None,
                config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest())


def redact_file(path):
    """Replace every finding in PATH with [REDACTED rule]; return how many were replaced."""
    try:
        text = open(path, errors='replace').read()
    except OSError:
        return 0
    count = 0
    for _, rule, secret in findings(path):
        count += text.count(secret)
        text = text.replace(secret, f'[REDACTED {rule}]')
    if count:
        open(path, 'w').write(text)
    return count


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('scan', 'redact'):
        sys.exit(__doc__)
    if sys.argv[1] == 'redact':
        print(sum(redact_file(path) for path in sys.argv[2:]))
        sys.exit(0)
    hits = [f'{path}:{line}: {rule}: {secret[:6]}…({len(secret)} chars)'
            for path in sys.argv[2:] for line, rule, secret in findings(path)]
    print('\n'.join(hits))
    sys.exit(1 if hits else 0)
