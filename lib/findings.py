"""Each finding of each eligible review, and whether REVIEW_RESPONSE.md answers it (stdlib only).

PROTOCOL 6.5 says findings MUST be evaluated on their merits and rejections recorded with reasons,
but nothing checked that they were: a field study's results gate passed with no response file at
all, and the reviews' value was precisely in their specific findings (field feedback #12, #16).
`arh ask` asks the reviewer to number findings F1, F2, ...; this reads them back and looks, in
REVIEW_RESPONSE.md, for each id beside a decision (accepted, rejected, fixed, deferred, ...).
With several reviews, a response section whose heading names a review's file answers that review;
otherwise the whole file is searched.

  findings.py check DIR MODE      MODE require|warn|off; prints a checklist; exit 1 if MODE is require
                                  and a numbered finding is unanswered
  findings.py skeleton DIR        a REVIEW_RESPONSE.md skeleton listing every numbered finding
"""
from pathlib import Path
import re
import sys

from harness import valid_records

FINDING = re.compile(r'^\s*(?:[-*+]\s+|\d+\.\s+)?(?:\*\*|__)?\[?(F\d{1,3})\]?(?:\*\*|__)?\s*[:.)\]–—-]\s*(?:\*\*|__)?\s*(.+)$')
DECISION = re.compile(r"\b(accept(?:ed)?|reject(?:ed)?|fix(?:ed)?|addressed|deferred|disput(?:e|ed)|declined|"
                      r"acknowledged|not applicable|n/a|won't fix|verified|new iteration|partly accepted)\b", re.I)


def findings(review):
    """[(id, summary)] in order of first appearance, after the VERDICT line."""
    text = Path(review).read_text(errors='replace')
    body = text.split('VERDICT:', 1)[1] if 'VERDICT:' in text else text
    seen, out = set(), []
    for line in body.splitlines():
        match = FINDING.match(line)
        if match and match.group(1) not in seen:
            seen.add(match.group(1))
            out.append((match.group(1), match.group(2).strip()[:140]))
    return out


def scope(response, review):
    """The part of the response that answers REVIEW: its own section when sections name reviews."""
    sections = re.split(r'(?m)^(?=#{1,6} )', response)
    named = [s for s in sections if s.startswith('#') and 'CROSSCHECK_' in s.splitlines()[0]]
    if not named:
        return response
    stem = Path(review).name.removesuffix('.md')
    return '\n'.join(s for s in named if stem in s.splitlines()[0])


def decision(text, fid):
    for paragraph in re.split(r'\n\s*\n', text):
        for line in paragraph.splitlines():
            if re.search(rf'\b{fid}\b', line):
                found = DECISION.search(paragraph)
                if found:
                    return found.group(1).lower()
    return None


def checklist(directory):
    directory = Path(directory)
    response = directory / 'REVIEW_RESPONSE.md'
    text = response.read_text(errors='replace') if response.is_file() else None
    rows = []
    for review in valid_records(directory):
        for fid, summary in findings(review):
            rows.append((Path(review).name, fid, summary, decision(scope(text, review), fid) if text else None))
    return text is not None, rows


def check(directory, mode):
    if mode == 'off':
        return 0
    has_response, rows = checklist(directory)
    if not rows:
        if not has_response:
            print('  WARN no REVIEW_RESPONSE.md: record what was done about each finding (protocol 6.5)')
        return 0
    open_rows = [r for r in rows if not r[3]]
    level = 'FAIL' if mode == 'require' else 'WARN'
    if not has_response:
        print(f'  {level} no REVIEW_RESPONSE.md, and the review(s) list {len(rows)} numbered finding(s) '
              '(protocol 6.5); start from: arh gate results -n N --skeleton')
    else:
        answered = len(rows) - len(open_rows)
        print(f'  {"OK  " if not open_rows else level} review response answers {answered} of {len(rows)} numbered finding(s)')
    for review, fid, summary, found in rows:
        mark = f'answered ({found})' if found else 'UNANSWERED'
        print(f'       {review}: {fid} {mark}: {summary}')
    return 1 if open_rows and mode == 'require' else 0


def skeleton(directory):
    _, rows = checklist(directory)
    print('# Review response\n')
    print('Each finding: accepted, rejected, fixed, deferred or disputed, with the reason and what was done.')
    print('A finding that needs new computation goes through `arh verify`, not into this iteration.\n')
    current = None
    for review, fid, summary, _ in rows:
        if review != current:
            print(f'\n## {review}\n')
            current = review
        print(f'- {fid}: <accepted | rejected | fixed | deferred | disputed> — <reason>  ({summary})')
    if not rows:
        print('(the eligible reviews list no numbered findings)')


if __name__ == '__main__':
    if sys.argv[1] == 'check':
        sys.exit(check(sys.argv[2], sys.argv[3]))
    elif sys.argv[1] == 'skeleton':
        skeleton(sys.argv[2])
    else:
        sys.exit(f'unknown command: {sys.argv[1]}')
