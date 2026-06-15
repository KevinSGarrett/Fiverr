# Catalog Rebuild Procedure

## Purpose

Rebuild machine-readable PM planning catalogs from `PM_Pack/ref` after reference documentation changes.

## When To Rebuild

- After any change under `PM_Pack/ref/project_plan/`
- After any change under `PM_Pack/ref/dod/`
- After any change under `PM_Pack/ref/todo/`
- After any change under `PM_Pack/ref/github/`

## Manual Rebuild Command

```powershell
python automation/ref_catalog_builder.py build
```

## Verification Command

```powershell
python automation/ref_catalog_builder.py verify --strict
```

## Automatic Rebuild Path

Catalogs are automatically rebuilt during:

```powershell
python automation/ai_cycle_controller.py compile-policy
```

`compile-policy` now invokes `automation.ref_catalog_builder.build_all_catalogs(...)` after writing the policy snapshot.
