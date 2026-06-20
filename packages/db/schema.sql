-- ================================================================
-- Carbon Footprint Platform -- Database Schema
-- PostgreSQL 15+
-- Apply with: psql $DATABASE_URL -f schema.sql
-- ================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================================
-- ENUMERATIONS
-- ================================================================

CREATE TYPE auth_provider_type   AS ENUM ('email', 'google', 'apple');
CREATE TYPE challenge_status     AS ENUM ('active', 'completed', 'failed');
CREATE TYPE challenge_difficulty AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE notification_type    AS ENUM ('reminder', 'streak_warning', 'achievement', 'weekly_digest', 'challenge_update');
CREATE TYPE notification_channel AS ENUM ('push', 'email', 'in_app');
CREATE TYPE org_role             AS ENUM ('admin', 'member');

-- ================================================================
-- 1. USERS -- IDENTITY, PROFILE & SECURITY
-- ================================================================
CREATE TABLE users (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email             VARCHAR(255) UNIQUE NOT NULL,
    password_hash     VARCHAR(255),
    auth_provider     auth_provider_type DEFAULT 'email',
    provider_user_id  VARCHAR(255),
    first_name        VARCHAR(100),
    last_name         VARCHAR(100),
    username          VARCHAR(50) UNIQUE,
    avatar_url        TEXT,
    region_code       VARCHAR(10) DEFAULT 'GLOBAL',
    current_streak    INT DEFAULT 0,
    highest_streak    INT DEFAULT 0,
    deleted_at        TIMESTAMP WITH TIME ZONE,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_auth_consistency CHECK (
        (auth_provider = 'email'  AND password_hash    IS NOT NULL)
     OR (auth_provider <> 'email' AND provider_user_id IS NOT NULL)
    )
);

-- ================================================================
-- 2. EMISSION FACTORS -- REGION-AWARE CALCULATION CONSTANTS
-- ================================================================
CREATE TABLE emission_factors (
    id             SERIAL PRIMARY KEY,
    category       VARCHAR(50)   NOT NULL,
    activity_type  VARCHAR(100)  NOT NULL,
    unit           VARCHAR(20)   NOT NULL,
    co2e_per_unit  NUMERIC(8, 4) NOT NULL,
    region_code    VARCHAR(10)   DEFAULT 'GLOBAL',
    source         VARCHAR(100),
    valid_from     DATE,
    valid_to       DATE,
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_activity_region UNIQUE (activity_type, region_code)
);

