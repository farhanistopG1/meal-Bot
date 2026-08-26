# D1 — Home Management Architecture

## Mission

Own the identity and membership of a household: its Home, Residents, and Cook.

## Lifecycle

```text
Create Home
    ↓
Add initial Resident
    ↓
Assign Cook
    ↓
Add or remove Residents as the household changes
```

## Business Objects

- `Home`: the household, its status, residents, and assigned cook.
- `Resident`: a person who belongs to a home and can save meal preferences.
- `Cook`: the person assigned to prepare the selected meal.

## Domain Boundaries

D1 does not own meal preferences, polling, votes, meal summaries, or meal plans.
