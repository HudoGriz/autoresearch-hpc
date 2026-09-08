#!/usr/bin/env bash
# discovery-loop test suite. Exercises the whole loop end to end with a generic
# toy study — no domain tools, no cluster, no network.
#
#   test/run_tests.sh            run in a temp dir, clean up
#   KEEP=1 test/run_tests.sh     keep the scratch project for inspection
set -uo pipefail

DL_HOME=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export DL_HOME PATH="$DL_HOME/bin:$PATH"

WORK=$(mktemp -d "${TMPDIR:-/tmp}/dl-test.XXXXXX")
PROJ="$WORK/toy"
pass=0; fail=0

ok()   { pass=$((pass+1)); printf '  ok %2d — %s\n' "$((pass+fail))" "$1"; }
no()   { fail=$((fail+1)); printf 'not ok %2d — %s\n' "$((pass+fail))" "$1"
         [ -n "${2-}" ] && printf '     %s\n' "$2"; }
# check <desc> <expect-exit 0|1> <cmd...>
check() {
  local desc="$1" want="$2"; shift 2
  local out rc
  out=$("$@" 2>&1); rc=$?
  if { [ "$want" = 0 ] && [ "$rc" = 0 ]; } || { [ "$want" != 0 ] && [ "$rc" != 0 ]; }
  then ok "$desc"; else no "$desc" "exit $rc (wanted ${want}); output: $(printf '%s' "$out" | tail -3 | tr '\n' ' ')"; fi
}
grep_ok() { # <desc> <pattern> <file>
  if grep -qE "$2" "$3" 2>/dev/null; then ok "$1"; else no "$1" "pattern '$2' not in $3"; fi
}

cleanup() { [ -n "${KEEP:-}" ] && printf '\nkept: %s\n' "$WORK" || rm -rf "$WORK"; }
trap cleanup EXIT

printf '# discovery-loop test suite\n# scratch: %s\n\n' "$WORK"

# --- 1. framework --------------------------------------------------------
printf '# framework\n'
check "dl prints usage"                    0 dl --help
check "dl rejects an unknown command"      1 dl nonsense
check "dl doctor runs outside a project"   0 env DL_PROJECT="$WORK" dl doctor
for f in "$DL_HOME"/bin/dl*; do
  bash -n "$f" 2>/dev/null && ok "syntax: $(basename "$f")" || no "syntax: $(basename "$f")"
done
python3 -c "
import json,glob,sys
for f in sorted(glob.glob('$DL_HOME/schema/*.json')): json.load(open(f))
" && ok "schemas are valid JSON" || no "schemas are valid JSON"

# --- 2. init -------------------------------------------------------------
printf '\n# init\n'
check "dl init creates a project"          0 dl init "$PROJ"
check "dl init refuses to re-init"         1 dl init "$PROJ"
for p in .dl/config/site.md .dl/config/project.md .dl/config/harnesses.md \
         PROGRESS.md AGENTS.md GOTCHAS.md rules/null-is-upper-bound.md .dl/registry.tsv; do
  [ -e "$PROJ/$p" ] && ok "created $p" || no "created $p"
done
[ -L "$PROJ/CLAUDE.md" ] && ok "CLAUDE.md symlinks to AGENTS.md" || no "CLAUDE.md symlinks to AGENTS.md"

cd "$PROJ"
check "dl doctor passes on a fresh project" 0 dl doctor

# --- 3. claiming ---------------------------------------------------------
printf '\n# claiming\n'
n=$(dl claim -t "Does the toy signal exceed its null?" -a tester 2>/dev/null)
[ "$n" = 1 ] && ok "first claim returns 1" || no "first claim returns 1" "got '$n'"
[ -f "iterations/iteration1/CLAIM.json" ] && ok "CLAIM.json written" || no "CLAIM.json written"
python3 -c "import json;json.load(open('iterations/iteration1/CLAIM.json'))" 2>/dev/null \
  && ok "CLAIM.json is valid JSON" || no "CLAIM.json is valid JSON"
