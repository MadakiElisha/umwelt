#!/usr/bin/env bash
# Clone and build a PX4 checkout that belongs to this project only.
#
# Lives in <workspace>/deps/PX4-Autopilot, pinned to the version umwelt is
# tested against, so work on other PX4 checkouts never affects umwelt.
# Safe to run again: an existing checkout is reused and only rebuilt.

set -euo pipefail

PX4_VERSION="${PX4_VERSION:-v1.15.0}"

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "$(basename "$(dirname "$repo_dir")")" = "src" ]; then
  default_ws="$(dirname "$(dirname "$repo_dir")")"
else
  default_ws="$HOME/umwelt_ws"
fi
ws="${UMWELT_WS:-$default_ws}"
deps="$ws/deps"
px4="$deps/PX4-Autopilot"

# PX4's build uses system Python packages. Step out of the project venv
# so they are found the same way PX4's own setup expects.
if [ -n "${VIRTUAL_ENV:-}" ]; then
  PATH="$(printf '%s' "$PATH" | tr ':' '\n' | grep -vxF "$VIRTUAL_ENV/bin" | paste -sd ':' -)"
  export PATH
  unset VIRTUAL_ENV
fi

mkdir -p "$deps"
# PX4 ships a package.xml. Keep colcon from trying to build it.
touch "$deps/COLCON_IGNORE"

if [ ! -d "$px4/.git" ]; then
  echo "Cloning PX4 $PX4_VERSION into $px4"
  git clone --branch "$PX4_VERSION" --depth 1 --recurse-submodules --jobs 8 \
    https://github.com/PX4/PX4-Autopilot.git "$px4"
else
  echo "Using existing checkout at $px4 ($(git -C "$px4" describe --tags --always))"
fi

echo "Building px4_sitl_default"
make -C "$px4" px4_sitl

echo
echo "Done. PX4 for umwelt is at $px4"
echo "scripts/activate.sh points PX4_DIR there automatically."
