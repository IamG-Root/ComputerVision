#!/bin/bash
set -e
cd "$(dirname "$0")"
case "${1:-}" in module|server) target="$1" ;; *) echo 'Usage: launcher.sh module|server [--draw] [--debug]'; exit 2 ;; esac
shift
args=()
for arg in "$@"; do
    case "$arg" in draw|debug) args+=("--$arg") ;; *) args+=("$arg") ;; esac
done
exec cvenv/bin/python "$target/main.py" "${args[@]}"