grep_ok "registry row appended" "^1[[:space:]]+tester" .dl/registry.tsv

# Concurrent claims must not collide. This is the failure the protocol exists
# to prevent: two agents creating the same iteration directory.
for i in 1 2 3 4 5 6; do ( dl claim -t "concurrent $i" -a "agent$i" >"$WORK/c$i" 2>/dev/null ) & done
wait
got=$(cat "$WORK"/c[1-6] 2>/dev/null | sort -n | tr '\n' ' ')
uniq_n=$(cat "$WORK"/c[1-6] 2>/dev/null | sort -n | uniq | wc -l)
[ "$uniq_n" = 6 ] && ok "6 concurrent claims get 6 distinct numbers" \
  || no "6 concurrent claims get 6 distinct numbers" "got: $got"
dirs=$(ls -1d iterations/iteration* | wc -l)
[ "$dirs" = 7 ] && ok "7 iteration directories exist" || no "7 iteration directories exist" "got $dirs"

# --- 4. pre-declaration gate --------------------------------------------
printf '\n# pre-declaration gate\n'
check "dl new scaffolds the README"         0 dl new -n 1
check "dl new refuses to overwrite"         1 dl new -n 1
check "gate rejects an unfilled template"   1 dl gate predeclare -n 1
if [ -f iterations/iteration1/PREDECLARATION.sha256 ]
then no "a failed gate freezes nothing"; else ok "a failed gate freezes nothing"; fi

cat > iterations/iteration1/README.md <<'EOF'
# Iteration 1 — Does the toy signal exceed its null?

**Status: PRE-DECLARED. Written BEFORE any result exists.**

## 1. Question
Does the mean of series A exceed the mean of series B by more than chance?

## 2. Estimand
The difference in means, A minus B, in raw units, over all 100 paired draws.

## 3. Instrument
python3 stdlib only, seed 20260908, sorted inputs, no container required.

## 4. Acceptance criteria
Both series carry exactly 100 records; no missing values; row counts reconcile.

## 5. Negative controls
Series B against a label-permuted copy of itself; expected to be null.

## 6. Detection limit
0.20 raw units at 80% power for n=100; smaller true differences are not
resolvable by this design and are reported as within the detection limit.

## 7. Prediction
The difference will be null and the negative control will not fire.

## 8. Limits of the conclusion
Results are associated with the grouping variable and cannot separate it from
draw order. Any null is an upper bound at the stated detection limit. Nothing
here is orthogonally validated, so every result is a candidate.
EOF
check "gate accepts a complete pre-declaration" 0 dl gate predeclare -n 1
[ -f iterations/iteration1/PREDECLARATION.sha256 ] && ok "hash frozen" || no "hash frozen"
frozen=$(head -1 iterations/iteration1/PREDECLARATION.sha256)

# A pre-declaration written after the results is not a pre-declaration.
dl new -n 2 >/dev/null 2>&1
mkdir -p iterations/iteration2/results && echo "answer" > iterations/iteration2/results/out.tsv
check "gate rejects pre-declaration after results exist" 1 dl gate predeclare -n 2

# --- 5. running work -----------------------------------------------------
printf '\n# running work\n'
mkdir -p iterations/iteration1/scripts iterations/iteration1/results/report
cat > iterations/iteration1/scripts/it1_01_toy.py <<'EOF'
"""Generic toy analysis: paired difference in means with a permutation null."""
import random, statistics, pathlib, sys
random.seed(20260908)
n = 100
a = [random.gauss(0, 1) for _ in range(n)]
b = [random.gauss(0, 1) for _ in range(n)]
assert len(a) == len(b) == n, "row counts must reconcile"
obs = statistics.mean(a) - statistics.mean(b)
pool = a + b
null = []
for _ in range(2000):
    random.shuffle(pool)
    null.append(statistics.mean(pool[:n]) - statistics.mean(pool[n:]))
