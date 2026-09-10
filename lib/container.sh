#!/usr/bin/env bash
# Container abstraction. Selected by `container_runtime` in .dl/config/site.md.
# Supported: apptainer | singularity | docker | none

dl_ctr_backend() { dl_config_get "$DL_SITE" container_runtime none; }

# dl_ctr_image <name> -> resolved path/URI for an image declared in site.md as
# `image_<name> = ...`, or the argument itself if it is already a path/URI.
dl_ctr_image() {
  local key="$1" v
  v=$(dl_config_get "$DL_SITE" "image_$key" "")
  [ -n "$v" ] || v="$key"
  case "$v" in
    /*|docker://*|*://*) printf '%s' "$v" ;;
    *) local base; base=$(dl_config_get "$DL_SITE" image_dir "$DL_ROOT/.dl/images")
       case "$base" in /*) ;; *) base="$DL_ROOT/$base" ;; esac
       printf '%s/%s' "$base" "$v" ;;
  esac
}

# Verify content identity without launching a container (also used by Nextflow).
dl_ctr_verify() {
  local key="$1" image="$2" expected actual backend
  backend=$(dl_ctr_backend)
  if [ "$backend" != none ]; then
    [ -n "$(dl_config_get "$DL_SITE" "image_$key" "")" ] || dl_die "image must be declared in site.md: $key"
    case "$image" in
      *://*)
        printf '%s' "$image" | grep -Eq '@sha256:[a-f0-9]{64}$' || dl_die "remote image requires @sha256 digest"
        ;;
      *)
        expected=$(dl_config_get "$DL_SITE" "image_${key}_sha256" "")
        [ -n "$expected" ] || dl_die "declare image_${key}_sha256 in site.md"
        [ -f "$image" ] || dl_die "image does not exist: $image"
        actual=$(dl_sha256 "$image")
        [ "$actual" = "$expected" ] || dl_die "image digest mismatch: $key"
        ;;
    esac
  fi
}

# dl_ctr_run <image-key-or-path> <cmd...>
dl_ctr_run() {
  local key="$1" image
  image=$(dl_ctr_image "$key"); shift
  local backend; backend=$(dl_ctr_backend)
  dl_ctr_verify "$key" "$image"
  local binds ro_binds b args=()
  ro_binds=$(dl_config_get "$DL_PROJ" immutable_inputs "")
  binds=$(dl_config_get "$DL_SITE" extra_binds "")

  case "$backend" in
    apptainer|singularity)
      args=(exec --cleanenv --containall --env LC_ALL=C)
      for b in $ro_binds; do [ -n "$b" ] && args+=(--bind "$b:$b:ro"); done
      for b in $binds;    do [ -n "$b" ] && args+=(--bind "$b"); done
      args+=(--bind "$DL_ROOT:$DL_ROOT" --pwd "$DL_ROOT" "$image")
      "$backend" "${args[@]}" "$@"
      ;;
    docker)
      image=${image#docker://}
      args=(run --rm -u "$(id -u):$(id -g)" -e LC_ALL=C)
      for b in $ro_binds; do [ -n "$b" ] && args+=(-v "$b:$b:ro"); done
      for b in $binds;    do [ -n "$b" ] && args+=(-v "$b"); done
      args+=(-v "$DL_ROOT:$DL_ROOT" -w "$DL_ROOT" "$image")
      docker "${args[@]}" "$@"
      ;;
    none)
      dl_warn "SMOKE TEST: host execution is unpinned and has no read-only container binds"
      "$@"
      ;;
    *) dl_die "unknown container_runtime: $backend" ;;
  esac
}
