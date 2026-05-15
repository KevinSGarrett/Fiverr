# Alert System
# Fiverr Research System — Wave 8

**Document Status:** Complete
**Wave:** 8 — Reporting and Dashboard
**Purpose:** All alert types with trigger conditions, severity levels, display location, resolution behavior, and storage schema.

---

## Alert Types

| # | Alert Type | Severity | Display Location | Auto-Resolve? |
|---|---|---|---|---|
| 1 | STALE_DATA | MEDIUM | Page 1 banner + Page 2 badge | Yes — on next successful collection |
| 2 | NEW_STRONG_GO | LOW | Page 1 banner | Yes — after user views Page 4 |
| 3 | LLM_COST_THRESHOLD | HIGH | Page 6 banner | No — manual dismiss |
| 4 | JOB_DEAD_LETTER | MEDIUM–HIGH | Page 5 banner | Yes — on successful retry |
| 5 | AUTO_PROMOTION | LOW | Page 1 banner | Yes — after user views |
| 6 | COMPETITOR_CHANGE | LOW–MEDIUM | Page 3 notification | Yes — on next run |
| 7 | RUN_FAILURE | HIGH | Global banner (all pages) | Yes — on next successful run |
| 8 | DATA_QUALITY_LOW | MEDIUM | Page 1 niche badge + Page 5 chart | Yes — when quality rises above threshold |

---

## Alert 1 — STALE_DATA

**Trigger condition:**
```python
def check_stale_data_alerts(db):
    """
    Fires when any REQUIRED collection record has exceeded its TTL.
    Checked at dashboard load and after every run.
    """
    for niche_id in get_active_niche_ids(db):
        stale_sources = get_stale_sources_for_niche(niche_id, db)
        if stale_sources:
            source_list = ", ".join([s["source_type"] for s in stale_sources])
            oldest_age_hours = max(s["age_hours"] for s in stale_sources)
            create_or_update_alert(
                alert_type="STALE_DATA",
                niche_id=niche_id,
                severity="MEDIUM" if oldest_age_hours < 336 else "HIGH",  # 2 weeks = HIGH
                message=(f"{get_niche_name(niche_id)}: {len(stale_sources)} data sources "
                         f"past TTL ({source_list}). Oldest: {oldest_age_hours:.0f}h. "
                         "Consider running collection."),
                metadata={"stale_sources": stale_sources},
                db=db,
            )
```

**Resolution:** Automatically resolved when the stale source is refreshed by a new collection run.

**Display:** Yellow/red banner on Opportunities page. Badge on niche name in keyword table.

---

## Alert 2 — NEW_STRONG_GO

**Trigger condition:**
```python
def check_new_strong_go_alerts(run_id: str, db):
    """
    Fires when keywords newly tagged STRONG GO in this run
    (were not STRONG GO in the previous run).
    """
    current_strong_go = get_keywords_by_tag("STRONG GO", run_id, db)
    previous_run_id = get_previous_run_id(run_id, db)
    if not previous_run_id:
        return  # First run — no comparison

    previous_strong_go_ids = set(get_keyword_ids_by_tag("STRONG GO", previous_run_id, db))
    new_strong_go = [kw for kw in current_strong_go if kw.keyword_id not in previous_strong_go_ids]

    if new_strong_go:
        keyword_names = [get_keyword_text(kw.keyword_id, db) for kw in new_strong_go[:5]]
        create_alert(
            alert_type="NEW_STRONG_GO",
            severity="LOW",
            message=f"{len(new_strong_go)} new STRONG GO keyword(s): {', '.join(keyword_names)}",
            metadata={"keyword_ids": [kw.keyword_id for kw in new_strong_go]},
            db=db,
        )
```

**Resolution:** Auto-resolves when user navigates to Recommendations page.

---

## Alert 3 — LLM_COST_THRESHOLD

**Trigger condition:**
```python
def check_llm_cost_alerts(run_id: str, db, config):
    """
    Fires when daily LLM spend exceeds config threshold.
    """
    daily_threshold = config.get("alerts", {}).get("llm_daily_cost_threshold", 5.00)
    today_cost = get_llm_cost_today(db)

    if today_cost > daily_threshold:
        create_alert(
            alert_type="LLM_COST_THRESHOLD",
            severity="HIGH",
            message=(f"Daily LLM spend ${today_cost:.2f} exceeds threshold "
                     f"${daily_threshold:.2f}. Review LLM Costs page."),
            metadata={"daily_cost": today_cost, "threshold": daily_threshold},
            db=db,
        )
```

**Resolution:** Manual dismiss by user. Reappears next day if threshold exceeded again.

**Config:**
```yaml
alerts:
  llm_daily_cost_threshold: 5.00
  llm_weekly_cost_threshold: 25.00
```

---

## Alert 4 — JOB_DEAD_LETTER

