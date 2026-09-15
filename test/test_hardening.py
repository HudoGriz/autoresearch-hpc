"""Behavioral regressions for the protocol boundaries; no live model required."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


# Submission tests need a configured controller and task runtime; without one they
# would fail for reasons unrelated to the protocol (and, on a Slurm host, submit real jobs).
needs_site = unittest.skipUnless(os.environ.get('ARH_TEST_SITE'),
                                 'set ARH_TEST_SITE to a configured local site.md (see README)')
needs_network = unittest.skipUnless(os.environ.get('ARH_TEST_NETWORK'), 'set ARH_TEST_NETWORK=1 to solve real packages')
REFUSE = ("import sys; sys.stderr.write('This content was flagged for possible biological risk. "
          "If this seems wrong, try rephrasing your request.\\n'); raise SystemExit(1)")


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

    def call(self, *args, good=True, timeout=90):
        result = subprocess.run([str(ROOT / 'bin/arh'), *args], env=self.env, cwd=self.root,
                                capture_output=True, text=True, timeout=timeout)
        if good is True:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        elif good is False:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def configure(self, body="print('VERDICT: SOUND')", family='anthropic', timeout=5, version=None, cmd_extra=''):
        self.mock.write_text(body + '\n')
        extra = f'harness_reviewer_version_cmd = {version}\n' if version else ''
        self.config.write_text(f'''```arh-config
producer = source
verifier = reviewer
harness_source_family = openai
harness_reviewer_family = {family}
harness_reviewer_cmd = python3 "{self.mock}" {{prompt}}{cmd_extra}
{extra}ask_timeout = {timeout}
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

    @needs_site
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
        result = self.call('ask', '-n', '1', '--note', 'x'*25000, good=False)
        self.assertFalse(list(self.it.glob('CROSSCHECK_*.md.json')))
        # The refusal names the size, the limit and the parts (field report, 2026-09-11).
        self.assertIn('ask_max_input_bytes is 24000', result.stderr)
        self.assertIn('pre-declaration', result.stderr)

    def test_output_budget_rejects_incomplete_review(self):
        self.configure("print('VERDICT: SOUND'); print('x'*12000)")
        self.ask(good=False); self.gate(good=False)

    def test_context_is_bounded_and_deterministic(self):
        first=self.call('context', '-n', '1').stdout
        self.assertEqual(first,self.call('context','-n','1').stdout)
        self.assertLess(len(first.encode()),8000)
        self.assertEqual(json.loads(first)['predeclaration'],'frozen')

    @needs_site
    def test_named_launch_lock(self):
        lock=self.it/'metadata/nextflow/busy/.launch-lock'; lock.mkdir(parents=True)
        script=self.it/'scripts/it1_01_busy.nf'; script.write_text('workflow {}')
        result=self.call('submit',str(script),'-n','busy',good=False)
        self.assertIn('already running',result.stderr)

    @needs_site
    def test_live_owner_lock_is_kept(self):
        lock=self.it/'metadata/nextflow/busy/.launch-lock'; lock.mkdir(parents=True)
        (lock/'owner.json').write_text(json.dumps({'host': socket.gethostname(), 'pid': os.getpid()}))
        script=self.it/'scripts/it1_01_busy.nf'; script.write_text('workflow {}')
        result=self.call('submit',str(script),'-n','busy',good=False)
        self.assertIn('already running',result.stderr); self.assertTrue(lock.is_dir())

    @needs_site
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

    @needs_site
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

    def legacy_study(self):
        """A minimal 0.1-layout study built from the current templates."""
        old = Path(self.temp.name) / 'legacy'
        (old / '.dl/config').mkdir(parents=True); (old / 'rules').mkdir()
        for name in ('site.md', 'project.md', 'harnesses.md'):
            (old / '.dl/config' / name).write_text((ROOT / 'config' / name).read_text().replace('arh-config', 'dl-config'))
        for rule in (ROOT / 'config/rules').glob('*.md'):
            (old / 'rules' / rule.name).write_text(rule.read_text().replace('arh-config', 'dl-config'))
        (old / '.dl/VERSION').write_text('protocol = 0.1.0\n')
        (old / '.dl/registry.tsv').write_text('iteration\tagent\tclaimed\tstatus\ttitle\n')
        (old / 'PROGRESS.md').write_text('# PROGRESS\n\n<!-- dl:status:begin — generated by `dl ledger render`; '
                                         'do not edit by hand -->\n| 1 | old |\n<!-- dl:status:end -->\n\n'
                                         'Iteration 1: `dl gate results` passed.\n')
        (old / 'AGENTS.md').write_text('# Automated discovery loop — agent contract\n\nUse `dl claim`.\n')
        it = old / 'iterations/iteration1'; it.mkdir(parents=True)
        (it / 'README.md').write_text('A frozen pre-declaration that mentions dl-config.\n')
        (it / 'CLAIM.json').write_text('{\n  "iteration": 1,\n  "declared_agent": "old",\n  "title": "legacy question"\n}\n')
        (old / 'iterations/iteration2').mkdir()                    # an iteration folder with no claim record
        return old

    def test_migrate_legacy_study(self):
        # Moving a real 0.1 study by hand took eight steps and missed the ledger markers (2026-09-11).
        old = self.legacy_study(); readme = (old / 'iterations/iteration1/README.md').read_bytes()
        env = dict(self.env, ARH_PROJECT=str(old))
        run = lambda *a: subprocess.run([str(ROOT / 'bin/arh'), 'migrate', str(old), *a], env=env, cwd=old,  # noqa: E731
                                        capture_output=True, text=True, timeout=120)
        dry = run()
        self.assertEqual(dry.returncode, 0, dry.stderr); self.assertIn('would change', dry.stdout)
        self.assertFalse((old / '.dl').is_symlink()); self.assertFalse((old / '.arh').exists())
        applied = run('--apply'); self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertTrue((old / '.arh').is_dir()); self.assertTrue((old / '.dl').is_symlink())
        for p in [*(old / '.arh/config').glob('*.md'), *(old / 'rules').glob('*.md')]:
            self.assertNotRegex(p.read_text(), r'(?m)^\s*```\s*dl-config', p.name)
        ledger = (old / 'PROGRESS.md').read_text()
        self.assertIn('arh:status:begin', ledger); self.assertNotIn('dl:status', ledger)
        self.assertIn('`dl gate results` passed', ledger)          # the record's prose is left as written
        protocol = re.search(r'protocol, v(\S+)', (ROOT / 'PROTOCOL.md').read_text()).group(1)
        self.assertIn(f'protocol = {protocol}', (old / '.arh/VERSION').read_text())
        self.assertTrue((old / 'AGENTS.md').read_text().startswith('# AutoResearch HPC'))
        self.assertTrue((old / 'skills/iterate/SKILL.md').is_file())
        self.assertEqual((old / 'iterations/iteration1/README.md').read_bytes(), readme)
        self.assertTrue(list((old / '.arh').glob('migration-backup-*.tgz')))
        subprocess.run([str(ROOT / 'bin/arh'), 'ledger', 'render'], env=env, cwd=old, check=True, capture_output=True)
        self.assertEqual((old / 'PROGRESS.md').read_text().count('status:begin'), 1)
        self.assertIn('nothing to do', run('--apply').stdout)

    def test_ledger_render_refuses_a_foreign_status_block(self):
        ledger = self.root / 'PROGRESS.md'
        text = ledger.read_text().replace('arh:status:', 'old:status:'); ledger.write_text(text)
        self.assertIn("'old:status'", self.call('ledger', 'render', good=False).stderr)
        self.assertEqual(ledger.read_text(), text)

    def test_ledger_check_detects_a_stale_table(self):
        self.ask(); self.call('ledger', 'render'); self.call('ledger', 'check')
        ledger = self.root / 'PROGRESS.md'
        ledger.write_text(ledger.read_text().replace('| frozen |', '| draft |'))
        self.assertIn('stale', self.call('ledger', 'check', good=False).stdout)
        self.call('ledger', 'render'); self.call('ledger', 'check')

    def test_rule_scope_paragraph(self):
        # One qualifier anywhere used to excuse every use of a forbidden term (2026-09-11).
        rule = self.root / 'rules/recall-scoped.md'
        body = 'id = recall-scoped\nseverity = error\napplies = report\nforbid = recall\nrequires = end.to.end\n'
        rule.write_text(f'```arh-config\n{body}scope = paragraph\n```\n')
        project = self.root / '.arh/config/project.md'
        project.write_text(re.sub(r'(?m)^(rules\s*=.*)$', r'\1 recall-scoped', project.read_text()))
        doc = self.root / 'doc.md'
        base = 'Negative controls did not fire. Detection limit: one event.\n\nEnd-to-end recall is 50%.\n\n'
        doc.write_text(base + 'Recall rose.\n')
        self.assertIn('a paragraph uses', self.call('gate', 'rules', str(doc), good=False).stdout)
        doc.write_text(base + 'End-to-end recall rose.\n'); self.call('gate', 'rules', str(doc))
        rule.write_text(f'```arh-config\n{body}```\n')             # default scope: document, as before
        doc.write_text(base + 'Recall rose.\n'); self.call('gate', 'rules', str(doc))

    def test_review_records_verifier_version(self):
        # The record named the verifier's family but not the build that answered (2026-09-11).
        self.configure(version='python3 -c "print(\'mock-cli 1.2.3\')"')
        self.ask()
        record = json.loads(next(self.it.glob('CROSSCHECK_*.md.json')).read_text())
        self.assertEqual(record['verifier_version'], 'mock-cli 1.2.3')
        self.gate()

    def test_doctor_names_a_protocol_mismatch(self):
        self.assertNotIn('records protocol', self.call('doctor', good=None).stdout)
        (self.root / '.arh/VERSION').write_text('protocol = 0.1.0\n')
        result = self.call('doctor', good=False)
        self.assertIn('records protocol 0.1.0', result.stdout); self.assertIn('arh migrate', result.stdout)

    def test_gate_warns_without_review_response(self):
        self.ask()
        self.assertIn('no REVIEW_RESPONSE.md', self.gate().stdout)
        (self.it / 'REVIEW_RESPONSE.md').write_text('Finding 1: accepted.\n')
        self.assertNotIn('no REVIEW_RESPONSE.md', self.gate().stdout)

    def test_claim_records_agent_source(self):
        env = {k: v for k, v in self.env.items() if not k.startswith(('CLAUDE', 'CODEX', 'OPENCODE', 'ARH_AGENT'))}
        def claim(title, **extra):
            result = subprocess.run([str(ROOT / 'bin/arh'), 'claim', '-t', title], env={**env, **extra},
                                    cwd=self.root, capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads((self.root / f'iterations/iteration{result.stdout.strip()}/CLAIM.json').read_text())
            return record, result.stderr
        record, stderr = claim('inherited marker', CLAUDECODE='1')
        self.assertEqual((record['agent'], record['agent_source']), ('claude', 'CLAUDECODE'))
        self.assertIn("configured producer is 'source'", stderr)
        record, stderr = claim('explicit agent', CLAUDECODE='1', ARH_AGENT='source')
        self.assertEqual((record['agent'], record['agent_source']), ('source', 'ARH_AGENT'))
        self.assertNotIn('configured producer', stderr)

    def test_content_refusal_is_its_own_outcome(self):
        # Codex refused a public RNA-seq count table as "flagged for possible biological risk"
        # (2026-09-15). Waiting does not change that, so it must not look like a quota error.
        self.configure(REFUSE)
        result = self.ask(good=False)
        self.assertEqual(result.returncode, 77, result.stderr)
        self.assertIn('content-policy', result.stderr)
        self.assertIn('provider said: This content was flagged', result.stderr)
        record = json.loads(next(self.it.glob('CROSSCHECK_*.md.json')).read_text())
        self.assertEqual((record['provider_error'], record['provider_error_kind']), (True, 'refusal'))
        self.assertIn('PROVIDER REFUSAL', self.gate(good=False).stdout)
        self.configure()
        self.ask()                                   # no round was spent: no --note required
        self.gate()

    def test_fallback_verifier_after_content_refusal(self):
        self.configure(REFUSE)
        backup = self.root / 'backup.py'
        backup.write_text("print('VERDICT: QUALIFIED')\n")
        with self.config.open('a') as cfg:
            cfg.write(f'```arh-config\nverifier_fallback = kin backup\n'
                      f'harness_kin_family = openai\nharness_kin_cmd = python3 "{backup}" {{prompt}}\n'
                      f'harness_backup_family = google\nharness_backup_cmd = python3 "{backup}" {{prompt}}\n```\n')
        result = self.ask()
        self.assertIn("fallback verifier 'kin' skipped", result.stderr)   # the producer's own family
        self.assertIn('VERDICT: QUALIFIED', result.stdout)
        kinds = sorted(json.loads(p.read_text())['provider_error_kind'] or 'review'
                       for p in self.it.glob('CROSSCHECK_*.md.json'))
        self.assertEqual(kinds, ['refusal', 'review'])
        self.gate()

    def test_limit_names_its_reset_and_skips_fallback(self):
        self.configure("print(\"ERROR: You've hit your usage limit. Try again at 4:13 PM.\")")
        with self.config.open('a') as cfg:
            cfg.write(f'```arh-config\nverifier_fallback = backup\nharness_backup_family = google\n'
                      f'harness_backup_cmd = python3 "{self.mock}" {{prompt}}\n```\n')
        result = self.ask(good=False)
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn('Try again at 4:13 PM', result.stderr)
        records = [json.loads(p.read_text()) for p in self.it.glob('CROSSCHECK_*.md.json')]
        self.assertEqual([(r['provider_error_kind'], r['retry_hint']) for r in records],
                         [('limit', 'Try again at 4:13 PM')])

    def test_review_records_usage(self):
        # "Bounded model calls" bounded bytes, but nothing counted tokens (2026-09-14).
        self.configure("import json,sys; open(sys.argv[2],'w').write(json.dumps({'input_tokens': 7})); "
                       "print('VERDICT: SOUND')", cmd_extra=' {usage}')
        self.ask()
        record = json.loads(next(self.it.glob('CROSSCHECK_*.md.json')).read_text())
        self.assertEqual(record['usage'], {'input_tokens': 7})
        self.assertFalse(list(self.it.glob('*.usage.json')))
        self.gate()

    def test_review_lock_owner_and_reclaim(self):
        lock = self.it / '.review-lock'
        lock.mkdir()
        (lock / 'owner.json').write_text(json.dumps({'host': socket.gethostname(), 'pid': os.getpid()}))
        self.assertIn('another review is running', self.ask(good=False).stderr)
        dead = subprocess.Popen(['true']); dead.wait()
        (lock / 'owner.json').write_text(json.dumps({'host': socket.gethostname(), 'pid': dead.pid}))
        self.assertIn('reclaimed a review lock', self.ask().stderr)
        self.assertFalse(lock.exists())

    def test_wait_blocks_on_live_work_only(self):
        # Headless sessions that ended their reply to wait for background work lost it (2026-09-14).
        self.assertIn('idle', self.call('wait', '-n', '1', '--timeout', '5').stdout)
        lock = self.it / 'metadata/nextflow/busy/.launch-lock'
        lock.mkdir(parents=True)
        holder = subprocess.Popen(['sleep', '60'])
        try:
            (lock / 'owner.json').write_text(json.dumps({'host': socket.gethostname(), 'pid': holder.pid}))
            result = self.call('wait', '-n', '1', '--timeout', '1', '--interval', '0.2', good=False)
            self.assertEqual(result.returncode, 124)
            self.assertIn('iteration1: submission busy', result.stdout)
        finally:
            holder.kill(); holder.wait()
        result = self.call('wait', '-n', '1', '--timeout', '5', '--interval', '0.2')
        self.assertIn('ignored: iteration1: submission busy', result.stdout)
        self.assertIn('idle', result.stdout)

    def test_migrate_refreshes_agent_contract_and_skills(self):
        # Agents read the study's copies, so framework fixes to AGENTS.md never reached them (2026-09-15).
        agents, skill = self.root / 'AGENTS.md', self.root / 'skills/iterate/SKILL.md'
        agents.write_text('# stale contract\n'); skill.unlink()
        own = self.root / 'skills/local/SKILL.md'; own.parent.mkdir(); own.write_text('project skill\n')
        self.assertIn("differ from the framework's", self.call('doctor', good=None).stderr)
        migrate = lambda *a: self.call('migrate', str(self.root), *a)  # noqa: E731
        self.assertIn('agent contract refreshed', migrate().stdout)
        self.assertEqual(agents.read_text(), '# stale contract\n')     # a dry run writes nothing
        migrate('--apply')
        self.assertEqual(agents.read_text(), (ROOT / 'AGENTS.md').read_text())
        self.assertEqual(skill.read_text(), (ROOT / 'skills/iterate/SKILL.md').read_text())
        self.assertEqual(own.read_text(), 'project skill\n')
        self.assertTrue((self.root / 'CLAUDE.md').is_symlink())
        self.assertIn('nothing to do', migrate().stdout)

    def test_env_cache_builds_once_for_many_projects(self):
        # Every study built its own ~1.5 GB of environments (2026-09-14).
        fake = Path(self.temp.name) / 'fake'; fake.mkdir()
        log, mm = fake / 'creates.log', fake / 'micromamba'
        mm.write_text(f"""#!{sys.executable}
