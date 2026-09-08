#!/usr/bin/env bash
# Scheduler abstraction. Selected by `scheduler` in .dl/config/site.md.
# Supported: slurm | pbs | local

dl_sched_backend() { dl_config_get "$DL_SITE" scheduler local; }

# dl_sched_submit <script> <jobname> <logdir> -> prints job id on stdout
dl_sched_submit() {
  local script="$1" name="$2" logdir="$3" backend jid
  backend=$(dl_sched_backend)
  mkdir -p "$logdir"
  case "$backend" in
    slurm)
      local part acct time cpus mem extra
      part=$(dl_config_get  "$DL_SITE" slurm_partition "")
      acct=$(dl_config_get  "$DL_SITE" slurm_account "")
      time=$(dl_config_get  "$DL_SITE" slurm_time "01:00:00")
      cpus=$(dl_config_get  "$DL_SITE" slurm_cpus "1")
      mem=$(dl_config_get   "$DL_SITE" slurm_mem "4G")
      extra=$(dl_config_get "$DL_SITE" slurm_extra "")
      set -- --job-name="$name" --time="$time" --cpus-per-task="$cpus" --mem="$mem" \
             --output="$logdir/${name}_%j.out" --error="$logdir/${name}_%j.err"
      [ -n "$part" ] && set -- "$@" --partition="$part"
      [ -n "$acct" ] && set -- "$@" --account="$acct"
      # shellcheck disable=SC2086
      jid=$(sbatch --parsable "$@" $extra "$script") || dl_die "sbatch failed"
      printf '%s' "$jid"
      ;;
    pbs)
      local queue time
      queue=$(dl_config_get "$DL_SITE" pbs_queue "")
      time=$(dl_config_get  "$DL_SITE" slurm_time "01:00:00")
      set -- -N "$name" -l "walltime=$time" -o "$logdir/${name}.out" -e "$logdir/${name}.err"
      [ -n "$queue" ] && set -- "$@" -q "$queue"
      jid=$(qsub "$@" "$script") || dl_die "qsub failed"
      printf '%s' "$jid"
      ;;
    local)
      # Run detached; the pid is the job id.
      nohup bash "$script" >"$logdir/${name}.out" 2>"$logdir/${name}.err" &
      printf '%s' "$!"
      ;;
    *) dl_die "unknown scheduler backend: $backend (set 'scheduler' in site.md)" ;;
  esac
}

# dl_sched_status <jobid> -> RUNNING | DONE | UNKNOWN
dl_sched_status() {
  local jid="$1" backend; backend=$(dl_sched_backend)
  case "$backend" in
    slurm) squeue -h -j "$jid" -o %T 2>/dev/null | grep -q . && echo RUNNING || echo DONE ;;
    pbs)   qstat  "$jid" >/dev/null 2>&1 && echo RUNNING || echo DONE ;;
    local) kill -0 "$jid" 2>/dev/null && echo RUNNING || echo DONE ;;
    *)     echo UNKNOWN ;;
  esac
}

# dl_sched_wait <jobid> [poll_seconds]
dl_sched_wait() {
  local jid="$1" poll="${2:-10}"
  while [ "$(dl_sched_status "$jid")" = RUNNING ]; do sleep "$poll"; done
}
