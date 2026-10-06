"""Does every measured number in a report come from a file under results/? (stdlib only)

The foreign reviewer of a field study caught mis-transcribed numbers in a report (field feedback
#16); a 2026 benchmark of agents reproducing ML papers found the most common error was never checking
an implementation against the paper's numbers. This check is the cheap half of that: each number the
report states with a decimal point or a percent sign should equal, at the precision written, a value
in a results file (as is, or as a percentage of a fraction). Numbers that also appear in the frozen
pre-declaration are declared constants, not results, and version strings and the Cross-check section
are skipped. A number computed in the text (a difference of two others) shows up as unmatched; that
is a prompt to put it in a results file, not proof of an error.

  report_numbers.py check DIR REPORT     one line per unmatched number: LINE<TAB>NUMBER<TAB>context
"""
from pathlib import Path
import re
import sys

NUMBER = re.compile(r'(?<![\w.\-/])[-+−]?(\d+\.\d+|\d{1,3}(?:,\d{3})+\.\d+)(%?)(?![\w.]*\d)(?!\.\d)')
TOKEN = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')
TEXT_SUFFIXES = ('.json', '.tsv', '.csv', '.txt', '.md', '.tab', '.yaml', '.yml', '.log')
MAX_BYTES = 64 * 1024 * 1024
MAX_TOKENS = 2_000_000


def report_numbers(report, declared):
    """[(line, text as written, value, decimals, percent)] outside the Cross-check section."""
    out, skip = [], False
    for number, line in enumerate(Path(report).read_text(errors='replace').splitlines(), 1):
        if line.startswith('#'):
            skip = 'cross-check' in line.lower() or 'crosscheck' in line.lower()
            continue
        if skip:
            continue
        for match in NUMBER.finditer(line):
            digits = match.group(1).replace(',', '')
            if digits in declared:
                continue
            out.append((number, match.group(0), float(digits), len(digits.split('.')[1]), match.group(2) == '%'))
    return out


def results_values(directory, report):
    values, size = set(), 0
    for path in sorted((Path(directory) / 'results').rglob('*')):
        if not path.is_file() or path.resolve() == Path(report).resolve() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        size += path.stat().st_size
        if size > MAX_BYTES:
            break
        for token in TOKEN.findall(path.read_text(errors='replace')):
            try:
                values.add(abs(float(token)))
            except ValueError:
                continue
            if len(values) >= MAX_TOKENS:
                return values
    return values


def unmatched(directory, report):
    plan = Path(directory) / 'README.md'
    declared = set(m.group(1).replace(',', '') for m in NUMBER.finditer(plan.read_text(errors='replace'))) \
        if plan.is_file() else set()
    wanted = report_numbers(report, declared)
    if not wanted:
        return []
    values = results_values(directory, report)
    if not values:
        return [(line, text, 'no numeric results file under results/') for line, text, *_ in wanted[:1]]
    by_decimals = {}
    for decimals in {d for *_, d, _ in wanted}:
        fmt = '{:.%df}' % decimals
        by_decimals[decimals] = ({fmt.format(v) for v in values}, {fmt.format(v * 100) for v in values})
    lines = Path(report).read_text(errors='replace').splitlines()
    out = []
    for line, text, value, decimals, percent in wanted:
        plain, scaled = by_decimals[decimals]
        written = ('{:.%df}' % decimals).format(value)
        if written in plain or (percent and written in scaled) or (not percent and written in scaled and value > 1):
            continue
        out.append((line, text, lines[line - 1].strip()[:100]))
    return out


if __name__ == '__main__':
    if sys.argv[1] == 'check':
        for line, text, context in unmatched(sys.argv[2], sys.argv[3]):
            print(f'{line}\t{text}\t{context}')
    else:
        sys.exit(f'unknown command: {sys.argv[1]}')
