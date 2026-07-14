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
CREATE TYPE concern_feedback_type AS ENUM ('worried', 'routine', 'mute');

CREATE TABLE portfolio_relationships (
    user_id TEXT NOT NULL REFERENCES users(id),
    stock_id TEXT NOT NULL REFERENCES stocks(id),
    relationship portfolio_relationship_type NOT NULL,
    importance relationship_importance_type NOT NULL DEFAULT 'unknown',
    average_cost NUMERIC(14, 4),
    shares NUMERIC(18, 4),
    source TEXT NOT NULL CHECK (source = 'user_confirmed'),
    confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, stock_id)
);

CREATE TABLE action_cards (
    id TEXT PRIMARY KEY,
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
    card_id TEXT NOT NULL REFERENCES action_cards(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    action TEXT NOT NULL CHECK (action IN ('confirmed_holding', 'watch_only', 'irrelevant')),
    occurred_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (card_id, user_id)
);

CREATE TABLE concern_feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    stock_id TEXT NOT NULL REFERENCES stocks(id),
    card_id TEXT REFERENCES action_cards(id),
    concern concern_feedback_type NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE interaction_events (
    event_id UUID PRIMARY KEY,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id),
    stock_id TEXT REFERENCES stocks(id),
    card_id TEXT REFERENCES action_cards(id),
    surface TEXT NOT NULL,
    action TEXT,
    source_date DATE,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE demo_news (
    id TEXT PRIMARY KEY,
    stock_id TEXT NOT NULL REFERENCES stocks(id),
    title TEXT NOT NULL,
    summary TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    source_name TEXT NOT NULL,
    is_demo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_interaction_events_user_time ON interaction_events (user_id, occurred_at DESC);
CREATE INDEX idx_interaction_events_type_time ON interaction_events (event_type, occurred_at DESC);
CREATE INDEX idx_concern_feedback_user_time ON concern_feedback (user_id, occurred_at DESC);

INSERT INTO users (id, display_name) VALUES ('LEO', 'LEO');
INSERT INTO stocks (id, name, industry) VALUES ('2382', '廣達', '電腦及週邊設備');

INSERT INTO action_cards (id, user_id, stock_id, card_type, title, summary, evidence, source_date)
VALUES (
    'signal-divergence-2382',
    'LEO',
    '2382',
    'signal_divergence',
    '市場很樂觀，法人卻仍在調節',
    '近 20 日法人賣超，但近 7 日明確多空貼文高度偏多。',
    '["institutional_net_20d=-60265", "community_bullish_ratio_7d=0.939"]'::JSONB,
    '2025-12-31'
);

INSERT INTO demo_news (id, stock_id, title, summary, published_at, source_name, is_demo) VALUES
    ('news-001', '2382', '廣達 AI 伺服器展望與市場關注焦點', '用於驗證 news_open 與 AI Context。', '2025-12-31T14:30:00+08:00', 'MVP Demo Feed', TRUE),
    ('news-002', '2382', '法人籌碼短線回補，中期動向仍待觀察', '示範摘要，不構成投資建議。', '2025-12-30T18:00:00+08:00', 'MVP Demo Feed', TRUE);
