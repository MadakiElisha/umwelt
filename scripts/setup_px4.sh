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

venv="$ws/.venv"
if [ ! -f "$venv/bin/activate" ]; then
  echo "No project venv at $venv. Run scripts/setup_env.sh first." >&2
  exit 1
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

# PX4's build needs Python packages (kconfiglib, empy, jinja2 and others).
# Install them into the project venv rather than the system Python, which
# Ubuntu 24.04 protects, and build from inside the venv so CMake finds them.
# shellcheck disable=SC1091
source "$venv/bin/activate"
reqs="$(mktemp)"
# PX4 v1.15 lists "matplotlib>=3.0.*", which current pip rejects as invalid.
sed 's/>=\([0-9.]*\)\.\*/>=\1/' "$px4/Tools/setup/requirements.txt" > "$reqs"
echo "Installing PX4 build requirements into $venv"
python -m pip install --quiet -r "$reqs"
rm -f "$reqs"

echo "Building px4_sitl_default"
make -C "$px4" px4_sitl

echo
echo "Done. PX4 for umwelt is at $px4"
echo "scripts/activate.sh points PX4_DIR there automatically."
