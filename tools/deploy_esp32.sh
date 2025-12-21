#!/usr/bin/env sh
set -eu

# Deploy MicroPython client + example main.py to an ESP32.
#
# Requirements:
#   - mpremote installed (recommended): https://docs.micropython.org/en/latest/reference/mpremote.html
#   - ESP32 flashed with MicroPython and connected via USB serial
#
# Usage:
#   PORT=/dev/tty.usbserial-XXXX ./clients/micropython/tools/deploy_esp32.sh

PORT="${PORT:-}"

if ! command -v mpremote >/dev/null 2>&1; then
  echo "ERROR: mpremote not found. Install with: pipx install mpremote (or pip install mpremote)" >&2
  exit 1
fi

# Autodetect port when possible.
if [ -z "$PORT" ]; then
  # macOS common patterns
  for candidate in /dev/tty.usbserial* /dev/tty.SLAB_USBtoUART* /dev/tty.wchusbserial* /dev/tty.usbmodem*; do
    if [ -e "$candidate" ]; then
      PORT="$candidate"
      break
    fi
  done
fi

if [ -z "$PORT" ]; then
  echo "ERROR: Could not autodetect serial port. Set PORT=/dev/tty...." >&2
  echo "Hint (macOS): ls /dev/tty.* | grep -E 'usb|SLAB|wch|modem'" >&2
  exit 1
fi

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PKG_DIR="$ROOT_DIR/lib"
MAIN_CODE_FILE="$ROOT_DIR/main.py"
ENV_FILE="$ROOT_DIR/environment.py"

if [ ! -d "$PKG_DIR" ]; then
  echo "ERROR: Package dir not found: $PKG_DIR" >&2
  exit 1
fi
if [ ! -f "$MAIN_CODE_FILE" ]; then
  echo "ERROR: Main code file not found: $MAIN_CODE_FILE" >&2
  exit 1
fi

echo "Deploying to $PORT"

echo "- Ensuring :/lib exists"
mpremote connect "$PORT" fs mkdir :/lib >/dev/null 2>&1 || true

echo "- Copying library to :/lib"
mpremote connect "$PORT" fs cp -r "$PKG_DIR"/* :/lib/

echo "- Copying code to device"
mpremote connect "$PORT" fs cp "$MAIN_CODE_FILE" :/main.py
mpremote connect "$PORT" fs cp "$ENV_FILE" :/environment.py


echo "Done. Next:" 
echo "  1) Edit WiFi + base_url in main.py, redeploy" 
echo "  2) Open REPL: mpremote connect \"$PORT\" repl" 
echo "  3) Soft reset run: mpremote connect \"$PORT\" reset" 
