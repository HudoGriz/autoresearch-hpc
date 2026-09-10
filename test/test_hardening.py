"""Behavioral regressions for the protocol boundaries; no live model required."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Protocol(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dl-hardening-')
        self.root = Path(self.temp.name) / 'project'
        self.env = dict(os.environ, DL_HOME=str(ROOT), DL_PROJECT=str(self.root),
                        PATH=str(ROOT / 'bin') + os.pathsep + os.environ['PATH'])
        subprocess.run([str(ROOT / 'bin/dl'), 'init', str(self.root)], check=True, capture_output=True)
        if os.environ.get('DL_TEST_SITE'):
            (self.root / '.dl/config/site.md').write_text(Path(os.environ['DL_TEST_SITE']).read_text())
        self.call('claim', '-t', 'validation')
        self.call('new', '-n', '1')
        self.it = self.root / 'iterations/iteration1'
        headings = ['Question', 'Estimand', 'Instrument', 'Acceptance criteria', 'Negative controls', 'Detection limit', 'Prediction']
        (self.it / 'README.md').write_text('\n'.join(f'## {i}. {h}\nDeterministic fixture; one failing check.\n' for i, h in enumerate(headings, 1)))
        self.call('gate', 'predeclare', '-n', '1')
        self.report = self.it / 'results/report/iteration1_report.md'
        self.report.parent.mkdir(parents=True, exist_ok=True)
        self.report.write_text('Negative controls reject failures. Detection limit: one check. Candidate only.\n')
        self.config = self.root / '.dl/config/harnesses.md'
        self.mock = self.root / 'mock.py'
        self.configure()

    def tearDown(self):
        self.temp.cleanup()

    def call(self, *args, good=True):
        result = subprocess.run([str(ROOT / 'bin/dl'), *args], env=self.env, cwd=self.root,
                                capture_output=True, text=True, timeout=90)
        if good:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def configure(self, body="print('VERDICT: SOUND')", family='anthropic', timeout=5):
        self.mock.write_text(body + '\n')
        self.config.write_text(f'''```dl-config
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
        p=self.root / '.dl/config/project.md'; p.write_text(p.read_text().replace('immutable_inputs  =', 'immutable_inputs  = raw'))
        self.call('guard', str(self.root/'raw/x'), good=False)

    def test_image_digest(self):
        image=self.root/'image.sif'; image.write_bytes(b'fixture')
        fake=self.root/'apptainer'; fake.write_text('#!/bin/sh\nexit 0\n'); fake.chmod(0o755)
        self.env['PATH']=str(self.root)+os.pathsep+self.env['PATH']
        site=self.root/'.dl/config/site.md'
        site.write_text(f'```dl-config\ncontainer_runtime = apptainer\nimage_test = {image}\nimage_test_sha256 = {hashlib.sha256(image.read_bytes()).hexdigest()}\n```\n')
        self.call('run', 'test', '--', 'true')
        image.write_bytes(b'changed'); self.call('run', 'test', '--', 'true', good=False)

    def test_remote_tag_rejected(self):
        (self.root/'.dl/config/site.md').write_text('```dl-config\ncontainer_runtime = docker\nimage_test = docker://python:latest\n```\n')
        self.call('run', 'test', '--', 'true', good=False)

    def test_result_snapshot_change_rejected(self):
        snapshot=self.it/'results/design.md'; snapshot.write_text('reviewed design')
        self.ask(); snapshot.write_text('changed design'); self.gate(good=False)

    def test_literal_prompt_placeholders_preserved(self):
        self.configure("import sys; assert '{cwd}' in sys.argv[1] and '{prompt}' in sys.argv[1]; print('VERDICT: SOUND')")
        self.call('ask', '-n', '1', '--note', 'Keep literal {cwd} and {prompt} in this source sample.')

    def test_local_digest_shaped_filename_is_hashed(self):
        image=self.root/('image@sha256:'+'a'*64); image.write_bytes(b'fixture')
        (self.root/'.dl/config/site.md').write_text(f'```dl-config\ncontainer_runtime = apptainer\nimage_test = {image}\n```\n')
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
