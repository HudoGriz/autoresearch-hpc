"""Behavioral regressions for the protocol boundaries; no live model required."""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Protocol(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='arh-hardening-')
        self.root = Path(self.temp.name) / 'project'
        self.env = dict(os.environ, ARH_HOME=str(ROOT), ARH_PROJECT=str(self.root),
                        PATH=str(ROOT / 'bin') + os.pathsep + os.environ['PATH'])
        subprocess.run([str(ROOT / 'bin/arh'), 'init', str(self.root)], check=True, capture_output=True)
        if os.environ.get('ARH_TEST_SITE'):
            (self.root / '.arh/config/site.md').write_text(Path(os.environ['ARH_TEST_SITE']).read_text())
        self.call('claim', '-t', 'validation')
        self.call('new', '-n', '1')
        self.it = self.root / 'iterations/iteration1'
        headings = ['Question', 'Estimand', 'Instrument', 'Acceptance criteria', 'Negative controls', 'Detection limit', 'Prediction']
        (self.it / 'README.md').write_text('\n'.join(f'## {i}. {h}\nDeterministic fixture; one failing check.\n' for i, h in enumerate(headings, 1)))
        self.call('gate', 'predeclare', '-n', '1')
        self.report = self.it / 'results/report/iteration1_report.md'
        self.report.parent.mkdir(parents=True, exist_ok=True)
        self.report.write_text('Negative controls reject failures. Detection limit: one check. Candidate only.\n')
        self.config = self.root / '.arh/config/harnesses.md'
        self.mock = self.root / 'mock.py'
        self.configure()

    def tearDown(self):
        self.temp.cleanup()

    def call(self, *args, good=True):
        result = subprocess.run([str(ROOT / 'bin/arh'), *args], env=self.env, cwd=self.root,
                                capture_output=True, text=True, timeout=90)
        if good:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def configure(self, body="print('VERDICT: SOUND')", family='anthropic', timeout=5):
        self.mock.write_text(body + '\n')
        self.config.write_text(f'''```arh-config
producer = source
verifier = reviewer
harness_source_family = openai
harness_reviewer_family = {family}
harness_reviewer_cmd = python3 "{self.mock}" {{prompt}}
ask_timeout = {timeout}
```
''')

    def ask(self, good=True):
        return self.call('ask', '-n', '1', good=good)

    def gate(self, good=True):
        return self.call('gate', 'results', '-n', '1', good=good)

    def test_closed_output_still_times_out(self):
        self.configure("import os,time; os.close(1); os.close(2); time.sleep(10)", timeout=1)
        self.ask(good=False)
        record = next(self.it.glob('CROSSCHECK_*.md.json'))
        self.assertEqual(json.loads(record.read_text())['exit_code'], 124)
        self.gate(good=False)

    def test_complete_review(self):
        self.ask(); self.gate()

    def test_failed_review_rejected(self):
        self.configure("print('VERDICT: SOUND'); raise SystemExit(7)")
        self.ask(good=False); self.gate(good=False)

    def test_missing_verdict_rejected(self):
        self.configure("print('looks fine')")
        self.ask(good=False); self.gate(good=False)

    def test_multiple_verdicts_rejected(self):
        self.configure("print('VERDICT: SOUND\\nVERDICT: UNSOUND')")
        self.ask(good=False); self.gate(good=False)

    def test_same_family_override_not_foreign(self):
        self.configure(family='openai')
        self.ask(good=False)
        self.call('ask', '-n', '1', '--same-family')
        self.gate(good=False)

    def test_unknown_family_rejected(self):
        self.configure(family='unknown'); self.ask(good=False)

    def test_mixed_family_rejected(self):
        self.configure(family='mixed'); self.ask(good=False)

    def test_stale_report_rejected(self):
        self.ask(); self.report.write_text(self.report.read_text() + 'Changed.\n'); self.gate(good=False)

    def test_modified_review_rejected(self):
        self.ask()
        record = next(self.it.glob('CROSSCHECK_*.md'))
        record.write_text(record.read_text() + 'Changed.\n'); self.gate(good=False)

    def test_legacy_filename_is_not_evidence(self):
        (self.it / 'CROSSCHECK_fake.md').write_text('VERDICT: SOUND\n'); self.gate(good=False)

    def test_repeated_reviews_unique(self):
        self.ask()
        self.call('ask', '-n', '1', '--note', 'Check a distinct concrete issue.')
        self.assertEqual(len(list(self.it.glob('CROSSCHECK_*.md.json'))), 2)

    def test_timeout_is_failure(self):
        self.configure('import time; time.sleep(10)', timeout=0.1)
        result=self.ask(good=False); self.assertEqual(result.returncode, 124); self.gate(good=False)

    def test_quotes_and_cwd(self):
        self.configure("import os,sys; assert os.getcwd() == " + repr(str(self.root)) + "; assert len(sys.argv)==2; print('VERDICT: SOUND')")
        self.ask(); self.gate()

    def test_refreeze_rejected_without_results(self):
        self.report.unlink()
        frozen=(self.it / 'PREDECLARATION.sha256').read_bytes()
        (self.it / 'README.md').write_text((self.it / 'README.md').read_text() + 'Changed\n')
        self.call('gate', 'predeclare', '-n', '1', good=False)
        self.assertEqual((self.it / 'PREDECLARATION.sha256').read_bytes(), frozen)

    def test_missing_rule_rejected(self):
        (self.root / 'rules/detection-limit-stated.md').unlink(); self.gate(good=False)

    def test_local_failure_propagates(self):
        script=self.it / 'scripts/it1_01_fail.sh'; script.write_text('set -euo pipefail\nexit 9\n')
        result=self.call('submit', str(script), '-w', good=False)
        self.assertNotEqual(result.returncode, 0)
        records=list((self.it/'logs').glob('nextflow/*/attempt-*/run.json'))
        self.assertNotEqual(json.loads(records[0].read_text())['exit_code'], 0)

    def test_submit_unfrozen_rejected(self):
        script=self.it / 'scripts/it1_01_no.sh'; script.write_text('exit 0\n')
        (self.it/'PREDECLARATION.sha256').unlink()
        self.call('submit', str(script), '-w', good=False)

    def test_relative_immutable_guard(self):
        p=self.root / '.arh/config/project.md'; p.write_text(p.read_text().replace('immutable_inputs  =', 'immutable_inputs  = raw'))
        self.call('guard', str(self.root/'raw/x'), good=False)

    def test_image_digest(self):
        image=self.root/'image.sif'; image.write_bytes(b'fixture')
        fake=self.root/'apptainer'; fake.write_text('#!/bin/sh\nexit 0\n'); fake.chmod(0o755)
        self.env['PATH']=str(self.root)+os.pathsep+self.env['PATH']
        site=self.root/'.arh/config/site.md'
        site.write_text(f'```arh-config\ncontainer_runtime = apptainer\nimage_test = {image}\nimage_test_sha256 = {hashlib.sha256(image.read_bytes()).hexdigest()}\n```\n')
        self.call('run', 'test', '--', 'true')
        image.write_bytes(b'changed'); self.call('run', 'test', '--', 'true', good=False)

    def test_remote_tag_rejected(self):
        (self.root/'.arh/config/site.md').write_text('```arh-config\ncontainer_runtime = docker\nimage_test = docker://python:latest\n```\n')
        self.call('run', 'test', '--', 'true', good=False)

    def test_result_snapshot_change_rejected(self):
        snapshot=self.it/'results/design.md'; snapshot.write_text('reviewed design')
        self.ask(); snapshot.write_text('changed design'); self.gate(good=False)

    def test_literal_prompt_placeholders_preserved(self):
        self.configure("import sys; assert '{cwd}' in sys.argv[1] and '{prompt}' in sys.argv[1]; print('VERDICT: SOUND')")
        self.call('ask', '-n', '1', '--note', 'Keep literal {cwd} and {prompt} in this source sample.')

    def test_local_digest_shaped_filename_is_hashed(self):
        image=self.root/('image@sha256:'+'a'*64); image.write_bytes(b'fixture')
        (self.root/'.arh/config/site.md').write_text(f'```arh-config\ncontainer_runtime = apptainer\nimage_test = {image}\n```\n')
        self.call('run', 'test', '--', 'true', good=False)

    def test_gate_surfaces_unsound_verdict(self):
        self.configure("print('VERDICT: UNSOUND')")
        self.ask(); result=self.gate(); self.assertIn('UNSOUND', result.stdout)

    def test_unchanged_review_reused(self):
        self.ask(); result=self.ask()
        self.assertIn('no model call', result.stdout)
        self.assertEqual(len(list(self.it.glob('CROSSCHECK_*.md.json'))), 1)

    def test_review_round_limit(self):
        self.ask(); self.call('ask', '-n', '1', '--note', 'Concrete second check')
        self.call('ask', '-n', '1', '--note', 'Third check exceeds budget', good=False)
        self.assertEqual(len(list(self.it.glob('CROSSCHECK_*.md.json'))), 2)

    def test_provider_error_does_not_consume_round(self):
        # codex exec printed this and exited 0 on a real cluster (2026-09-10).
        self.configure("print(\"ERROR: You've hit your usage limit. Try again at 4:13 PM.\")")
        result = self.ask(good=False)
        self.assertIn('did not consume a review round', result.stderr)
        self.assertIn('PROVIDER ERROR', self.call('gate', 'results', '-n', '1', good=False).stdout)
        self.configure()
        self.ask()                                   # first real round: no --note required
        self.call('ask', '-n', '1', '--note', 'Concrete second check')
        self.assertEqual(len(list(self.it.glob('CROSSCHECK_*.md.json'))), 3)
        self.gate()

    def test_rule_violation_blocks_review_before_dispatch(self):
        # A report the results gate will reject must not be sent for review: fixing it afterwards
        # invalidates the review and costs a round (2026-09-11).
        # Violates detection-limit-stated (it never states one); every other rule is satisfied.
        self.report.write_text('Negative controls reject failures. Candidate only.\n')
        result = self.ask(good=False)
        self.assertIn('standing rules', result.stderr)
        self.assertFalse(list(self.it.glob('CROSSCHECK_*.md.json')))

    def test_verbose_stderr_does_not_abort_review(self):
        # codex exec echoes the entire prompt to stderr; a 16 KB stderr cap killed every real
        # review (exit 66) before the model answered (2026-09-11).
        self.configure("import sys; sys.stderr.write('x' * 40000); print('VERDICT: SOUND')")
        self.ask(); self.gate()

    def test_input_budget_prevents_dispatch(self):
        self.call('ask', '-n', '1', '--note', 'x'*25000, good=False)
        self.assertFalse(list(self.it.glob('CROSSCHECK_*.md.json')))

    def test_output_budget_rejects_incomplete_review(self):
        self.configure("print('VERDICT: SOUND'); print('x'*12000)")
        self.ask(good=False); self.gate(good=False)

    def test_context_is_bounded_and_deterministic(self):
        first=self.call('context', '-n', '1').stdout
        self.assertEqual(first,self.call('context','-n','1').stdout)
        self.assertLess(len(first.encode()),8000)
        self.assertEqual(json.loads(first)['predeclaration'],'frozen')

    def test_named_launch_lock(self):
        lock=self.it/'metadata/nextflow/busy/.launch-lock'; lock.mkdir(parents=True)
        script=self.it/'scripts/it1_01_busy.nf'; script.write_text('workflow {}')
        result=self.call('submit',str(script),'-n','busy',good=False)
        self.assertIn('already running',result.stderr)

    def test_live_owner_lock_is_kept(self):
        lock=self.it/'metadata/nextflow/busy/.launch-lock'; lock.mkdir(parents=True)
        (lock/'owner.json').write_text(json.dumps({'host': socket.gethostname(), 'pid': os.getpid()}))
        script=self.it/'scripts/it1_01_busy.nf'; script.write_text('workflow {}')
        result=self.call('submit',str(script),'-n','busy',good=False)
        self.assertIn('already running',result.stderr); self.assertTrue(lock.is_dir())

    def test_dead_owner_lock_reclaimed_and_scripts_hashed(self):
        # A wrapper killed before its `finally` left .launch-lock behind and every later submit
        # under that name refused; the receipt also hashed the workflow but not the scripts it
        # calls (2026-09-11).
        dead=subprocess.Popen(['true']); dead.wait()
        lock=self.it/'metadata/nextflow/ok/.launch-lock'; lock.mkdir(parents=True)
        (lock/'owner.json').write_text(json.dumps({'host': socket.gethostname(), 'pid': dead.pid}))
        (self.it/'scripts/it1_00_helper.py').write_text('print(1)\n')
        script=self.it/'scripts/it1_01_ok.sh'; script.write_text('set -euo pipefail\nexit 0\n')
        result=self.call('submit',str(script),'-n','ok')
        self.assertIn('reclaimed a launch lock',result.stderr); self.assertFalse(lock.exists())
        record=json.loads(next((self.it/'logs/nextflow/ok').glob('attempt-*/run.json')).read_text())
        self.assertIn('iterations/iteration1/scripts/it1_00_helper.py',record['script_sha256'])

    def test_sigterm_to_wrapper_releases_lock(self):
        # Stopping a submit by signalling its wrapper left the lock behind (2026-09-11). The
        # wrapper now forwards the signal to Nextflow, records it, and releases the lock.
        script=self.it/'scripts/it1_01_slow.sh'; script.write_text('sleep 300\n')
        proc=subprocess.Popen([str(ROOT/'bin/arh'),'submit',str(script),'-n','slow'],env=self.env,cwd=self.root,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        work=self.it/'metadata/nextflow/slow/work'; deadline=time.time()+120
        while proc.poll() is None and time.time()<deadline and not list(work.glob('*/*/.command.begin')):
            time.sleep(0.5)
        if proc.poll() is not None:     # build the message only on failure: communicate() blocks
            self.fail('submit ended before its task started: '+proc.communicate()[1][-2000:])
        proc.send_signal(signal.SIGTERM); out,err=proc.communicate(timeout=120)
        self.assertNotEqual(proc.returncode,0,err)
        self.assertFalse((self.it/'metadata/nextflow/slow/.launch-lock').exists())
        record=json.loads(next((self.it/'logs/nextflow/slow').glob('attempt-*/run.json')).read_text())
        self.assertEqual(record['signal'],'SIGTERM')


if __name__ == '__main__':
    unittest.main(verbosity=2)
