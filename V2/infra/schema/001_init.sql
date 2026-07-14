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
