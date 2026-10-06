// `arh doctor --smoke`: one task through the site's real executor and container, checking the
// boundary a study relies on rather than only that the binaries exist. Each line is "ok" or "FAIL".
params.outdir = 'results'
params.immutable = []
params.sealed = []
params.gpu = false

def shellQuote(value) { "'" + value.toString().replace("'", "'\"'\"'") + "'" }

process SMOKE {
    cache false

    output:
    stdout

    script:
    def immutable = params.immutable.collect { shellQuote(it) }.join(' ')
    def sealed = params.sealed.collect { shellQuote(it) }.join(' ')
    """
    if command -v python3 >/dev/null; then echo "ok   task environment on PATH: \$(command -v python3)"
    else echo "FAIL no python3 on PATH inside the task"; fi
    if mkdir -p ${shellQuote(params.outdir)} && echo ok > ${shellQuote(params.outdir)}/smoke.txt; then
      echo "ok   the project is writable from the task"
    else echo "FAIL the task cannot write under the project"; fi
    for d in ${immutable}; do
      if [ ! -e "\$d" ]; then echo "FAIL immutable input not visible in the task: \$d"
      elif [ -d "\$d" ] && touch "\$d/.arh-smoke-write" 2>/dev/null; then rm -f "\$d/.arh-smoke-write"; echo "FAIL immutable input is writable: \$d"
      elif [ ! -d "\$d" ] && [ -w "\$d" ]; then echo "FAIL immutable input is writable: \$d"
      else echo "ok   immutable input visible and read-only: \$d"; fi
    done
    for s in ${sealed}; do
      if { [ -d "\$s" ] && [ -n "\$(ls -A "\$s" 2>/dev/null)" ]; } || { [ -f "\$s" ] && [ -s "\$s" ]; }; then
        echo "FAIL sealed input readable without a freeze: \$s"
      else echo "ok   sealed input hidden: \$s"; fi
    done
    """
}

process SMOKE_GPU {
    label 'gpu'
    cache false

    output:
    stdout

    script:
    """
    if nvidia-smi -L >/dev/null 2>&1; then echo "ok   GPU visible: \$(nvidia-smi -L | head -1)"
    else echo "FAIL no GPU visible in a task labelled gpu"; fi
    """
}

workflow {
    SMOKE() | view
    if (params.gpu) {
        SMOKE_GPU() | view
    }
}
