# EC2 Failover Plan — Fiverr Research System

**Use when:** Local runner (`FIVERR-AI-RUNNER`) is unreachable and work must continue.  
**EC2 role:** Cold standby — configured/AMI saved, instance stopped when not needed.

---

## When to Activate

Activate EC2 failover when:
- Local runner machine is unreachable via Tailscale, RDP, and Chrome Remote Desktop
- Local power or internet is down for > 2 hours
- Local machine hardware failure prevents restart
- Work continuity is required and local recovery timeline is unknown

---

## Pre-requisites (one-time setup)

```text
[ ] EC2 instance created (Windows Server or Amazon Linux)
[ ] SSM Agent installed and IAM role attached
[ ] GitHub self-hosted runner installed (label: fiverr-ai-runner-ec2)
[ ] Python 3.11 + venv + pip installed
[ ] Cursor CLI installed and authenticated (if headless mode works)
[ ] runner.env secrets stored in AWS SSM Parameter Store or local to instance
[ ] AMI snapshot saved after full setup
[ ] Instance stopped (cold standby)
```

---

## Failover Activation Procedure

### Step 1 — Stop local runner if reachable
```powershell
# On local machine (if accessible)
schtasks /End /TN "AI Runner Controller"
Stop-Service "actions.runner.*"
```

### Step 2 — Start EC2 instance
```bash
# From AWS Console or CLI
aws ec2 start-instances --instance-ids i-XXXXXXXXXXXXXXXXX
aws ec2 wait instance-running --instance-ids i-XXXXXXXXXXXXXXXXX
```

### Step 3 — Connect via SSM Session Manager
```bash
aws ssm start-session --target i-XXXXXXXXXXXXXXXXX
```

### Step 4 — Pull latest develop
```bash
cd /path/to/Fiverr
git fetch --all --prune
git checkout develop
git pull origin develop
```

### Step 5 — Verify environment
```bash
python -m ruff check .
python -m mypy src
python -m pytest -q
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py compile-policy
```

### Step 6 — Run model verification
```bash
# Verify cursor_model_state.json is current on EC2
python automation/ai_cycle_controller.py brain-check
```

### Step 7 — Confirm GitHub runner is online
Go to: `https://github.com/KevinSGarrett/Fiverr/settings/actions/runners`
Confirm the EC2 runner label `fiverr-ai-runner-ec2` is online.

### Step 8 — Start controller in dev_auto
```bash
python automation/ai_cycle_controller.py tick
```

---

## Failback to Local Runner

When local machine is restored:

1. Allow EC2 active cycle/PR to complete safely
2. Push all EC2 branches and open PRs
3. Update Jira with failover note on active tickets
4. Stop EC2 controller
5. On local: `git fetch --all --prune && git checkout develop && git pull origin develop`
6. Run local: `python automation/ai_cycle_controller.py brain-check`
7. Re-register local tasks if needed: `powershell -File C:\AI_Runner\scripts\register_tasks.ps1`
8. Start local controller: `schtasks /Run /TN "AI Runner Controller"`
9. Stop EC2 instance (return to cold standby)

---

## Cost Control

- Use t3.medium or c5.large (enough for Python + Cursor)
- Stop instance immediately after failback
- Set billing alerts at $20/month for EC2
- Use Spot instance for non-critical extended runs

---

## Verification Checklist After Failover

```text
[ ] EC2 instance running
[ ] SSM Session Manager connected
[ ] develop branch pulled cleanly
[ ] Tests pass on EC2
[ ] brain-check PASS
[ ] cursor_model_state.json current (or advisory mode set)
[ ] GitHub runner label online
[ ] Controller tick running
[ ] No active lock conflicts with local runner
```
