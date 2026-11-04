"""Small file/config helpers for deterministic AutoResearch HPC adapters."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


def config(path):
    """Read key/value pairs from an ``arh-config`` Markdown block."""
    values, inside = {}, False
    if not Path(path).is_file():
        return values
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line.startswith('```'):
            inside = line[3:].strip() == 'arh-config'
        elif inside and not line.startswith('#') and '=' in line:
            key, value = (part.strip() for part in line.split('=', 1))
            values.setdefault(key, value)
    return values


def iteration_config(directory, project_harn):
    """The harness configuration iteration DIRECTORY runs under: its own harnesses.md, where present,
    over the project's (arh_iter_harn in common.sh writes the same as a file for the shell)."""
    values = config(Path(directory) / 'harnesses.md')
    for key, value in config(project_harn).items():
        values.setdefault(key, value)
    return values


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def cache_path(directory, kind):
    """.arh/cache/KIND/<name>-<key>.json of the project holding DIRECTORY; None outside a project or with
    ARH_NO_HASH_CACHE=1."""
    directory = Path(directory).resolve()
    if os.environ.get('ARH_NO_HASH_CACHE'):
        return None
    for parent in directory.parents:
        if (parent / '.arh').is_dir():
            key = hashlib.sha256(str(directory).encode()).hexdigest()[:16]
            return parent / '.arh/cache' / kind / f'{directory.name}-{key}.json'
    return None


def cached_digests(files, cache_file):
    """{key: SHA-256} of FILES ({key: path}, existing files only). Each hash is kept in CACHE_FILE with
    the file's size, mtime, ctime and inode and reused only while all four match: ctime cannot be set
    by a user (even `touch` moves it), so any write is hashed again (field feedback #102, #136)."""
    try:
        cached = json.loads(cache_file.read_text()) if cache_file else {}
    except (OSError, ValueError):
        cached = {}
    out, fresh = {}, {}
    for key, path in files.items():
        st = Path(path).stat()
        sig = [st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino]
        hit = cached.get(key)
        out[key] = hit[4] if isinstance(hit, list) and hit[:4] == sig else sha256_file(path)
        fresh[key] = sig + [out[key]]
    if cache_file and fresh != cached:
        try:                     # a lost race or an unwritable cache only costs a re-hash next time
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile('w', dir=cache_file.parent, delete=False) as tmp:
                json.dump(fresh, tmp)
            os.replace(tmp.name, cache_file)
        except OSError:
            pass
    return out


def notify(root, event, iteration, message):
    """Tell the operator: run site.md's notify command (mail, ntfy, a chat webhook) with ARH_EVENT,
    ARH_ITERATION and ARH_MESSAGE set. Best effort: a failing command never fails the caller."""
    cmd = config(Path(root) / '.arh/config/site.md').get('notify', '')
    if not cmd:
        return
    env = dict(os.environ, ARH_EVENT=event, ARH_ITERATION=str(iteration), ARH_MESSAGE=message, ARH_ROOT=str(root))
    try:
        subprocess.run(cmd, shell=True, env=env, cwd=root, stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        pass


def guard(path, root, immutable=()):
    path, root = Path(path).resolve(), Path(root).resolve()
    if path != root and root not in path.parents:
        raise ValueError('write outside project: ' + str(path))
    for item in immutable:
        source = Path(item)
        source = (source if source.is_absolute() else root / source).resolve()
        if path == source or source in path.parents:
            raise ValueError('immutable path: ' + str(path))
    return path


def share(path):
    """Give a file or directory made by mkdtemp/mkstemp (0700/0600) the mode the umask gives anything
    else, keeping a directory's setgid bit. In a project shared between two accounts through a group,
    private run directories hid run.json and nextflow.log from the other account (field feedback #88)."""
    path = Path(path)
    mask = os.umask(0)
    os.umask(mask)
    if path.is_dir():
        os.chmod(path, (0o777 & ~mask) | (path.stat().st_mode & stat.S_ISGID))
    else:
        os.chmod(path, 0o666 & ~mask)
    return path


def knowledge(root):
    """{label: path} of the files that carry what outlives a session: the study's directives and
    gotchas, and the site's shared gotchas when site.md names them. Missing files are left out."""
    root = Path(root)
    # The label stays DIRECTIVES.md in records; `directives =` in project.md can name another file.
    directives = config(root / '.arh/config/project.md').get('directives') or 'DIRECTIVES.md'
    found = {name: root / path for name, path in (('DIRECTIVES.md', directives), ('GOTCHAS.md', 'GOTCHAS.md'))
             if (root / path).is_file()}
    shared = config(root / '.arh/config/site.md').get('site_gotchas', '')
    if shared and Path(shared).is_file():
        found['site_gotchas'] = Path(shared)
    return found


def knowledge_hashes(root):
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in knowledge(root).items()}


if __name__ == '__main__':
    if sys.argv[1] == 'knowledge-hashes':     # knowledge-hashes ROOT: JSON object for a record
        print(json.dumps(knowledge_hashes(sys.argv[2]), sort_keys=True))
    else:
        sys.exit(f'unknown command: {sys.argv[1]}')
