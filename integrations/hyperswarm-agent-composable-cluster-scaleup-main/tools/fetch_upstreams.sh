#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
# shellcheck disable=SC1091
source "${ROOT}/tools/upstreams.env"

mkdir -p "${ROOT}/third_party"

clone_or_update() {
  local name="$1" url="$2" ref="$3"
  local dir="${ROOT}/third_party/${name}"
  if [ ! -d "${dir}/.git" ]; then
    rm -rf "${dir}"
    git clone --quiet "${url}" "${dir}"
  fi
  ( cd "${dir}" && git fetch --all --tags --quiet && git checkout --quiet "${ref}" )
  echo "OK: ${name} @ ${ref}"
}

clone_or_update "kubespray" "${KUBESPRAY_URL}" "${KUBESPRAY_REF}"
clone_or_update "krew" "${KREW_URL}" "${KREW_REF}"
clone_or_update "fybrik-the-mesh-for-data" "${FYBRIK_URL}" "${FYBRIK_REF}"
clone_or_update "heroku-buildpack-apt" "${HEROKU_BUILDPACK_APT_URL}" "${HEROKU_BUILDPACK_APT_REF}"

echo "OK: fetched all upstreams into third_party/"
