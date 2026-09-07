#!/usr/bin/env bash
#
# deploy.sh - Render the recipes sub-site and produce site.zip for deployment.
#
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

usage() {
    cat << EOF
Usage: ${SCRIPT_NAME} [-h] RECIPES_PATH

Render recipes from RECIPES_PATH into the recipes sub-site, and produce
site.zip for deployment.

Arguments:
  RECIPES_PATH   Base path of the recipes repository.

Options:
  -h, --help    Show this help message and exit.
EOF
}

# --- Parse arguments ---
RECIPES_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "Error: unknown option '$1'" >&2
            echo >&2
            usage >&2
            exit 1
            ;;
        *)
            if [[ -n "$RECIPES_PATH" ]]; then
                echo "Error: unexpected extra argument '$1'" >&2
                echo >&2
                usage >&2
                exit 1
            fi
            RECIPES_PATH="$1"
            shift
            ;;
    esac
done

# Handle any remaining args after --
if [[ $# -gt 0 ]]; then
    if [[ -n "$RECIPES_PATH" ]]; then
        echo "Error: unexpected extra argument '$1'" >&2
        echo >&2
        usage >&2
        exit 1
    fi
    RECIPES_PATH="$1"
fi

if [[ -z "$RECIPES_PATH" ]]; then
    echo "Error: RECIPES_PATH is required" >&2
    echo >&2
    usage >&2
    exit 1
fi

# Resolve ROOT_PATH
ROOT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_DIR="${ROOT_PATH}/site"
SITE_ZIP="${ROOT_PATH}/site.zip"
OUTPUT_DIR="${SITE_DIR}/recipes"

rm -rf "${OUTPUT_DIR}" "${SITE_ZIP}"

uv run cook-render -b "${RECIPES_PATH}" -o "${OUTPUT_DIR}"

cd "${SITE_DIR}"
zip -r "${SITE_ZIP}" .

echo "Built ${SITE_ZIP}"