import sys
from pathlib import Path
args = sys.argv[1:]
if args[:1] == ['--version']:
    print('2.8.1'); sys.exit()
prefix = Path(args[args.index('-p') + 1])
if args[0] == 'create':
    with open({str(log)!r}, 'a') as fh:
        fh.write(str(prefix) + '\\n')
    (prefix / 'bin').mkdir(parents=True)
    (prefix / 'bin/python3').symlink_to({sys.executable!r})
    (prefix / 'bin/nextflow').write_text('#!/bin/sh\\n')
    (prefix / 'bin/nextflow').chmod(0o755)
elif args[0] == 'list':
    print('https://conda.example/pkg-1.0-0.conda#' + 'a' * 32)
""")
        singularity = fake / 'singularity'        # `exec [options] IMAGE micromamba ARGS` runs the fake
        singularity.write_text(f'#!/bin/sh\nwhile [ "$1" != micromamba ]; do shift; done\nshift\nexec "{mm}" "$@"\n')
        for tool in (mm, singularity):
            tool.chmod(0o755)
        image, cache = fake / 'runtime.sif', Path(self.temp.name) / 'cache'
        image.write_bytes(b'image')
        env = dict(self.env, PATH=str(fake) + os.pathsep + self.env['PATH'])
        prefixes = []
        for name in ('a', 'b'):
            project = Path(self.temp.name) / name
            result = subprocess.run([str(ROOT / 'bin/arh'), 'init', str(project), '--bootstrap', '--micromamba', str(mm),
                                     '--runtime', str(image), '--env-cache', str(cache)],
                                    env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            site = (project / '.arh/config/site.md').read_text()
            prefixes.append([re.search(rf'(?m)^{key}\s*=\s*(\S+)', site).group(1) for key in ('nextflow_prefix', 'runtime_prefix')])
            self.assertTrue((project / '.arh/nextflow-host-explicit.lock').is_file())
        self.assertEqual(prefixes[0], prefixes[1])
        for prefix in prefixes[0]:
            self.assertTrue(prefix.startswith(str(cache)), prefix)
            self.assertTrue(Path(prefix, '.arh-complete').is_file())
        self.assertEqual(len(log.read_text().splitlines()), 2)       # host and task environment, each built once

    @needs_site
    def test_nextflow_reports_setting(self):
        site = self.root / '.arh/config/site.md'
        script = self.it / 'scripts/it1_01_ok.sh'; script.write_text('exit 0\n')
        for mode in ('gzip', 'none'):
            text = re.sub(r'(?m)^nextflow_reports\s*=.*\n', '', site.read_text())
            site.write_text(text + f'\n```arh-config\nnextflow_reports = {mode}\n```\n')
            self.call('submit', str(script), '-n', 'reports_' + mode, timeout=300)
            attempt = next((self.it / 'logs/nextflow' / ('reports_' + mode)).glob('attempt-*'))
            self.assertEqual(json.loads((attempt / 'run.json').read_text())['reports'], mode)
            self.assertFalse(list(attempt.glob('*.html')))
            self.assertEqual(sorted(p.name for p in attempt.glob('*.html.gz')),
                             ['report.html.gz', 'timeline.html.gz'] if mode == 'gzip' else [])

    @needs_site
    def test_lint_checks_without_running(self):
        good = self.it / 'scripts/it1_01_good.nf'
        good.write_text('workflow {\n    channel.of(1).view()\n}\n')
        self.call('submit', str(good), '--lint', timeout=300)
        bad = self.it / 'scripts/it1_02_bad.nf'
        bad.write_text('import groovy.json.JsonSlurper\n\nworkflow {\n    println(new JsonSlurper())\n}\n')
        self.call('submit', str(bad), '--lint', good=False, timeout=300)
        self.assertFalse((self.it / 'logs/nextflow').exists())

    @needs_site
    @needs_network
    def test_env_create_locks_and_is_immutable(self):
        prefix = self.call('env', 'create', 'tiny', 'zlib', timeout=1200).stdout.strip()
        self.assertTrue(Path(prefix, '.arh-complete').is_file())
        lock = self.root / '.arh/tiny-explicit.lock'
        self.assertEqual(lock.read_text().splitlines()[0], '@EXPLICIT')
        self.assertIn('zlib', lock.read_text())
        self.assertEqual(self.call('env', 'path', 'tiny').stdout.strip(), prefix)
        self.assertIn('is ready', self.call('env', 'create', 'tiny', 'zlib').stderr)
        self.assertIn('different package set', self.call('env', 'create', 'tiny', 'zlib', 'xz', good=False).stderr)
        shutil.rmtree(prefix)
        self.call('env', 'create', 'tiny', timeout=1200)             # rebuilt from its lock, package list verified
        self.assertTrue(Path(prefix, '.arh-complete').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)
