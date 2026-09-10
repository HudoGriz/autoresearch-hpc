"""Small file/config helpers for deterministic adapters (no agent framework)."""
from pathlib import Path


def config(path):
    values, inside = {}, False
    if not Path(path).is_file():
        return values
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line.startswith('```'):
            inside = line[3:].strip() == 'dl-config'
        elif inside and not line.startswith('#') and '=' in line:
            key, value = (part.strip() for part in line.split('=', 1))
            values.setdefault(key, value)
    return values


def guard(path, root, immutable=()):
    path, root = Path(path).resolve(), Path(root).resolve()
    if root not in path.parents:
        raise ValueError('write outside project: ' + str(path))
    for item in immutable:
        source = Path(item)
        source = (source if source.is_absolute() else root / source).resolve()
        if path == source or source in path.parents:
            raise ValueError('immutable path: ' + str(path))
    return path
