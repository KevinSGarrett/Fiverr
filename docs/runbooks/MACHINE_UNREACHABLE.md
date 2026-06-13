# Machine Unreachable Playbook

## Layer 1 — Tailscale (Fastest)

- Command: `tailscale ping <runner-hostname>`
- Recovery time: 2-5 minutes
- Action: connect via Tailscale IP, RDP to machine, restart runner process
- Verify after recovery: runner online, heartbeat timestamp current, model state still VERIFIED

## Layer 2 — Chrome Remote Desktop

- Use if Tailscale is down but internet is available.
- Open [https://remotedesktop.google.com/access](https://remotedesktop.google.com/access) from trusted device.
- Recovery time: 5-10 minutes
- Action: remote in, relaunch `C:\actions-runner\run.cmd`
- Verify: actions runner status online, heartbeat fresh

## Layer 3 — GitHub Web Recovery

- Open [https://github.com/KevinSGarrett/Fiverr/actions](https://github.com/KevinSGarrett/Fiverr/actions).
- Recovery time: 5-15 minutes
- Action: inspect last job, trigger re-registration workflow if process-level issue
- Verify: new jobs leave waiting state and bind runner

## Layer 4 — Phone/Tablet Access

- Use Tailscale mobile app to reach runner host.
- Recovery time: 10-20 minutes
- Action: mobile SSH/RDP path to restart runner and review logs
- Verify: heartbeat updates and runner online

## Layer 5 — Smart Plug Power Cycle

- Use only when machine is non-responsive.
- Recovery time: 15-30 minutes
- Action: power cycle, wait 3 minutes, confirm BIOS auto-power setting enabled (`Power On After Power Failure`)
- Verify: Windows starts, runner starts, model freshness still valid

## Layer 6 — What Cannot Be Fixed Remotely (Last)

Some conditions require physical presence:

- Cursor re-auth requiring UI interaction
- Windows update restart loop requiring keyboard intervention
- BIOS updates requiring local confirmation
- hardware failure

Recovery time: variable (30+ minutes to multi-hour).

## Post-Recovery Checklist (All Layers)

1. Confirm runner online.
2. Confirm `heartbeat.json` updated recently.
3. Confirm `cursor_model_state.json` remains VERIFIED and fresh.
4. Record incident and recovery layer used.

