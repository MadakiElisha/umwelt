#!/usr/bin/env bash
# Report what the development machine has installed.
# Read-only: this script never installs or changes anything.

set -u

ok()   { printf '  [ok]   %s\n' "$1"; }
warn() { printf '  [warn] %s\n' "$1"; }
miss() { printf '  [miss] %s\n' "$1"; }

section() { printf '\n%s\n' "$1"; }

# check <command> <label> <hint if missing>
check() { if command -v "$1" >/dev/null 2>&1; then ok "$2"; else miss "$2 ($3)"; fi; }

section "System"
if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  if [ "${VERSION_ID:-}" = "24.04" ]; then ok "$PRETTY_NAME"; else warn "$PRETTY_NAME (target is Ubuntu 24.04)"; fi
fi
mem_gb=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
swap_gb=$(awk '/SwapTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
ok "RAM ${mem_gb} GB, swap ${swap_gb} GB"
if [ "$mem_gb" -lt 24 ] && [ "$swap_gb" -lt 8 ]; then
  warn "Gazebo, PX4 and a vision model together can exceed 16 GB. Consider 16 GB of swap."
fi

section "GPU"
if command -v nvidia-smi >/dev/null 2>&1; then
  ok "$(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader)"
else
  warn "nvidia-smi not found"
fi

section "ROS 2"
if [ -f /opt/ros/jazzy/setup.bash ]; then
  ok "ROS 2 Jazzy installed at /opt/ros/jazzy"
else
  miss "ROS 2 Jazzy (/opt/ros/jazzy/setup.bash)"
fi
check colcon "colcon" "sudo apt install python3-colcon-common-extensions"
check rosdep "rosdep" "sudo apt install python3-rosdep"

section "Simulation"
if command -v gz >/dev/null 2>&1; then
  gz_ver=$(gz sim --versions 2>/dev/null | head -n1)
  ok "Gazebo ${gz_ver:-installed}"
  case "$gz_ver" in 8.*) ;; *) warn "Jazzy pairs with Gazebo Harmonic (gz-sim 8)";; esac
else
  miss "Gazebo (gz)"
fi

px4_dir="${PX4_DIR:-$HOME/PX4-Autopilot}"
if [ -d "$px4_dir/.git" ]; then
  ok "PX4 at $px4_dir ($(git -C "$px4_dir" describe --tags --always 2>/dev/null))"
else
  miss "PX4-Autopilot (set PX4_DIR if it is not in ~/PX4-Autopilot)"
fi
check MicroXRCEAgent "Micro XRCE-DDS Agent" "bridge between PX4 and ROS 2"

section "Python"
ok "$(python3 --version)"
if python3 -c "import venv" 2>/dev/null; then ok "venv module"; else miss "venv (sudo apt install python3-venv)"; fi

ws="${UMWELT_WS:-$HOME/umwelt_ws}"
if [ -d "$ws/.venv" ]; then ok "project venv at $ws/.venv"; else warn "no project venv yet (run scripts/setup_env.sh)"; fi

printf '\n'