**Trigger condition:**
```python
def check_dead_letter_alerts(run_id: str, db):
    """
    Fires when high-impact jobs end in dead letter queue.
    """
    dead_letters = db.query(Job).filter(
        Job.run_id == run_id,
        Job.status == "DEAD_LETTER",
    ).all()

    high_impact_types = {"fiverr_search", "gig_detail_scrape", "seller_profile_scrape",
                         "google_trends_fetch", "recommendation_generation"}

    high_impact_dead = [dl for dl in dead_letters if dl.job_type in high_impact_types]

    if high_impact_dead:
        create_alert(
            alert_type="JOB_DEAD_LETTER",
            severity="HIGH" if len(high_impact_dead) > 5 else "MEDIUM",
            message=(f"{len(high_impact_dead)} high-impact jobs failed permanently: "
                     f"{', '.join(set(dl.job_type for dl in high_impact_dead[:5]))}"),
            metadata={"dead_letter_ids": [dl.id for dl in high_impact_dead]},
            db=db,
        )
```

**Resolution:** Auto-resolves when all dead letter jobs are retried successfully.

---

## Alert 5 — AUTO_PROMOTION

**Trigger condition:**
```python
def check_auto_promotion_alerts(run_id: str, db):
    """
    Fires when the auto-promotion evaluator changes a niche's depth.
    """
    promotions = db.query(AutoPromotionLog).filter(
        AutoPromotionLog.run_id == run_id,
    ).all()

    for promo in promotions:
        direction = "promoted" if promo.to_depth_rank > promo.from_depth_rank else "demoted"
        create_alert(
            alert_type="AUTO_PROMOTION",
            niche_id=promo.niche_id,
            severity="LOW",
            message=(f"{get_niche_name(promo.niche_id)} {direction}: "
                     f"{promo.from_depth} → {promo.to_depth}"),
            metadata={"from": promo.from_depth, "to": promo.to_depth},
            db=db,
        )
```

**Resolution:** Auto-resolves after user views the Opportunities page.

---

## Alert 6 — COMPETITOR_CHANGE

**Trigger condition:** Directly from `detect_competitor_changes()` in Wave 5 COMPETITOR_PROFILING.md. Changes include review surge (>20%), level upgrade, and new top-10 entrant.

**Resolution:** Auto-resolves on next run (changes are now the baseline).

---

## Alert 7 — RUN_FAILURE

**Trigger condition:**
```python
def check_run_failure_alerts(run_id: str, db):
    """
    Fires when a run ends with FAILED status.
    """
    run = db.query(RunLog).filter(RunLog.run_id == run_id).first()
    if run and run.status == "FAILED":
        create_alert(
            alert_type="RUN_FAILURE",
            severity="HIGH",
            message=(f"Run {run_id[:8]} failed at Stage {run.failed_at_stage}: "
                     f"{run.error_message[:100]}"),
            metadata={"run_id": run_id, "stage": run.failed_at_stage},
            db=db,
        )
```

**Resolution:** Auto-resolves on next successful run completion.

**Display:** Persistent red banner on ALL dashboard pages until resolved.

---

## Alert 8 — DATA_QUALITY_LOW

**Trigger condition:**
```python
def check_data_quality_alerts(db):
    """
    Fires when a niche's data quality score drops below 50%.
    """
    for niche_id in get_active_niche_ids(db):
        quality = calculate_niche_data_quality(niche_id, db)
        if quality["score"] < 50:
            missing = quality.get("missing_fields", [])[:3]
            create_or_update_alert(
                alert_type="DATA_QUALITY_LOW",
                niche_id=niche_id,
                severity="MEDIUM",
                message=(f"{get_niche_name(niche_id)} data quality at {quality['score']}% "
                         f"({quality['label']}). Missing: {', '.join(missing)}"),
                metadata=quality,
                db=db,
            )
```

**Resolution:** Auto-resolves when data quality score rises above 50%.

---

## Alert Storage Schema

```python
# Already in Wave 3 SCHEMA.md — documented here for reference

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String, nullable=False, index=True)
    niche_id = Column(String, nullable=True, index=True)
    severity = Column(String, nullable=False)  # HIGH, MEDIUM, LOW
    message = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    run_id = Column(String, nullable=True)
```

---

## Alert Orchestration

```python
def run_alert_checks(run_id: str, db, config):
    """Called at end of every run after all stages complete."""
    check_stale_data_alerts(db)
    check_new_strong_go_alerts(run_id, db)
    check_llm_cost_alerts(run_id, db, config)
    check_dead_letter_alerts(run_id, db)
    check_auto_promotion_alerts(run_id, db)
    # COMPETITOR_CHANGE alerts are created during Stage 8 (competitor analysis)
    check_run_failure_alerts(run_id, db)
    check_data_quality_alerts(db)

    active_count = db.query(Alert).filter(Alert.resolved == False).count()
    log.info(f"Alert check complete: {active_count} active alerts")
```
