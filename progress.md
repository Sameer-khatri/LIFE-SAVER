> Last updated: 2026-04-21, Repair sprint complete. App is operational.

# LIFE SAVER Progress Tracker

## About the App & Mission
**LIFE SAVER** is an execution system built to enforce discipline and track progress.
**Mission**: Build real proof in AI, automation, and cybersecurity over 12 weeks through shipped projects, honest execution tracking, and internship-focused packaging.

## The Core Projects
1. **LIFE SAVER**: The core execution system tracking daily tasks, evidence, and weekly outcomes.
2. **PromptShield**: The flagship AI + cybersecurity project.
3. **Internship Copilot Lite**: The supporting AI + automation project to aid internship applications.

## Current Status
**Status:** Week 1. App is fully operational and ready for daily use.

## Completed Work

### Phase 1: Seed Data (done)
- `master_roadmap.md` established.
- `weeks_seed.json` generated for roadmap context (12 weeks, 3 phases).
- `daily_tasks_seed.json` generated containing day-by-day action plans.
- `weekly_review_templates.json` created.
- `seed_loader.py` script created and executed.
- `lifesaver.db` initialized with all tables and populated with seed data.

### Phase 2: Flask App v1 (done)
- `app.py` — Flask backend with initial 5 routes.
- `templates/base.html` — Base layout with sticky navbar.
- `templates/index.html` — Dashboard with week stats and quick links.
- `templates/checkin.html` — Daily check-in form.
- `templates/roadmap.html` — Weekly roadmap view.
- `templates/tasks.html` — Day-by-day task cards.
- `templates/review.html` — Weekly review with template signals.
- `static/style.css` — Dark glassmorphism design system.

### Phase 3: Repair Sprint (done)
- Safe schema migrations at app startup (ALTER TABLE, no data loss).
- Check-in truth layer fixed: evidence and blockers are separate fields.
- Upsert behavior: one check-in per date, editing updates the existing row.
- Check-in form pre-populates if today already has an entry.
- Evidence logs: dedicated `/evidence` page with form (type, title, project, proof link, commit ref, impact level).
- POST/Redirect/GET on check-in and review forms (no duplicates on refresh).
- Task status tracking: pending / in_progress / done with toggle buttons.
- Week navigation: dropdown in navbar to switch active week (W1-W12).
- History page: `/history` showing recent check-ins, evidence, and reviews.
- Dashboard shows real tracked data: today's check-in status, task completion, evidence count.
- Encoding cleanup: emoji replaced with text labels, UTF-8 response headers.
- `start.bat` added for one-click launch with browser auto-open.

## Current App Structure
```
lifesaver_seed/
  app.py                  # Flask backend (10 routes)
  config.json             # Active week setting
  lifesaver.db            # SQLite database
  start.bat               # One-click launcher
  seed_loader.py          # DB seeder (already run)
  master_roadmap.md       # 12-week plan
  progress.md             # This file
  weeks_seed.json         # Week/phase seed data
  daily_tasks_seed.json   # Task seed data
  weekly_review_templates.json
  static/
    style.css             # Design system (1000+ lines)
  templates/
    base.html             # Layout + navbar + week selector
    index.html            # Dashboard with real stats
    checkin.html           # Daily check-in (upsert)
    tasks.html             # Tasks with status tracking
    evidence.html          # Evidence log form + list
    roadmap.html           # Weekly roadmap view
    review.html            # Weekly review
    history.html           # Activity history
```

## App Routes
| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Dashboard with real stats |
| `/checkin` | GET/POST | Daily check-in (upsert per date) |
| `/tasks` | GET | Task view with status badges |
| `/tasks/update_status` | POST | Toggle task status |
| `/evidence` | GET/POST | Evidence log form + list |
| `/roadmap` | GET | Weekly roadmap |
| `/review` | GET/POST | Weekly review |
| `/history` | GET | Recent activity log |
| `/set_week` | POST | Change active week |

## What Has NOT Been Done Yet
- No GitHub push yet.
- No evidence scoring or streak tracking.
- No export or report generation.
- No multi-week comparison view.

## Exact Next Step
Start using the app for real daily check-ins today. First saved check-in = proof that Week 1 deliverable is met.

## Tech Stack
- Python 3 + Flask
- SQLite (lifesaver.db)
- Server-rendered HTML/CSS (Jinja2 templates)

## Weekly Rules to Carry Forward
- Tutorial time max 45 minutes per day.
- Every day must create proof.
- No redesign rabbit hole.
- No second project this week.
- No switching stack.

---

> **Note for any future AI agent**: Read `master_roadmap.md` first, then this file before doing anything.

