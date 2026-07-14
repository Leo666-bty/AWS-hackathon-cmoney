CREATE TABLE users (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE stocks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TYPE portfolio_relationship_type AS ENUM ('holding', 'watch_only', 'irrelevant');
CREATE TYPE relationship_importance_type AS ENUM ('core', 'normal', 'small', 'unknown');

CREATE TABLE portfolio_relationships (
    user_id TEXT NOT NULL REFERENCES users(id),
    stock_id TEXT NOT NULL REFERENCES stocks(id),
    relationship portfolio_relationship_type NOT NULL,
    importance relationship_importance_type NOT NULL DEFAULT 'unknown',
    source TEXT NOT NULL CHECK (source = 'user_confirmed'),
    confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, stock_id)
);

CREATE TABLE action_cards (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    stock_id TEXT NOT NULL REFERENCES stocks(id),
    card_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence JSONB NOT NULL,
    source_date DATE NOT NULL,
    shown_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE card_feedback (
    id BIGSERIAL PRIMARY KEY,
    card_id UUID NOT NULL REFERENCES action_cards(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    action portfolio_relationship_type NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (card_id, user_id)
);

INSERT INTO users (id, display_name) VALUES ('LEO', 'LEO');
INSERT INTO stocks (id, name, industry) VALUES
    ('2382', '廣達', '電腦及週邊設備');
