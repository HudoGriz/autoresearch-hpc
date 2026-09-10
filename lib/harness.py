"""Shell-free harness dispatch and hash-bound cross-check records (stdlib only)."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import selectors
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def result_artifacts(directory):
    directory = Path(directory)
    return {str(p.relative_to(directory)): digest(p)
            for p in sorted((directory / 'results').rglob('*')) if p.is_file()}


def valid_records(directory):
    directory = Path(directory)
    valid = []
    for record in sorted(directory.glob('CROSSCHECK_*.md.json')):
        try:
            data = json.loads(record.read_text())
            output = Path(str(record)[:-5])
            report = directory / 'results/report' / (directory.name + '_report.md')
            pf, vf = data['producer_family'], data['verifier_family']
            if (data['exit_code'] == 0 and data['verdict'] in ('SOUND', 'QUALIFIED', 'UNSOUND')
                    and pf not in ('', 'unknown', 'mixed') and vf not in ('', 'unknown', 'mixed')
                    and pf != vf and not data['same_family_override']
                    and data['review_sha256'] == digest(output)
                    and data['report_sha256'] == digest(report)
                    and data['predeclaration_sha256'] == digest(directory / 'README.md')
                    and ('result_artifacts' not in data or data['result_artifacts'] == result_artifacts(directory))):
                valid.append(str(output))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return valid


def budget():
    directory, prompt, command, role, harness, pf, vf, max_input, max_rounds, note, dry = sys.argv[2:]
    if Path(prompt).stat().st_size > int(max_input):
        sys.exit('review input exceeds ask_max_input_bytes; supply a smaller explicit evidence packet')
    for record in valid_records(directory):
        data = json.loads(Path(record + '.json').read_text())
        if (Path(record).name.startswith('CROSSCHECK_' + role + '_' + harness + '_')
                and data.get('command_template') == command
                and data.get('prompt_sha256') == digest(prompt)
                and data['producer_family'] == pf and data['verifier_family'] == vf):
            print(record)
            return
    if dry == '1':
        return
    attempts = len(list(Path(directory).glob('CROSSCHECK_*.md')))
    if attempts >= int(max_rounds):
        sys.exit('review round budget exhausted; leave unresolved work recorded or deliberately revise the budget')
    if attempts and not note.strip():
        sys.exit('a further review requires --note describing the concrete unresolved issue')


def run():
    command, prompt_file, cwd, output, seconds, pf, vf, override, output_limit = sys.argv[2:]
    prompt = Path(prompt_file).read_text()
    values = {'{prompt}': prompt, '{cwd}': cwd}
    argv = [re.sub(r'\{prompt\}|\{cwd\}', lambda match: values[match.group()], arg)
            for arg in shlex.split(command)]
    if not argv:
        raise ValueError('empty harness command')
    timeout = float(seconds)
    if timeout <= 0:
        raise ValueError('ask_timeout must be positive')
    directory = Path(output).parent
    report = directory / 'results/report' / (directory.name + '_report.md')
    reviewed_report = digest(report) if report.exists() else None
    reviewed_predeclaration = digest(directory / 'README.md')
    reviewed_artifacts = result_artifacts(directory)
    started = time.time()
    limit = int(output_limit)
    if limit <= 0:
        raise ValueError('ask_max_output_bytes must be positive')
    sent_input = None if '{prompt}' in command else open(prompt_file, 'rb')
    with open(output, 'ab') as stdout, open(output + '.err', 'wb') as stderr:
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdin=sent_input or subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       start_new_session=True)
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ, (stdout, limit))
            selector.register(process.stderr, selectors.EVENT_READ, (stderr, 16384))
            received = {process.stdout: 0, process.stderr: 0}
            rc = None
            while selector.get_map():
                if time.time() - started >= timeout:
                    rc = 124
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    break
                for key, _ in selector.select(timeout=0.1):
                    chunk = os.read(key.fileobj.fileno(), 4096)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    target, maximum = key.data
                    available = max(0, maximum - received[key.fileobj])
                    target.write(chunk[:available])
                    received[key.fileobj] += len(chunk)
                    if received[key.fileobj] > maximum:
                        rc = 66
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        break
                if rc is not None:
                    break
            selector.close()
            try:
                status = process.wait(timeout=max(0.01, timeout - (time.time() - started)))
            except subprocess.TimeoutExpired:
                rc = 124
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                status = process.wait()
            rc = status if rc is None else rc
            if rc == 66:
                stderr.write(b'\nReview output exceeded its byte limit; response is incomplete.\n')
        finally:
            if sent_input:
                sent_input.close()
    verdicts = re.findall(r'^VERDICT: (SOUND|QUALIFIED|UNSOUND)\s*$', Path(output).read_text(errors="replace"), re.M)
    verdict = verdicts[0] if len(verdicts) == 1 else None
    if not verdict and rc == 0:
        rc = 65
    directory = Path(output).parent
    report = directory / 'results/report' / (directory.name + '_report.md')
    data = dict(exit_code=rc, verdict=verdict, producer_family=pf, verifier_family=vf,
                same_family_override=override == '1', started=started, finished=time.time(),
                command_template=command, cwd=cwd, prompt_sha256=digest(prompt_file),
                review_sha256=digest(output), report_sha256=reviewed_report,
                predeclaration_sha256=reviewed_predeclaration, result_artifacts=reviewed_artifacts)
    with open(output + '.json', 'x') as record:
        json.dump(data, record, indent=2)
        record.write('\n')
    return rc


if __name__ == '__main__':
    if sys.argv[1] == 'budget':
        budget()
    elif sys.argv[1] == 'valid':
        print('\n'.join(valid_records(sys.argv[2])))
    elif sys.argv[1] == 'describe':
        directory = Path(sys.argv[2])
        valid = set(valid_records(directory))
        for path in sorted(directory.glob('CROSSCHECK_*.md')):
            if str(path) in valid:
                data = json.loads(Path(str(path) + '.json').read_text())
                print(path.name + ': ' + data['verdict'])
            else:
                print(path.name + ': INELIGIBLE (missing/failed metadata, invalid verdict, family or artifact hash)')
    else:
        sys.exit(run())
