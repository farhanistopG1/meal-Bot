# 🍽️ MealBot

**A production-deployed implementation of Engineering OS using Domain-Centric Design (DCD), Coordination/Transport (C/T), and state reconciliation.**

MealBot solves a simple household problem:

> **What are we eating tomorrow, and who's cooking it?**

But the system is designed around a deeper engineering principle:

**external reality is observed, business meaning is defined internally, and state is reconciled between the two.**

Residents maintain standing meal preferences. MealBot converts those preferences into a date-specific menu, publishes a Telegram poll, observes human votes, reconciles those observations into authoritative business state, determines the winning meal, creates the resulting meal plan, and delivers the decision to the people who need it.

---

# The Engineering Model

MealBot is built from three complementary foundations:

### 1. DCD — Domain-Centric Design

DCD answers:

> **What does the business mean?**

The business is decomposed into independent domains with explicit ownership.

```text
Reality
   ↓
Operating Environment
   ↓
Business Domain
   ↓
Business Events
   ↓
Business Rules
   ↓
Business Behaviours
   ↓
Business Objects
   ↓
Persistence
   ↓
Runtime
   ↓
Infrastructure
   ↓
Deployment

DCD prevents infrastructure, transport, and external providers from defining the business itself.

2. C/T — Coordination / Transport

C/T answers:

How does external reality interact with the business system?

Telegram is not treated as MealBot's business database.

Instead:

External Reality
      ↓
Transport
      ↓
Observation
      ↓
Coordination
      ↓
Business State

Transport carries signals.

Coordination observes those signals, decides what needs to happen, retries where necessary, and reconciles external state with internal state.

This allows Telegram to remain replaceable without changing the D1/D2/D3 business model.

3. State Reconciliation

MealBot does not assume that external reality and internal state are always synchronized.

Instead, it repeatedly asks:

What exists externally, what do we believe internally, and what needs to be reconciled?

Examples:

Telegram group
      ↕
transport_endpoints

Telegram resident
      ↕
resident_transport_identities

Telegram poll
      ↕
transport_poll_bindings

Telegram vote
      ↓
D3 MealVote

This makes reconciliation a first-class system behaviour rather than an afterthought.

The System in One Sentence

Telegram is where human reality happens; C/T observes and reconciles it; DCD defines what MealBot means; runtime coordinates it; repositories remember it; PostgreSQL preserves it; systemd and infrastructure keep the organism alive.

                    REALITY
                       │
                    Telegram
                       │
                       ▼
              Coordination / Transport
                 N1 · N2 · N3 · N4
                       │
                       ▼
                Business Domains
                  D1 · D2 · D3
                       │
                       ▼
                    Runtime
               body.py → organs.py
                       │
                       ▼
                  Repositories
                       │
                       ▼
                  PostgreSQL
                       │
                       ▼
              Infrastructure
        systemd · nginx · HTTPS · VPS
Domain Architecture

Each domain owns its business meaning and state transitions.

Domain	Question answered	Key objects
D1 — Home Management	Who belongs to this Home?	Home, Resident, Cook
D2 — Meal Preferences	What does each resident generally prefer?	MealPreference
D3 — Daily Meal Coordination	What will this Home eat on a particular date?	HomeMenu, DailyMealPoll, MealVote, MealSummary, MealPlan
D1

Defines the household boundary.

Owns:

Home creation
Resident management
Cook management
Household membership
D2

Stores long-term resident preferences.

Each resident maintains exactly five unique favourite meals.

D2 retains preference history while exposing the current preference state consumed by D3.

D3

Turns long-term preferences into an operational decision.

It owns:

menu construction
meal recommendation
poll creation
voting
poll closure
winner selection
MealSummary
MealPlan
Daily Decision Loop
D2 Preferences
      ↓
HomeMenu
      ↓
MealRecommendationEngine
      ↓
Top 3 meal choices
      ↓
DailyMealPoll
      ↓
Telegram
      ↓
Residents vote
      ↓
C/T reconciliation
      ↓
D3 MealVote
      ↓
Poll closes
      ↓
MealSummary
      ↓
MealPlan
      ↓
Transport
      ↓
Telegram result

The important distinction is that Telegram votes are observations, not authoritative business state.

A Telegram vote becomes a MealVote only after the transport identity and poll relationship have been reconciled.

Coordination Layer

MealBot's external coordination is divided into explicit responsibilities.

N1 — Home Bootstrap

Triggered by:

/bootstrap

N1 observes an unknown Telegram group and begins Home bootstrap.

/bootstrap
    ↓
Resolve Telegram chat
    ↓
Check Home link
    ↓
Observe Telegram members
    ↓
Select Home host
    ↓
Configure Home
    ↓
Persist Telegram ↔ Home relationship

The same group does not repeatedly bootstrap once an active transport relationship exists.

N2 — Resident Reconciliation

N2 continuously reconciles Telegram membership against MealBot's resident model.

Telegram members
       ↓
Observed identities
       ↓
Compare with persisted identities
       ↓
Missing resident?
       ↓
Configuration / onboarding

N2 runs independently under systemd.

N3 — Daily Poll Coordination

N3 handles the external Telegram representation of D3 polls.

The scheduled workflow creates tomorrow's D3 poll.

The independent Telegram poll reconciler then:

discovers open D3 polls
creates their Telegram representation
persists the transport binding
observes Telegram votes
maps Telegram residents to MealBot residents
reconciles votes into D3
stops Telegram polls when D3 closes

The Telegram poll is therefore an external representation of a D3 business object rather than the business object itself.

N4 — Daily Poll Closure

N4 closes the daily decision.

It does not contain a hardcoded meal date.

Instead:

Schedule
   ↓
Discover latest poll
   ↓
Is latest poll OPEN?
   ├── No → 404
   └── Yes
        ↓
      Close
        ↓
   MealSummary
        ↓
     MealPlan
        ↓
     Delivery

The discovery rule is deliberately strict:

Only the latest poll by meal date can be returned.

An older OPEN poll is never selected if a newer poll already exists in another state.

This prevents stale historical polls from being accidentally closed and delivered.

Persistence

MealBot uses PostgreSQL as durable business and transport memory.

The current schema contains 13 tables.

D1 — Household
homes
residents
cooks
D2 — Preferences
meal_preferences
meal_preference_items
D3 — Daily Decision
daily_meal_polls
poll_options
meal_votes
meal_summaries
meal_plans
Transport
transport_endpoints
resident_transport_identities
transport_poll_bindings

The separation is intentional:

Business Identity
       ≠
Transport Identity

A Telegram user is not automatically a MealBot Resident.

A Telegram poll is not automatically a D3 DailyMealPoll.

A Telegram vote is not automatically a D3 MealVote.

The C/T layer reconciles these representations.

Each domain owns its repository and SQL rather than relying on one shared generic data-access layer.

Runtime Architecture
HTTP Request
     ↓
body.py
     ↓
organs.py
     ↓
D1 / D2 / D3
     ↓
Repositories
     ↓
PostgreSQL
body.py

HTTP transport boundary.

Responsible for:

receiving requests
validating request models
returning HTTP responses
organs.py

Runtime orchestration.

Responsible for:

cross-domain workflows
resolving entities
coordinating business operations
invoking transport delivery
brain.py

Reserved for cross-domain intelligence and reasoning.

It is not required for the deterministic D1/D2/D3 daily decision loop.

Deployment Architecture

MealBot is deployed to a Linux VPS.

Internet
   ↓
HTTPS
   ↓
nginx
   ↓
Uvicorn
   ↓
FastAPI
   ↓
MealBot

Systemd provides process lifecycle management.

Linux
 ├── mealbot.service
 ├── mealbot-telegram-poll.service
 └── mealbot-telegram-resident.service

The D3 Telegram poll reconciler also runs continuously under systemd with automatic restart.

The infrastructure therefore does not depend on a terminal session remaining open.

Production Services
Service	Responsibility
mealbot.service	FastAPI/Uvicorn application
mealbot-telegram-poll.service	Telegram D3 poll reconciliation and vote observation
mealbot-telegram-resident.service	N2 resident reconciliation

All services run from the production virtual environment and are managed by systemd.

nginx provides external routing and HTTPS termination.

Frontend

MealBot also contains a manually constructed configuration frontend.

The frontend communicates with the deployed API:

Frontend
   ↓
FastAPI
   ↓
D1
   ↓
PostgreSQL

The frontend was intentionally built separately from the backend so that the existing domain architecture could be expressed through a real client rather than hidden behind a framework abstraction.

Production Verification

The system has been verified across the complete daily workflow:

Resident preferences
        ↓
D3 recommendation
        ↓
Telegram poll
        ↓
Telegram vote
        ↓
Transport identity reconciliation
        ↓
D3 MealVote
        ↓
Poll closure
        ↓
MealSummary
        ↓
MealPlan
        ↓
Meal result delivery

The Home onboarding flow was also verified from an intentionally empty database, including host reuse, resident creation, Telegram identity persistence, and D2 preference persistence.

The deployed system has also been exercised through real PostgreSQL persistence and systemd-managed services.

Engineering Principles Demonstrated

MealBot is intentionally built around several principles.

Business state is authoritative

External providers represent reality.

They do not define business truth.

Transport is replaceable

Telegram is currently the transport environment.

The D1/D2/D3 domains do not depend on Telegram's data model.

Reconciliation is explicit

External state and internal state are treated as separate representations that must be reconciled.

Domains own meaning

D1, D2 and D3 own their business rules and transitions.

Runtime owns coordination

Cross-domain orchestration belongs outside individual domains.

Persistence owns memory

PostgreSQL stores durable business and transport facts.

Infrastructure owns liveness

systemd keeps processes alive.

nginx routes traffic.

Linux provides the operating environment.

Engineering OS

MealBot is the first production embodiment of a broader Engineering OS built around the idea that software systems are cooperating organisms with explicit boundaries.

The architecture evolved from:

Body → Organs → Brain

into a broader model:

Reality
   ↓
Coordination
   ↓
Business Domains
   ↓
Runtime
   ↓
Persistence
   ↓
Infrastructure
   ↓
Deployment

The goal is not to create abstraction for its own sake.

The goal is to make responsibility visible.

Current Status

MVP — Production Deployed

D1 Home Management              ✅
D2 Meal Preferences             ✅
D3 Daily Meal Coordination      ✅

N1 Home Bootstrap               ✅
N2 Resident Reconciliation      ✅
N3 Telegram Poll Coordination   ✅
N4 Daily Poll Closure            ✅

PostgreSQL                      ✅
Telegram integration            ✅
n8n orchestration               ✅
FastAPI                         ✅
systemd                         ✅
nginx                           ✅
HTTPS                           ✅
Linux VPS                       ✅
Configuration frontend          ✅

The MVP daily loop is operational:

Preferences
→ Poll
→ Vote
→ Reconcile
→ Close
→ Plan
→ Deliver
Known Limitations

The MVP intentionally leaves several areas for future hardening:

Home creation and transport-endpoint creation are not yet one atomic transaction.
Host detection can be strengthened with authenticated, short-lived onboarding context.
Telegram workflows need broader idempotency and retry guarantees.
Authentication and authorization are not yet implemented as a general application layer.
Integration-test coverage is still limited.
Operational observability and structured retry logging can be expanded.
The meal recommendation strategy can evolve beyond the current top-three model.
Cook delivery can be expanded beyond the current Telegram result flow.

These are hardening and expansion areas, not prerequisites for the current MVP lifecycle.

Tech Stack
Python
FastAPI
Pydantic
PostgreSQL
Telegram Bot API
Telethon
n8n
nginx
systemd
Linux VPS
HTML / CSS / TypeScript
Git / GitHub
Why this project?

MealBot is not primarily a demonstration of FastAPI.

It is a demonstration of business-first systems engineering.

The interesting problem is not:

"Can an API create a poll?"

The interesting problem is:

How do you build a system where human actions occur in an external environment, those actions are observed and reconciled, business meaning remains internally authoritative, state survives process failure, and the entire organism continues operating without a human attached to it?

MealBot is one concrete answer.

Author

Farhan Ahmed Mudgal

Building Engineering OS one deployed project at a time.
