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
    *) printf '%s/%s' "$(dl_config_get "$DL_SITE" image_dir "$DL_ROOT/.dl/images")" "$v" ;;
  esac
}

# dl_ctr_run <image-key-or-path> <cmd...>
dl_ctr_run() {
  local image; image=$(dl_ctr_image "$1"); shift
  local backend; backend=$(dl_ctr_backend)
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
      args=(run --rm -u "$(id -u):$(id -g)" -e LC_ALL=C)
      for b in $ro_binds; do [ -n "$b" ] && args+=(-v "$b:$b:ro"); done
      for b in $binds;    do [ -n "$b" ] && args+=(-v "$b"); done
      args+=(-v "$DL_ROOT:$DL_ROOT" -w "$DL_ROOT" "$image")
      docker "${args[@]}" "$@"
      ;;
    none)
      "$@"
      ;;
    *) dl_die "unknown container_runtime: $backend" ;;
  esac
}
