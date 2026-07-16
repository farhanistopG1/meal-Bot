# 🍽️ MealBot

> The first production implementation of **Engineering OS**.

MealBot is a domain-driven backend application that manages the complete lifecycle of home meal management.

Rather than being built around frameworks, MealBot is built around **business responsibilities**. Every component exists because the business requires it—not because the technology does.

---

# Mission

MealBot exists to validate the Engineering OS architecture by implementing a real business.

Current Goal:

```
Manage the complete lifecycle of home meal management.
```

---

# Current Progress

## ✅ D1 — Home Management

Implemented:

- Home Business Object
- Resident Business Object
- Cook Business Object
- Business Behaviors
- Business Rules
- Business Workflow
- Repository (In-Memory)
- Runtime Integration
- FastAPI Endpoint

Request Flow

```
HTTP Request
        ↓
FastAPI Runtime
        ↓
Pydantic Validation
        ↓
Runtime Orchestrator
        ↓
D1 Home Management
        ↓
Repository
        ↓
HTTP Response
```

---

# Architecture

MealBot follows **Engineering OS**.

```
Reality
        ↓
Business Domain
        ↓
Business Objects
        ↓
Business Behaviors
        ↓
Business Workflows
        ↓
Runtime
        ↓
Persistence
        ↓
Infrastructure
        ↓
Deployment
```

---

# Runtime Structure

```
Project Root

body.py
    Transport Layer

organs.py
    Runtime Orchestration

brain.py
    Cross-Domain Intelligence

database.py
    Runtime Infrastructure
```

---

# Domain Structure

Every business capability owns its own implementation.

```
D1_HOME_MANAGEMENT/

body.py
    Business Objects

organs.py
    Business Workflow

database.py
    Repository
```

Future Domains

```
D2_MEAL_PLANNING

D3_NOTIFICATIONS

...
```

---

# Engineering Principles

MealBot follows one simple philosophy.

**Responsibilities First. Technology Second.**

Examples:

Transport belongs to Runtime.

Business belongs to Domains.

Persistence belongs to Repositories.

Infrastructure belongs to Deployment.

Every implementation can change.

Responsibilities remain stable.

---

# Technologies

- Python
- FastAPI
- Pydantic
- Uvicorn

Current Persistence:

- In-Memory Repository

Future:

- PostgreSQL

---

# Roadmap

- [x] D1 Home Management
- [ ] D2 Meal Planning
- [ ] D3 Notifications
- [ ] PostgreSQL Persistence
- [ ] Authentication
- [ ] Deployment
- [ ] Docker
- [ ] Monitoring

---

# Why this project?

MealBot is not intended to demonstrate FastAPI.

It is intended to demonstrate **software engineering through business-first architecture.**

The project explores how independent business domains, runtime orchestration, and clear ownership boundaries can produce maintainable backend systems.

---

# Author

Farhan Ahmed Mudgal

Building Engineering OS one deployed project at a time.
