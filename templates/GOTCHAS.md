# Silent failure modes

Failures that produce plausible output. Each entry gets an **assertion** — a
command that fails loudly when the mode recurs — so the knowledge lives in the
pipeline rather than in someone's memory.

Add an entry the first time a failure costs you a day. The format:

## <short name>

**Discovered:** <date, iteration>
**Symptom:** <what it looks like when it happens — emphasise why it looks fine>
**Cause:** <the actual mechanism>
**Assertion:**

```bash
# fails loudly if the mode has recurred
```

---

## Example — a tool that silently drops the tags you need

**Discovered:** (example entry; delete when you add your own)
**Symptom:** The output file looks normal, the downstream tool runs clean, and
every position is reported as negative. Nothing errors.
**Cause:** A converter dropped an optional tag because a flag was missing. The
absence is indistinguishable from a true negative in every downstream view.
**Assertion:**

```bash
test "$(samtools view aln.bam | grep -c 'MM:Z:')" -gt 0 \
  || { echo 'FATAL: base-modification tags absent'; exit 1; }
```

**The general lesson.** Any step that *can* drop data silently gets an assertion
that the data survived. "The tool ran without error" is not evidence.
