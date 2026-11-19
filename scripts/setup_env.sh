#!/usr/bin/env bash
# Create the project virtual environment.
#
# The venv is created with --system-site-packages so ROS 2 Python packages
# installed through apt stay importable, while anything installed with pip
# stays inside the venv and away from other projects.
#
# Safe to run more than once.

set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# If the repo sits in <ws>/src/umwelt, use <ws>. Otherwise fall back to ~/umwelt_ws.
if [ "$(basename "$(dirname "$repo_dir")")" = "src" ]; then
  default_ws="$(dirname "$(dirname "$repo_dir")")"
else
  default_ws="$HOME/umwelt_ws"
fi
ws="${UMWELT_WS:-$default_ws}"
venv="$ws/.venv"

if [ ! -f /opt/ros/jazzy/setup.bash ]; then
  echo "ROS 2 Jazzy not found at /opt/ros/jazzy. Install it first." >&2
  exit 1
fi

mkdir -p "$ws"

if [ ! -d "$venv" ]; then
  echo "Creating $venv"
  python3 -m venv --system-site-packages "$venv"
else
  echo "Using existing $venv"
fi

# colcon scans the whole workspace. Keep it out of the venv.
touch "$venv/COLCON_IGNORE"

# shellcheck disable=SC1091
source "$venv/bin/activate"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r "$repo_dir/requirements.txt"

echo
echo "Done. In each new shell run:"
echo "  source $repo_dir/scripts/activate.sh"
