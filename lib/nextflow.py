"""Delegate execution to Nextflow; keep only protocol checks and run receipts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import shutil
import shlex
import sys
import tempfile

from project import config, guard


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def alive(pid):
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except (PermissionError, ValueError, TypeError, OverflowError):
        return True
    return True


def acquire(lock, parser):
    """Take the named launch lock. A lock whose recorded owner is a dead process on this host is
    reclaimed; a lock with no owner record, or a live or remote owner, is left alone."""
    try:
        lock.mkdir()
    except FileExistsError:
        try:
            owner = json.loads((lock / 'owner.json').read_text())
        except (OSError, ValueError):
            owner = None
        if not owner or owner.get('host') != socket.gethostname() or alive(owner.get('pid')):
            where = f" (owner pid {owner.get('pid')} on {owner.get('host')}; stop it with kill -TERM)" if owner else ''
            parser.error('this named workflow is already running; inspect .launch-lock before recovery' + where)
        stale = lock.with_name(f'{lock.name}.stale-{os.getpid()}')
        try:
            lock.rename(stale)      # atomic: of two reclaimers only one succeeds
        except OSError:
            parser.error('this named workflow is already running; inspect .launch-lock before recovery')
        shutil.rmtree(stale, ignore_errors=True)
        print(f"arh: reclaimed a launch lock left by dead process {owner['pid']} on {owner['host']}", file=sys.stderr)
        try:
            lock.mkdir()
        except FileExistsError:
            parser.error('this named workflow is already running; inspect .launch-lock before recovery')
    (lock / 'owner.json').write_text(json.dumps({'host': socket.gethostname(), 'pid': os.getpid(),
                                                 'started': datetime.now(timezone.utc).isoformat()}) + '\n')


def release(lock):
    (lock / 'owner.json').unlink(missing_ok=True)
    lock.rmdir()


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workflow', type=Path)
    parser.add_argument('-n', '--name')
    parser.add_argument('-w', '--wait', action='store_true', help='compatibility flag; Nextflow always owns the run until completion')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--params', type=Path, help='Nextflow JSON/YAML params file')
    parser.add_argument('-l', '--logdir', type=Path)
    args = parser.parse_args()
    root, home = Path(os.environ['ARH_ROOT']), Path(os.environ['ARH_HOME'])
    site = config(root / '.arh/config/site.md')
    project = config(root / '.arh/config/project.md')
    immutable = project.get('immutable_inputs', '').split()
    workflow = args.workflow.resolve()
    if not workflow.is_file() or root not in workflow.parents:
        parser.error('workflow must be a local file inside the study')
    iteration = next((p for p in workflow.parents if (p / 'CLAIM.json').is_file()), None)
    if iteration is None or root not in iteration.parents:
        parser.error('workflow must belong to a claimed iteration')
    freeze = iteration / 'PREDECLARATION.sha256'
    if not freeze.is_file() or freeze.read_text().splitlines()[0] != sha(iteration / 'README.md'):
        parser.error('iteration must have an unchanged frozen pre-declaration')
    name = args.name or workflow.stem
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
        parser.error('name must contain only letters, digits, underscores and hyphens')
    if workflow.suffix not in ('.nf', '.sh'):
        parser.error('supply a native .nf workflow or a migration .sh script')
    if args.resume and workflow.suffix == '.sh':
        parser.error('resume requires a native .nf workflow with declared inputs; shell adapter is never cached')
    image = site.get('runtime_image') or os.environ.get('ARH_RUNTIME_IMAGE')
    prefix = site.get('nextflow_prefix')
    if os.environ.get('APPTAINER_CONTAINER') or os.environ.get('SINGULARITY_CONTAINER'):
        parser.error('run the Nextflow controller on the host, outside Singularity')
    if not image or not prefix:
        parser.error('configure runtime_image and nextflow_prefix for the host micromamba driver')
    binary = Path(prefix) / 'bin/nextflow'
    if not binary.is_file():
        parser.error('versioned micromamba env/bin/nextflow is missing; host fallback is disabled')
    pin = json.loads((home / 'config/dependencies.json').read_text())['nextflow']
    version = site.get('nextflow_version') or pin['version']
    installed = list((Path(prefix) / 'conda-meta').glob('nextflow-*.json'))
    if len(installed) != 1 or json.loads(installed[0].read_text()).get('version') != version:
        parser.error('host Nextflow environment does not match the configured version')
    expected = sha(binary)
    engine = guard(iteration / 'metadata/nextflow' / name, root, immutable)
    logs = guard((args.logdir or iteration / 'logs/nextflow') / name, root, immutable)
    # Custom log locations must also respect iteration ownership.
    if iteration not in logs.parents:
        parser.error('logs must stay under the producing iteration')
    engine.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    lock = engine / '.launch-lock'
    acquire(lock, parser)
    try:
        attempt = Path(tempfile.mkdtemp(prefix='attempt-', dir=logs))
        env = dict(os.environ, NXF_HOME=str(root / '.arh/nextflow'), NXF_VER=version,
                   NXF_ANSI_LOG='false', NXF_DISABLE_CHECK_LATEST='true', NXF_OFFLINE='true')
        # Plugins/images must be staged in advance for offline execution.
        site_nf = root / '.arh/config/nextflow.config'
        generated = attempt / 'execution.config'
        executor = site.get('scheduler', 'local')
        if executor not in ('local', 'slurm', 'pbs'):
            parser.error('scheduler must be local, slurm or pbs')
        runtime = 'singularity'
        def literal(value):
            return json.dumps(str(value)).replace('$', '\\$')
        if not shutil.which('singularity'):
            parser.error('Singularity must be available on the host')
        if executor == 'slurm':
            for tool in ('sbatch', 'squeue', 'scancel'):
                if not shutil.which(tool):
                    parser.error('Slurm command missing from host PATH: ' + tool)
        if not Path(image).is_file() or sha(image) != site.get('runtime_sha256'):
            parser.error('runtime SIF missing or digest mismatch')
        binds = [str(root) + ':' + str(root) + ':rw']
        task_prefix = site.get('runtime_prefix')
        if task_prefix:
            binds.append(task_prefix + ':' + task_prefix + ':ro')
        for item in immutable:
            source = Path(item)
            source = (source if source.is_absolute() else root / source).resolve()
            binds.append(str(source) + ':' + str(source) + ':ro')
        options = ' '.join('--bind ' + shlex.quote(bind) for bind in binds)
        if task_prefix:
            options += ' --env ' + shlex.quote('PATH=' + task_prefix + '/bin:/usr/local/bin:/usr/bin:/bin')
        lines = [f'process.executor = {literal(executor)}', 'process.errorStrategy = "terminate"',
                 'process.maxRetries = 0', 'tower.enabled = false', 'wave.enabled = false',
                 f'process.container = {literal(image)}', 'singularity.enabled = true',
                 'singularity.autoMounts = true', f'singularity.runOptions = {literal(options)}']
        if executor == 'slurm':
            for key, directive in [('slurm_partition', 'queue'), ('slurm_time', 'time'),
                                   ('slurm_mem', 'memory')]:
                if site.get(key):
                    lines.append(f'process.{directive} = {literal(site[key])}')
            if site.get('slurm_cpus'):
                lines.append('process.cpus = ' + str(int(site['slurm_cpus'])))
            cluster_options = site.get('slurm_extra', '')
            if site.get('slurm_account'):
                cluster_options += ' --account=' + shlex.quote(site['slurm_account'])
            if cluster_options.strip():
                lines.append('process.clusterOptions = ' + literal(cluster_options.strip()))
        generated.write_text('\n'.join(lines) + '\n')
        configs = [str(site_nf)] if site_nf.is_file() else []
        configs.append(str(generated))
        cmd = [str(Path(binary).resolve()), '-log', str(attempt / 'nextflow.log'), '-C', ','.join(configs),
               'run', str(workflow if workflow.suffix == '.nf' else home / 'workflows/script.nf'),
               '-work-dir', str(engine / 'work'), '-with-trace', str(attempt / 'trace.tsv'),
               '-with-report', str(attempt / 'report.html'), '-with-timeline', str(attempt / 'timeline.html'),
               '-ansi-log', 'false']
        if args.resume:
            cmd.append('-resume')
        if args.params:
            params = args.params.resolve()
            if not params.is_file():
                parser.error('params file missing')
            cmd += ['-params-file', str(params)]
        if workflow.suffix == '.sh':
            cmd += ['--arh_script', str(workflow), '--arh_project', str(root)]
        else:
            cmd += ['--outdir', str(iteration / 'results' / name)]
        # Workflows call the iteration's scripts by path, and those scripts are not Nextflow inputs:
        # without their hashes two receipts of runs that did different things can look identical.
        scripts = iteration / 'scripts'
        script_sha256 = ({str(p.relative_to(root)): sha(p) for p in sorted(scripts.rglob('*'))
                          if p.is_file() and '__pycache__' not in p.parts} if scripts.is_dir() else {})
        record = dict(engine='nextflow', version=version, executable_sha256=expected, environment_prefix=prefix,
                      workflow=str(workflow.relative_to(root)), workflow_sha256=sha(workflow),
                      script_sha256=script_sha256,
                      predeclaration_sha256=sha(iteration / 'README.md'),
                      params_sha256=sha(args.params) if args.params else None,
                      config_sha256={str(p): sha(p) for p in map(Path, configs)},
                      executor=executor, runtime=runtime, image=image or None, image_sha256=sha(image),
                      driver_package_sha256=sha(installed[0]),
                      environment_locks={p.name: sha(p) for p in (root / '.arh').glob('*explicit.lock')},
                      resume=args.resume, command=cmd, started=datetime.now(timezone.utc).isoformat())
        receipt = attempt / 'run.json'
        receipt.write_text(json.dumps(record, indent=2) + '\n')
        received = []
        with (attempt / 'console.log').open('w') as output:
            proc = subprocess.Popen(cmd, cwd=engine, env=env, stdout=output, stderr=subprocess.STDOUT)

            def forward(signum, frame):
                # Stopping the wrapper must stop Nextflow (which cancels its jobs) and still reach
                # the `finally` that releases the launch lock. A second signal escalates.
                received.append(signal.Signals(signum))
                proc.send_signal(signal.SIGTERM if len(received) == 1 else signal.SIGKILL)

            handlers = {s: signal.signal(s, forward) for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
            try:
                returncode = proc.wait()
            finally:
                for s, handler in handlers.items():
                    signal.signal(s, handler)
        record.update(exit_code=returncode, finished=datetime.now(timezone.utc).isoformat())
        if received:
            record['signal'] = received[0].name
            returncode = returncode or 128 + received[0].value
        receipt.write_text(json.dumps(record, indent=2) + '\n')
        print(attempt)
        print(f'arh: Nextflow exit={record["exit_code"]}; trace and logs: {attempt}'
              + (f'; stopped by {record["signal"]}' if received else ''), file=sys.stderr)
        if returncode:
            print('\n'.join((attempt / 'console.log').read_text().splitlines()[-20:]), file=sys.stderr)
        return returncode
    finally:
        release(lock)


if __name__ == '__main__':
    sys.exit(run())