p = sum(1 for x in null if abs(x) >= abs(obs)) / len(null)
out = pathlib.Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(f"metric\tvalue\nn\t{n}\ndiff_means\t{obs:.6f}\nperm_p\t{p:.4f}\n")
print(f"n={n} diff={obs:.6f} p={p:.4f}")
EOF
cat > iterations/iteration1/scripts/it1_01_run.sh <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$PROJ"
python3 iterations/iteration1/scripts/it1_01_toy.py iterations/iteration1/results/it1_01_result.tsv
EOF
chmod +x iterations/iteration1/scripts/it1_01_run.sh

jid=$(dl submit iterations/iteration1/scripts/it1_01_run.sh -n it1_01 \
        -l iterations/iteration1/logs -w 2>/dev/null)
[ -n "$jid" ] && ok "dl submit returned a job id ($jid)" || no "dl submit returned a job id"
for _ in $(seq 1 50); do [ -s iterations/iteration1/results/it1_01_result.tsv ] && break; sleep 0.2; done
[ -s iterations/iteration1/results/it1_01_result.tsv ] \
  && ok "job produced results" || no "job produced results"
grep_ok "results reconcile to n=100" "^n[[:space:]]+100" iterations/iteration1/results/it1_01_result.tsv
check "dl run works with container_runtime=none" 0 dl run any -- true

# --- 6. guard ------------------------------------------------------------
printf '\n# immutable-input guard\n'
check "guard allows a path inside the project" 0 dl guard "$PROJ/iterations/iteration1/results/x"
check "guard refuses a path outside"           1 dl guard /etc/passwd
python3 - <<EOF
import re,pathlib
p=pathlib.Path(".dl/config/project.md"); s=p.read_text()
p.write_text(s.replace("immutable_inputs  =", "immutable_inputs  = $WORK/raw"))
EOF
mkdir -p "$WORK/raw"
check "guard refuses a declared immutable input" 1 dl guard "$WORK/raw/x"

# --- 7. standing rules ---------------------------------------------------
printf '\n# standing rules\n'
cat > "$WORK/bad_report.md" <<'EOF'
# Report
The exposure causes the outcome. There is no effect in the control arm.
EOF
check "rules reject causal language and a bare null" 1 dl gate rules "$WORK/bad_report.md"
cat > "$WORK/good_report.md" <<'EOF'
# Report
The exposure is associated with the outcome; this design cannot separate it from
draw order and the claim is not causal. The control arm is null: we cannot
exclude effects below the stated detection limit of 0.20 units, which is the
upper bound this design supports. Negative controls did not fire.
EOF
check "rules accept a properly qualified report" 0 dl gate rules "$WORK/good_report.md"

# --- 8. results gate & tamper detection ---------------------------------
printf '\n# results gate\n'
check "results gate fails with no report" 1 dl gate results -n 1
cat > iterations/iteration1/results/report/iteration1_report.md <<'EOF'
# Iteration 1 report

## Headline
The difference in means is associated with nothing detectable: the observed
difference is null, and we cannot exclude effects below the detection limit of
0.20 raw units, which is the upper bound this design supports.

## Negative controls
The label-permuted control did not fire, as pre-declared.

## Result
diff_means and perm_p are in results/it1_01_result.tsv. n = 100, reconciled.

## Was the prediction right?
Yes — §7 predicted a null with a quiet negative control.

## What this does not establish
Association only; the design cannot separate grouping from draw order. The
result is a candidate, not a validated finding.
EOF
check "results gate still fails with no cross-check" 1 dl gate results -n 1
cat > "iterations/iteration1/CROSSCHECK_adversary_codex_20260908T000000Z.md" <<'EOF'
# Cross-check — iteration 1
VERDICT: SOUND
No findings; the null is reported as an upper bound.
EOF
check "results gate passes when cross-checked" 0 dl gate results -n 1

