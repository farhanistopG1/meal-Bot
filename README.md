🍽️ MealBot

A Domain-Centric Design (DCD) implementation of Engineering OS, applied to a real problem: what is this household eating tomorrow, and who's cooking it.

MealBot runs a household's daily meal decision end-to-end: residents hold standing preferences, a menu is built from them, a poll goes out to the household's Telegram group, residents vote, and the winning meal is recorded and handed to whoever's cooking.

The model, in one sentence

Telegram is where reality happens; coordination observes and reconciles it; DCD defines what MealBot means; runtime coordinates it; repositories remember it; PostgreSQL preserves it; infrastructure keeps the organism alive.

Reality (Telegram)
        ↓
Coordination (N1 bootstrap · N2 reconciliation)
        ↓
Business Domains (D1 · D2 · D3)
        ↓
Runtime (body.py · organs.py)
        ↓
Repositories
        ↓
PostgreSQL
        ↓
Infrastructure & Deployment

Each layer owns exactly one responsibility and stays out of the others':

Layer	Owns	Does not own
Telegram	Groups, chats, polls, messages, human actions	Business rules or authoritative meal state
N1 / N2 coordination	Observation, schedules, retries, reconciliation	The meaning of Home, Resident, vote, or winner
Runtime	HTTP boundary, cross-domain orchestration	Telegram provider details
D1 / D2 / D3	Business rules and state transitions	Infrastructure timing and delivery
PostgreSQL	Durable business and transport facts	Workflow decisions
Domains
Domain	Question answered	Key objects
D1 — Home Management	Who belongs to this home?	Home, Resident, Cook
D2 — Meal Preferences	What does each resident generally prefer?	MealPreference (exactly five unique favourite meals)
D3 — Daily Meal Coordination	What will this home eat tomorrow?	HomeMenu, DailyMealPoll, MealVote, MealSummary, MealPlan

D1 creates the household boundary. D2 stores long-term, versioned preferences. D3 turns those preferences into one date-specific operational decision.

Daily decision loop
Residents hold current D2 preferences (five unique favourite meals each).
D3 merges active preferences into a HomeMenu and ranks meals by popularity.
D3 selects the top three choices and opens one poll for the Home and meal date.
Each active resident casts one vote for one of the choices.
Closing the poll deterministically picks a winner, records the MealSummary, and produces the MealPlan.
Transport delivers the resulting instruction to the people who need it.
Telegram integration (N1 / N2)

Telegram is treated as observed reality, never as a source of business truth — a message or a vote only becomes meaningful once it's reconciled into a D1/D2/D3 record.

N1 (bootstrap): observes an unknown Telegram group, resolves it via a transport-endpoint lookup, and — if unknown — selects a host and routes them to /configure?chat_id=<chat_id>. The frontend carries that context through Home creation; runtime persists an active Telegram resident_poll endpoint so the same group never re-bootstraps.
N2 (reconciliation): periodically enumerates active Home↔Telegram links, compares observed group membership against saved resident identities, and issues onboarding links for anyone missing.
Poll listener: an independent process resolves host-selection polls, detects the winner, and announces it back to the group.
Resident onboarding
Host: the configuration page resolves and reuses the anchor Resident — it never creates a duplicate.
Normal resident: the configuration page collects contact details and meal preferences, adds the Resident to the Home (with duplicate-phone validation), and persists their Telegram identity plus current D2 preference record.

This flow was verified in a clean-room run from an intentionally empty database: the host was correctly reused rather than duplicated, a second resident was added cleanly, and both active Telegram identities and D2 preference records persisted correctly.

Persistence

13-table PostgreSQL schema. Business memory and transport memory are kept deliberately separate, so an external Telegram identity never becomes a business entity on its own.

Area	Tables
D1 household	homes, residents, cooks
D2 preferences	meal_preferences, meal_preference_items
D3 daily decision	daily_meal_polls, poll_options, meal_votes, meal_summaries, meal_plans
Transport identity	transport_endpoints, resident_transport_identities, transport_poll_bindings

Each domain (D1/D2/D3) owns its own repository and SQL — there's no shared, general-purpose data-access layer.

Production deployment
Service	Behavior
mealbot.service	FastAPI/Uvicorn behind nginx + HTTPS — serves the API
mealbot-telegram-poll.service	Runs the Telegram poll listener from the production venv
mealbot-telegram-resident.service	Runs the N2 reconciler with automatic restart

nginx serves the deployed frontend from a separate static path; source (/root/meal-Bot) and the served copy are deliberately kept as separate states. All three services run under systemd — process lifecycle, restart, and boot-time startup are handled by the OS, not by a terminal session.

Runtime structure
body.py      → HTTP transport only
organs.py    → runtime orchestration across D1 / D2 / D3
brain.py     → cross-domain intelligence
database.py  → runtime infrastructure
bash
uvicorn body:app --reload
Status — frozen checkpoint: 4 September 2026 (58aeac5)

Built and verified:

D1, D2, D3 domains, each persisted to PostgreSQL with its own repository
Full daily decision loop (preferences → menu → poll → vote → winner → summary/plan) verified end-to-end
Telegram environment observer, N1 bootstrap, N2 reconciliation
Resident onboarding (host + normal resident), clean-room verified
Configuration frontend wired end-to-end: frontend → API → D1 → PostgreSQL
Deployed to a Linux VPS behind nginx/HTTPS, all three services running under systemd

Known limitations / next phase — not yet done:

Home creation + transport-endpoint insertion aren't yet a single transaction — a binding failure can currently leave an orphaned Home
Host detection compares Telegram display name to the anchor Resident's name — works for the MVP, not final identity proof; needs authenticated, signed, short-lived onboarding context instead
Incoming Telegram votes should be validated against a persisted transport_poll_bindings record before being trusted as D3 votes
meal_plans has a schema/repository mismatch — the repository reads/writes a vote_count field the schema doesn't define
No idempotency keys, auth, retry logging, or integration tests yet on the Telegram-driven workflows
The full autonomous daily loop (D3 recommendation → real Telegram poll → votes → winner → cook notification, orchestrated end-to-end via n8n) is the current build target, not yet shipped
The current frontier is a genuinely coherent internal people model — beyond simply creating a Home from an observed Telegram group

A green systemd status is not treated as proof of correctness here — liveness, heartbeat, scheduled work, and business outcome are tracked as separate signals.

Tech stack

Python · FastAPI · PostgreSQL · Telegram Bot API · nginx · systemd · Linux VPS

Why this project?

MealBot isn't meant to demonstrate FastAPI. It's meant to demonstrate business-first software design: independent domains, an environment that's observed rather than trusted, and infrastructure that keeps running without a human attached to it.

Author

Farhan Ahmed Mudgal — building Engineering OS one deployed project at a time.
