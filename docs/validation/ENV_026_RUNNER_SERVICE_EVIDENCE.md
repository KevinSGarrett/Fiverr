# ENV-026 Runner Service Evidence (Cycle 077)

Command:

```text
Get-Service -Name "actions.runner.*" | Select-Object Name,Status
```

Output:

```text
[no services matched]
```

Timestamp: 2026-06-12T20:08:00-05:00

Result: No local Windows service matched `actions.runner.*` on this host at collection time.
