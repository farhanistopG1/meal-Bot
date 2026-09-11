-- MealBot PostgreSQL schema
-- Status: ready for implementation
-- Run through scripts/create_postgres_schema.py or with psql.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS homes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    status TEXT NOT NULL CHECK (status IN ('Active', 'Archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS residents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL REFERENCES homes(id) ON DELETE RESTRICT,
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    phone TEXT NOT NULL CHECK (btrim(phone) <> ''),
    status TEXT NOT NULL CHECK (status IN ('Active', 'Archived')),
    onboarded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (home_id, phone),
    UNIQUE (home_id, id)
);

CREATE TABLE IF NOT EXISTS cooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL REFERENCES homes(id) ON DELETE RESTRICT,
    name TEXT NOT NULL CHECK (btrim(name) <> ''),
    phone TEXT NOT NULL CHECK (btrim(phone) <> ''),
    status TEXT NOT NULL CHECK (status IN ('Active', 'Archived')),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (home_id),
    UNIQUE (home_id, id)
);

CREATE TABLE IF NOT EXISTS meal_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resident_id UUID NOT NULL REFERENCES residents(id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK (version > 0),
    protein_preference TEXT NOT NULL CHECK (
        protein_preference IN ('vegetarian', 'egg', 'non_vegetarian')
    ),
    spice_preference TEXT NOT NULL CHECK (
        spice_preference IN ('mild', 'medium', 'spicy')
    ),
    is_current BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    superseded_at TIMESTAMPTZ,
    CHECK (
        (is_current AND superseded_at IS NULL)
        OR (NOT is_current AND superseded_at IS NOT NULL)
    ),
    UNIQUE (resident_id, version)
);

CREATE UNIQUE INDEX IF NOT EXISTS one_current_meal_preference_per_resident
    ON meal_preferences (resident_id)
    WHERE is_current;

CREATE TABLE IF NOT EXISTS meal_preference_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meal_preference_id UUID NOT NULL REFERENCES meal_preferences(id) ON DELETE CASCADE,
    meal_name TEXT NOT NULL CHECK (meal_name = lower(btrim(meal_name)) AND meal_name <> ''),
    position SMALLINT NOT NULL CHECK (position BETWEEN 1 AND 5),
    UNIQUE (meal_preference_id, meal_name),
    UNIQUE (meal_preference_id, position)
);

CREATE TABLE IF NOT EXISTS daily_meal_polls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL REFERENCES homes(id) ON DELETE RESTRICT,
    meal_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Draft', 'Open', 'Closed')),
    opened_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    CHECK (
        (status = 'Draft' AND opened_at IS NULL AND closed_at IS NULL)
        OR (status = 'Open' AND opened_at IS NOT NULL AND closed_at IS NULL)
        OR (status = 'Closed' AND opened_at IS NOT NULL AND closed_at IS NOT NULL)
    ),
    CHECK (closed_at IS NULL OR closed_at >= opened_at),
    UNIQUE (home_id, meal_date),
    UNIQUE (home_id, id)
);

CREATE TABLE IF NOT EXISTS poll_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poll_id UUID NOT NULL REFERENCES daily_meal_polls(id) ON DELETE RESTRICT,
    meal_name TEXT NOT NULL CHECK (meal_name = lower(btrim(meal_name)) AND meal_name <> ''),
    rank SMALLINT NOT NULL CHECK (rank BETWEEN 1 AND 3),
    UNIQUE (poll_id, meal_name),
    UNIQUE (poll_id, rank),
    UNIQUE (poll_id, id)
);

CREATE TABLE IF NOT EXISTS meal_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL,
    poll_id UUID NOT NULL,
    poll_option_id UUID NOT NULL,
    resident_id UUID NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (poll_id, resident_id),
    FOREIGN KEY (home_id, poll_id)
        REFERENCES daily_meal_polls (home_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (home_id, resident_id)
        REFERENCES residents (home_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (poll_id, poll_option_id)
        REFERENCES poll_options (poll_id, id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS meal_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL,
    poll_id UUID NOT NULL UNIQUE,
    winning_poll_option_id UUID NOT NULL,
    total_votes INTEGER NOT NULL CHECK (total_votes >= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (home_id, id),
    FOREIGN KEY (home_id, poll_id)
        REFERENCES daily_meal_polls (home_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (poll_id, winning_poll_option_id)
        REFERENCES poll_options (poll_id, id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS meal_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL,
    meal_summary_id UUID NOT NULL UNIQUE,
    cook_id UUID NOT NULL,
    meal_date DATE NOT NULL,
    meal_name TEXT NOT NULL CHECK (meal_name = lower(btrim(meal_name)) AND meal_name <> ''),
    vote_count INTEGER NOT NULL CHECK (vote_count >= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (home_id, meal_date),
    FOREIGN KEY (home_id, meal_summary_id)
        REFERENCES meal_summaries (home_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (home_id, cook_id)
        REFERENCES cooks (home_id, id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS transport_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL REFERENCES homes(id) ON DELETE RESTRICT,
    provider TEXT NOT NULL CHECK (provider = 'telegram'),
    purpose TEXT NOT NULL CHECK (purpose IN ('resident_poll', 'cook_notification')),
    external_destination_id TEXT NOT NULL CHECK (btrim(external_destination_id) <> ''),
    status TEXT NOT NULL CHECK (status IN ('Active', 'Inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (home_id, provider, purpose),
    UNIQUE (home_id, id)
);

CREATE TABLE IF NOT EXISTS resident_transport_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resident_id UUID NOT NULL REFERENCES residents(id) ON DELETE RESTRICT,
    provider TEXT NOT NULL CHECK (provider = 'telegram'),
    external_user_id TEXT NOT NULL CHECK (btrim(external_user_id) <> ''),
    status TEXT NOT NULL CHECK (status IN ('Active', 'Inactive')),
    linked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (resident_id, provider),
    UNIQUE (provider, external_user_id)
);

CREATE TABLE IF NOT EXISTS transport_poll_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_id UUID NOT NULL,
    daily_meal_poll_id UUID NOT NULL,
    transport_endpoint_id UUID NOT NULL,
    provider_poll_id TEXT NOT NULL CHECK (btrim(provider_poll_id) <> ''),
    provider_message_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,
    CHECK (closed_at IS NULL OR closed_at >= created_at),
    UNIQUE (daily_meal_poll_id, transport_endpoint_id),
    UNIQUE (transport_endpoint_id, provider_poll_id),
    FOREIGN KEY (home_id, daily_meal_poll_id)
        REFERENCES daily_meal_polls (home_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (home_id, transport_endpoint_id)
        REFERENCES transport_endpoints (home_id, id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS daily_meal_polls_open_by_home
    ON daily_meal_polls (home_id, meal_date)
    WHERE status = 'Open';

CREATE INDEX IF NOT EXISTS meal_votes_by_poll
    ON meal_votes (poll_id);