-- ================================================================
-- 3. BASELINES -- USER FOOTPRINT BASELINE HISTORY
-- ================================================================
CREATE TABLE baselines (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
    total_co2e        NUMERIC(6, 2) NOT NULL,
    housing_co2e      NUMERIC(5, 2),
    transport_co2e    NUMERIC(5, 2),
    diet_co2e         NUMERIC(5, 2),
    consumption_co2e  NUMERIC(5, 2),
    quiz_responses    JSONB,
    is_current        BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Only one active baseline per user
CREATE UNIQUE INDEX idx_baselines_current_user
    ON baselines (user_id) WHERE is_current = TRUE;

-- ================================================================
-- 4. USER GOALS -- PERSONAL ANNUAL REDUCTION TARGETS
-- ================================================================
CREATE TABLE user_goals (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID REFERENCES users(id) ON DELETE CASCADE,
    baseline_id    UUID REFERENCES baselines(id),
    target_co2e    NUMERIC(6, 2) NOT NULL,
    reduction_pct  NUMERIC(5, 2),
    target_year    SMALLINT NOT NULL,
    is_active      BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- 5. DAILY LOGS -- HISTORICAL ACTIVITY ENTRIES
-- ================================================================
CREATE TABLE daily_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID REFERENCES users(id) ON DELETE CASCADE,
    log_date            DATE NOT NULL,
    category            VARCHAR(50)   NOT NULL,
    activity_type       VARCHAR(100)  NOT NULL,
    emission_factor_id  INT REFERENCES emission_factors(id),
    quantity            NUMERIC(10, 2) NOT NULL,
    total_co2e          NUMERIC(10, 3),
    is_estimated        BOOLEAN DEFAULT FALSE,
    metadata            JSONB,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_user_date_activity UNIQUE (user_id, log_date, activity_type)
);

-- ================================================================
-- 6. ECO CHALLENGES -- MASTER CHALLENGE CATALOGUE
-- ================================================================
CREATE TABLE eco_challenges (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title         VARCHAR(255) NOT NULL,
    description   TEXT NOT NULL,
    category      VARCHAR(50) NOT NULL,
    difficulty    challenge_difficulty DEFAULT 'medium',
    target_value  INT NOT NULL,
    metric_type   VARCHAR(50) NOT NULL,
    co2e_reward   NUMERIC(6, 2),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- 7. USER CHALLENGE PROGRESSION
-- ================================================================
CREATE TABLE user_challenges (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    challenge_id  UUID REFERENCES eco_challenges(id) ON DELETE CASCADE,
    status        challenge_status DEFAULT 'active',
    progress      INT DEFAULT 0,
    started_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at  TIMESTAMP WITH TIME ZONE,
    failed_at     TIMESTAMP WITH TIME ZONE,

    CONSTRAINT unique_user_challenge UNIQUE (user_id, challenge_id)
);

-- ================================================================
-- 8. NOTIFICATIONS -- SCHEDULED NUDGE & ALERT LEDGER
-- ================================================================
CREATE TABLE notifications (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    type          notification_type    NOT NULL,
    channel       notification_channel NOT NULL,
    title         VARCHAR(255) NOT NULL,
    body          TEXT,
    scheduled_at  TIMESTAMP WITH TIME ZONE,
    sent_at       TIMESTAMP WITH TIME ZONE,
    read_at       TIMESTAMP WITH TIME ZONE,
    metadata      JSONB,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- 9. ORGANIZATIONS -- B2B WORKSPACE ACCOUNTS
-- ================================================================
CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    logo_url    TEXT,
    plan        VARCHAR(50) DEFAULT 'business',
    deleted_at  TIMESTAMP WITH TIME ZONE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE organization_members (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id  UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id          UUID REFERENCES users(id) ON DELETE CASCADE,
    role             org_role DEFAULT 'member',
    joined_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_org_member UNIQUE (organization_id, user_id)
);

-- ================================================================
-- INDEXES
-- ================================================================
CREATE INDEX idx_daily_logs_user_date     ON daily_logs (user_id, log_date DESC);
CREATE INDEX idx_daily_logs_category      ON daily_logs (user_id, category);
CREATE INDEX idx_user_challenges_active   ON user_challenges (user_id) WHERE status = 'active';
CREATE INDEX idx_emission_factors_region  ON emission_factors (activity_type, region_code);
CREATE INDEX idx_notifications_unread     ON notifications (user_id, scheduled_at) WHERE read_at IS NULL;
CREATE INDEX idx_users_active             ON users (id) WHERE deleted_at IS NULL;

-- ================================================================
-- TRIGGER 1: Auto-calculate CO2e on daily_log insert/update
--   Resolution: user region -> GLOBAL fallback -> NULL + WARNING
-- ================================================================
CREATE OR REPLACE FUNCTION calculate_log_co2e()
RETURNS TRIGGER AS $$
DECLARE
    v_factor_id    INT;
    v_factor       NUMERIC(8, 4);
    v_user_region  VARCHAR(10);
BEGIN
    SELECT region_code INTO v_user_region FROM users WHERE id = NEW.user_id;
    v_user_region := COALESCE(v_user_region, 'GLOBAL');

    -- Try region-specific factor first
    SELECT id, co2e_per_unit
      INTO v_factor_id, v_factor
      FROM emission_factors
     WHERE activity_type = NEW.activity_type
       AND region_code   = v_user_region
       AND (valid_to IS NULL OR valid_to >= CURRENT_DATE);

    -- Fallback to GLOBAL if region-specific not found
    IF v_factor IS NULL AND v_user_region <> 'GLOBAL' THEN
        SELECT id, co2e_per_unit
          INTO v_factor_id, v_factor
          FROM emission_factors
         WHERE activity_type = NEW.activity_type
           AND region_code   = 'GLOBAL'
           AND (valid_to IS NULL OR valid_to >= CURRENT_DATE);

        IF v_factor IS NOT NULL THEN
            NEW.is_estimated := TRUE;
        END IF;
    END IF;

    IF v_factor IS NOT NULL THEN
        NEW.total_co2e         := NEW.quantity * v_factor;
        NEW.emission_factor_id := v_factor_id;
    ELSE
        RAISE WARNING 'No emission factor for activity_type=% region=% -- total_co2e left NULL',
            NEW.activity_type, v_user_region;
        NEW.total_co2e    := NULL;
        NEW.is_estimated  := TRUE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calculate_co2e
BEFORE INSERT OR UPDATE ON daily_logs
FOR EACH ROW EXECUTE FUNCTION calculate_log_co2e();

-- ================================================================
-- TRIGGER 2: Auto-retire old baselines when a new one is inserted
-- ================================================================
CREATE OR REPLACE FUNCTION deactivate_old_baseline()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE baselines
       SET is_current = FALSE
     WHERE user_id    = NEW.user_id
       AND id        <> NEW.id
       AND is_current = TRUE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_deactivate_old_baseline
BEFORE INSERT ON baselines
FOR EACH ROW EXECUTE FUNCTION deactivate_old_baseline();
