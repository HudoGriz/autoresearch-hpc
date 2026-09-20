"""Shell-free dispatch for optional external research generators (stdlib only)."""
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shlex
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone


PLACEHOLDERS = {"request", "output", "project", "iteration", "phase", "prompt"}
PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_-]*)\}")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def command(template, values):
    try:
        parts = shlex.split(template)
    except ValueError as exc:
        raise SystemExit(f"invalid generator command template: {exc}")
    if not parts:
        raise SystemExit("generator command is empty")
    unknown = sorted({name for part in parts for name in PLACEHOLDER.findall(part)} - PLACEHOLDERS)
    if unknown:
        raise SystemExit("unknown generator command placeholder(s): " + ", ".join(unknown))
    return [PLACEHOLDER.sub(lambda match: values[match.group(1)], part) for part in parts]


def stop(proc, grace=3):
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def version(template, cwd):
    if not template.strip():
        return None
    argv = command(template, {name: "" for name in PLACEHOLDERS})
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = result.stdout.strip() or result.stderr.strip()
    return text.splitlines()[0][:500] if text else None


def stream(proc, stdout_path, stderr_path, timeout, limit):
    selector = selectors.DefaultSelector()
    for pipe, name in ((proc.stdout, "stdout"), (proc.stderr, "stderr")):
        os.set_blocking(pipe.fileno(), False)
        selector.register(pipe, selectors.EVENT_READ, name)
    total = 0
    started = time.monotonic()
    timed_out = limited = False
    with open(stdout_path, "wb") as stdout, open(stderr_path, "wb") as stderr:
        files = {"stdout": stdout, "stderr": stderr}
        while selector.get_map():
            if time.monotonic() - started > timeout:
                timed_out = True
                stop(proc)
            events = selector.select(0.2)
            for key, _ in events:
                try:
                    chunk = os.read(key.fileobj.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                room = max(0, limit - total)
                files[key.data].write(chunk[:room])
                total += len(chunk)
                if total > limit and not limited:
                    limited = True
                    stop(proc)
            if proc.poll() is not None and not events:
                for key in list(selector.get_map().values()):
                    try:
                        chunk = os.read(key.fileobj.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if chunk:
                        room = max(0, limit - total)
                        files[key.data].write(chunk[:room])
                        total += len(chunk)
                    else:
                        selector.unregister(key.fileobj)
        if timed_out:
            stderr.write(b"\n[arh: generator timed out]\n")
        if limited:
            stderr.write(b"\n[arh: combined stdout/stderr limit exceeded]\n")
    proc.wait()
    return 124 if timed_out else (65 if limited else proc.returncode), total


def main():
    if len(sys.argv) not in (14, 15) or sys.argv[1] not in ("plan", "run"):
        raise SystemExit(
            "usage: evoke.py {plan|run} TEMPLATE VERSION_CMD REQUEST OUTPUT CWD "
            "TIMEOUT LIMIT TOOL PHASE ITERATION SOURCE CONFIG_SHA [KIND]"
        )
    (mode, template, version_cmd, request, output, cwd, timeout, limit,
     tool, phase, iteration, source, config_sha) = sys.argv[1:14]
    # An evocation calls a system outside the protocol; a delegation calls a harness the project
    # already configures. The runner is identical -- compose a request, run a command under a
    # timeout and an output cap, record what ran -- so only the record's vocabulary differs.
    kind = sys.argv[14] if len(sys.argv) > 14 else "evocation"
    request, output, cwd = Path(request), Path(output), Path(cwd)
    values = {
        "request": str(request),
        # A harness configured for `arh ask` writes {prompt}; a generator writes {request}. They
        # name the same composed file, so a delegation can reuse a harness command unchanged.
        "prompt": str(request),
        "output": str(output),
        "project": str(Path(os.environ.get("ARH_ROOT", cwd))),
        "iteration": iteration,
        "phase": phase,
    }
    argv = command(template, values)
    if mode == "plan":
        print(shlex.join(argv))
        return

    output.mkdir(parents=True, exist_ok=False)
    run_dir = output.parent
    record_path = run_dir / "run.json"
    started = utc_now()
    tool_version = version(version_cmd, cwd)
    labels = ({"schema": "arh-delegation-v1", "harness": tool, "role": phase, "family": source or None}
              if kind == "delegation" else
              {"schema": "arh-evocation-v1", "tool": tool, "phase": phase, "source": source or None})
    record = {
        **labels,
        "iteration": int(iteration),
        "command_template": template,
        "version_command": version_cmd or None,
        "tool_version": tool_version,
        "cwd": str(cwd),
        "request_sha256": digest(request),
        "config_sha256": config_sha,
        "started": started,
        "finished": None,
        "exit_code": None,
        "timed_out": False,
        "output_limited": False,
    }
    record_path.write_text(json.dumps(record, indent=2) + "\n")
    try:
        proc = subprocess.Popen(
            argv,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        rc, observed = stream(
            proc,
            run_dir / "response.md",
            run_dir / "stderr.log",
            float(timeout),
            int(limit),
        )
    except OSError as exc:
        rc, observed = 127, 0
        (run_dir / "response.md").write_text("")
        (run_dir / "stderr.log").write_text(f"arh: cannot start generator: {exc}\n")
    record.update(
        finished=utc_now(),
        exit_code=rc,
        timed_out=rc == 124,
        output_limited=rc == 65,
        observed_output_bytes=observed,
    )
    record_path.write_text(json.dumps(record, indent=2) + "\n")
    raise SystemExit(rc)


if __name__ == "__main__":
    main()

