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

# PX4 talks to ROS 2 through the Micro XRCE-DDS Agent, which publishes over DDS.
# Nodes on a different middleware (for example rmw_zenoh_cpp) will not see PX4
# topics, so this project pins Fast DDS for the current shell only.
# Override with UMWELT_RMW if you need something else.
export RMW_IMPLEMENTATION="${UMWELT_RMW:-rmw_fastrtps_cpp}"

# Use the project's own PX4 checkout when it exists (scripts/setup_px4.sh).
if [ -z "${PX4_DIR:-}" ] && [ -d "$UMWELT_WS/deps/PX4-Autopilot" ]; then
  export PX4_DIR="$UMWELT_WS/deps/PX4-Autopilot"
fi

# Keep this project's DDS traffic separate from other ROS 2 work on the same
# network. PX4 must use the same domain: its UXRCE_DDS_DOM_ID parameter is set
# from this value by the sim launch files.
export ROS_DOMAIN_ID="${UMWELT_DOMAIN_ID:-42}"

unset _umwelt_repo _umwelt_ws
