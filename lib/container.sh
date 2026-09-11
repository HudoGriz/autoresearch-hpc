#!/usr/bin/env bash
# Container abstraction. Selected by `container_runtime` in .arh/config/site.md.
# Supported: apptainer | singularity | docker | none

arh_ctr_backend() { arh_config_get "$ARH_SITE" container_runtime none; }

# arh_ctr_image <name> -> resolved path/URI for an image declared in site.md as
# `image_<name> = ...`, or the argument itself if it is already a path/URI.
arh_ctr_image() {
  local key="$1" v
  v=$(arh_config_get "$ARH_SITE" "image_$key" "")
  [ -n "$v" ] || v="$key"
  case "$v" in
    /*|docker://*|*://*) printf '%s' "$v" ;;
    *) local base; base=$(arh_config_get "$ARH_SITE" image_dir "$ARH_ROOT/.arh/images")
       case "$base" in /*) ;; *) base="$ARH_ROOT/$base" ;; esac
       printf '%s/%s' "$base" "$v" ;;
  esac
}

# Verify content identity without launching a container (also used by Nextflow).
arh_ctr_verify() {
  local key="$1" image="$2" expected actual backend
  backend=$(arh_ctr_backend)
  if [ "$backend" != none ]; then
    [ -n "$(arh_config_get "$ARH_SITE" "image_$key" "")" ] || arh_die "image must be declared in site.md: $key"
    case "$image" in
      *://*)
        printf '%s' "$image" | grep -Eq '@sha256:[a-f0-9]{64}$' || arh_die "remote image requires @sha256 digest"
        ;;
      *)
        expected=$(arh_config_get "$ARH_SITE" "image_${key}_sha256" "")
        [ -n "$expected" ] || arh_die "declare image_${key}_sha256 in site.md"
        [ -f "$image" ] || arh_die "image does not exist: $image"
        actual=$(arh_sha256 "$image")
        [ "$actual" = "$expected" ] || arh_die "image digest mismatch: $key"
        ;;
    esac
  fi
}

# arh_ctr_run <image-key-or-path> <cmd...>
arh_ctr_run() {
  local key="$1" image
  image=$(arh_ctr_image "$key"); shift
  local backend; backend=$(arh_ctr_backend)
  arh_ctr_verify "$key" "$image"
  local binds ro_binds b args=()
  ro_binds=$(arh_config_get "$ARH_PROJ" immutable_inputs "")
  binds=$(arh_config_get "$ARH_SITE" extra_binds "")

  case "$backend" in
    apptainer|singularity)
      args=(exec --cleanenv --containall --env LC_ALL=C)
      for b in $ro_binds; do [ -n "$b" ] && args+=(--bind "$b:$b:ro"); done
      for b in $binds;    do [ -n "$b" ] && args+=(--bind "$b"); done
      args+=(--bind "$ARH_ROOT:$ARH_ROOT" --pwd "$ARH_ROOT" "$image")
      "$backend" "${args[@]}" "$@"
      ;;
    docker)
      image=${image#docker://}
      args=(run --rm -u "$(id -u):$(id -g)" -e LC_ALL=C)
      for b in $ro_binds; do [ -n "$b" ] && args+=(-v "$b:$b:ro"); done
      for b in $binds;    do [ -n "$b" ] && args+=(-v "$b"); done
      args+=(-v "$ARH_ROOT:$ARH_ROOT" -w "$ARH_ROOT" "$image")
      docker "${args[@]}" "$@"
      ;;
    none)
      arh_warn "SMOKE TEST: host execution is unpinned and has no read-only container binds"
      "$@"
      ;;
    *) arh_die "unknown container_runtime: $backend" ;;
  esac
}
