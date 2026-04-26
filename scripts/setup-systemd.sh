#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BIN="$(which keep-it-tidy 2>/dev/null || echo "")"
if [[ -z "$BIN" ]]; then
    echo "Error: keep-it-tidy not found in PATH." >&2
    echo "Install it first: pip install -e '${PROJECT_DIR}'" >&2
    exit 1
fi

CONFIG_PATH="${PROJECT_DIR}/config/config.toml"
if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "Error: config.toml not found at ${CONFIG_PATH}" >&2
    echo "Copy the example: cp ${PROJECT_DIR}/config/config.example.toml ${CONFIG_PATH}" >&2
    exit 1
fi

SYSTEMD_DIR="${HOME}/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

cat > "${SYSTEMD_DIR}/keep-it-tidy.service" <<EOF
[Unit]
Description=keep-it-tidy directory cleanup

[Service]
Type=oneshot
ExecStart=${BIN} --config ${CONFIG_PATH}
StandardOutput=journal
StandardError=journal
EOF

cat > "${SYSTEMD_DIR}/keep-it-tidy.timer" <<EOF
[Unit]
Description=Run keep-it-tidy daily

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now keep-it-tidy.timer

echo ""
echo "keep-it-tidy timer installed and enabled."
echo ""
systemctl --user status keep-it-tidy.timer || true
echo ""
echo "Check logs: journalctl --user -u keep-it-tidy.service -n 50"