# The core mechanism: editing the pre-declaration after results must be caught.
printf '\n' >> iterations/iteration1/README.md
echo "## 9. Added after the fact" >> iterations/iteration1/README.md
check "tampering with a frozen pre-declaration is caught" 1 dl gate results -n 1
grep_ok "tamper report names the file" "README.md CHANGED" <(dl gate results -n 1 2>&1)
python3 - <<'EOF'
import pathlib
p = pathlib.Path("iterations/iteration1/README.md")
lines = p.read_text().splitlines(True)
p.write_text("".join(lines[:-2]))
EOF
now=$(sha256sum iterations/iteration1/README.md | awk '{print $1}')
[ "$now" = "$frozen" ] && ok "restored README matches the frozen hash" \
  || no "restored README matches the frozen hash"
check "results gate passes again after restore" 0 dl gate results -n 1

# --- 9. cross-harness dispatch ------------------------------------------
printf '\n# cross-harness dispatch\n'
check "dl ask --dry-run composes a prompt"    0 dl ask --role adversary -n 1 --dry-run
out=$(dl ask --role adversary -n 1 --dry-run 2>&1)
printf '%s' "$out" | grep -q "^# Role: adversary" \
  && ok "prompt carries the role instructions" || no "prompt carries the role instructions"
printf '%s' "$out" | grep -q "PRE-DECLARED" \
  && ok "prompt carries the pre-declaration" || no "prompt carries the pre-declaration"
check "dl ask rejects an unknown role"        1 dl ask --role nonsense -n 1 --dry-run
python3 - <<'EOF'
import pathlib
p = pathlib.Path(".dl/config/harnesses.md")
p.write_text(p.read_text().replace("verifier   = codex", "verifier   = claude"))
EOF
check "same-family verification is refused"   1 dl ask --role adversary -n 1 --dry-run
check "--same-family overrides it"            0 dl ask --role adversary -n 1 --dry-run --same-family
python3 - <<'EOF'
import pathlib
p = pathlib.Path(".dl/config/harnesses.md")
p.write_text(p.read_text().replace("verifier   = claude", "verifier   = codex"))
EOF

# --- 10. ledger ----------------------------------------------------------
printf '\n# ledger\n'
check "dl ledger render"  0 dl ledger render
grep_ok "status table rendered" "^\| 1 \| tester" PROGRESS.md
grep_ok "frozen state shown"    "frozen" PROGRESS.md
check "dl ledger render is idempotent" 0 dl ledger render
[ "$(grep -c 'dl:status:begin' PROGRESS.md)" = 1 ] \
  && ok "render does not duplicate the table" || no "render does not duplicate the table"
check "dl status runs" 0 dl status
grep_ok "status shows the cross-check" "yes" <(dl status 2>&1)

python3 - <<'EOF'
import pathlib
p = pathlib.Path("iterations/iteration1/README.md")
p.write_text(p.read_text() + "\ntampered\n")
EOF
check "ledger check catches an altered pre-declaration" 1 dl ledger check
grep_ok "ledger names the altered iteration" "iteration 1 — README.md altered" <(dl ledger check 2>&1)

# --- 11. config ----------------------------------------------------------
printf '\n# configuration\n'
python3 - <<'EOF'
import pathlib
p = pathlib.Path(".dl/config/site.md")
p.write_text(p.read_text().replace("scheduler         = local", "scheduler         = nonesuch"))
EOF
check "doctor fails on an unknown scheduler backend" 1 dl doctor
python3 - <<'EOF'
import pathlib
p = pathlib.Path(".dl/config/site.md")
p.write_text(p.read_text().replace("scheduler         = nonesuch", "scheduler         = local"))
EOF
check "doctor passes when the config matches the machine" 0 dl doctor

# --- 12. harness install -------------------------------------------------
printf '\n# harness install\n'
check "harness/install.sh runs" 0 "$DL_HOME/harness/install.sh" "$PROJ"
for p in .claude/skills/iterate/SKILL.md .codex/config.toml opencode.json; do
  [ -e "$PROJ/$p" ] && ok "installed $p" || no "installed $p"
done

printf '\n1..%d\n' "$((pass+fail))"
printf '# passed %d, failed %d\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
