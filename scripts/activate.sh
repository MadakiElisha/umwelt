# shellcheck shell=bash
# Source this file, do not execute it:
#   source scripts/activate.sh
#
# Sets up ROS 2 Jazzy, the project venv and the workspace overlay.

_umwelt_repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "$(basename "$(dirname "$_umwelt_repo")")" = "src" ]; then
  _umwelt_ws="$(dirname "$(dirname "$_umwelt_repo")")"
else
  _umwelt_ws="$HOME/umwelt_ws"
fi
export UMWELT_WS="${UMWELT_WS:-$_umwelt_ws}"

# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash

if [ -f "$UMWELT_WS/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$UMWELT_WS/.venv/bin/activate"
else
  echo "umwelt: no venv at $UMWELT_WS/.venv, run scripts/setup_env.sh" >&2
fi

if [ -f "$UMWELT_WS/install/setup.bash" ]; then
  # shellcheck disable=SC1091
  source "$UMWELT_WS/install/setup.bash"
fi

# Keep this project's DDS traffic separate from other ROS 2 work on the same network.
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"

unset _umwelt_repo _umwelt_ws
