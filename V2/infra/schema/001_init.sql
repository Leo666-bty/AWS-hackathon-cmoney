-- Mindfolio V2 schema (PostgreSQL, self-hosted on the EC2 instance).
-- Market data is file-based; only user-confirmed state is persisted here.
-- Constitution V: only trades the user marked "holding" and consented to may be
-- written as confirmed holdings; anonymous sessions and member profiles use
-- different identifiers (user_id carries whichever the caller supplies).

CREATE TABLE IF NOT EXISTS confirmed_holdings (
    user_id      TEXT        NOT NULL,
    stock_id     TEXT        NOT NULL,
    source       TEXT        NOT NULL DEFAULT 'user_confirmed'
                             CHECK (source = 'user_confirmed'),
    confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, stock_id)
);

CREATE INDEX IF NOT EXISTS idx_confirmed_holdings_user
    ON confirmed_holdings (user_id, confirmed_at DESC);

ALTER TABLE confirmed_holdings
    ADD COLUMN IF NOT EXISTS source_report_id TEXT,
    ADD COLUMN IF NOT EXISTS last_reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE TABLE IF NOT EXISTS reconstruction_reports (
    report_id        TEXT        PRIMARY KEY,
    claim_token_hash TEXT        NOT NULL,
    trades           JSONB       NOT NULL,
    result           JSONB       NOT NULL,
    narrative        JSONB       NOT NULL,
    claimed_by       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    claimed_at       TIMESTAMPTZ,
    expires_at       TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reconstruction_reports_member
    ON reconstruction_reports (claimed_by, created_at DESC)
    WHERE claimed_by IS NOT NULL;

CREATE TABLE IF NOT EXISTS action_card_feedback (
    member_id  TEXT        NOT NULL,
    card_id    TEXT        NOT NULL,
    preference TEXT        NOT NULL
                            CHECK (preference IN ('review_evidence', 'routine', 'mute')),
    saved_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (member_id, card_id)
);

CREATE TABLE IF NOT EXISTS interaction_events (
    event_id    TEXT        PRIMARY KEY,
    member_id   TEXT,
    session_id  TEXT        NOT NULL,
    event_type  TEXT        NOT NULL,
    surface     TEXT        NOT NULL,
    action      TEXT,
    stock_id    TEXT,
    occurred_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata    JSONB       NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_interaction_events_member_time
    ON interaction_events (member_id, occurred_at DESC);
