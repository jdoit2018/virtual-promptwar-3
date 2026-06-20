-- Enable secure cryptographic UUID extensions
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
-- 1. USERS â€” IDENTITY, PROFILE & SECURITY
-- ================================================================
CREATE TABLE users (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email             VARCHAR(255) UNIQUE NOT NULL,
    password_hash     VARCHAR(255),                  -- NULL for OAuth-only accounts
    auth_provider     auth_provider_type DEFAULT 'email',
    provider_user_id  VARCHAR(255),                  -- External OAuth subject identifier
    first_name        VARCHAR(100),
    last_name         VARCHAR(100),
    username          VARCHAR(50) UNIQUE,
    avatar_url        TEXT,
    region_code       VARCHAR(10) DEFAULT 'GLOBAL',  -- ISO 3166-1 alpha-2 or 'GLOBAL'
    current_streak    INT DEFAULT 0,
    highest_streak    INT DEFAULT 0,
    deleted_at        TIMESTAMP WITH TIME ZONE,      -- Soft-delete for GDPR right-to-erasure
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Enforce auth consistency: email users must have password_hash;
    -- OAuth users must have provider_user_id
    CONSTRAINT chk_auth_consistency CHECK (
        (auth_provider = 'email'  AND password_hash    IS NOT NULL)
     OR (auth_provider <> 'email' AND provider_user_id IS NOT NULL)
    )
);

-- ================================================================
-- 2. EMISSION FACTORS â€” REGION-AWARE CALCULATION CONSTANTS
-- ================================================================
CREATE TABLE emission_factors (
    id             SERIAL PRIMARY KEY,
    category       VARCHAR(50)  NOT NULL,             -- 'transportation', 'diet', 'energy', 'consumption'
    activity_type  VARCHAR(100) NOT NULL,             -- 'gas_car_mile', 'beef_meal', 'kwh_coal_grid'
    unit           VARCHAR(20)  NOT NULL,             -- 'mile', 'serving', 'kwh'
    co2e_per_unit  NUMERIC(8, 4) NOT NULL,            -- kg CO2e per unit
    region_code    VARCHAR(10)  DEFAULT 'GLOBAL',     -- ISO 3166-1 alpha-2 or 'GLOBAL' fallback
    source         VARCHAR(100),                      -- 'Climatiq', 'DEFRA 2024', 'EPA'
    valid_from     DATE,                              -- Factor validity window start
    valid_to       DATE,                              -- NULL = currently active
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_activity_region UNIQUE (activity_type, region_code)
);

-- ================================================================
-- 3. BASELINES â€” USER FOOTPRINT BASELINE HISTORY
--    Replaces the deprecated static baseline_co2e scalar on users.
-- ================================================================
CREATE TABLE baselines (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
    total_co2e        NUMERIC(6, 2) NOT NULL,          -- Total annual MT CO2e
    housing_co2e      NUMERIC(5, 2),                   -- Housing pillar sub-total
    transport_co2e    NUMERIC(5, 2),                   -- Transportation pillar sub-total
    diet_co2e         NUMERIC(5, 2),                   -- Diet pillar sub-total
    consumption_co2e  NUMERIC(5, 2),                   -- Consumption pillar sub-total
    quiz_responses    JSONB,                            -- Full answer snapshot for audit trail
    is_current        BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enforce single active baseline per user
CREATE UNIQUE INDEX idx_baselines_current_user
    ON baselines (user_id) WHERE is_current = TRUE;

-- ================================================================
-- 4. USER GOALS â€” PERSONAL ANNUAL REDUCTION TARGETS
-- ================================================================
CREATE TABLE user_goals (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID REFERENCES users(id) ON DELETE CASCADE,
    baseline_id    UUID REFERENCES baselines(id),      -- Anchored to a specific baseline snapshot
    target_co2e    NUMERIC(6, 2) NOT NULL,              -- Absolute target MT CO2e/year
    reduction_pct  NUMERIC(5, 2),                      -- Derived: (1 - target/baseline) * 100
    target_year    SMALLINT NOT NULL,
    is_active      BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- 5. DAILY LOGS â€” HISTORICAL ACTIVITY ENTRIES
-- ================================================================
CREATE TABLE daily_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID REFERENCES users(id) ON DELETE CASCADE,
    log_date            DATE NOT NULL,
    category            VARCHAR(50)  NOT NULL,
    activity_type       VARCHAR(100) NOT NULL,
    emission_factor_id  INT REFERENCES emission_factors(id),  -- FK replaces fragile string reference
    quantity            NUMERIC(10, 2) NOT NULL,
    total_co2e          NUMERIC(10, 3),                       -- Nullable: NULL signals unresolved factor
    is_estimated        BOOLEAN DEFAULT FALSE,                 -- TRUE when GLOBAL fallback factor applied
    metadata            JSONB,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_user_date_activity UNIQUE (user_id, log_date, activity_type)
);

-- ================================================================
-- 6. ECO CHALLENGES â€” MASTER CHALLENGE CATALOGUE
-- ================================================================
CREATE TABLE eco_challenges (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title         VARCHAR(255) NOT NULL,
    description   TEXT NOT NULL,
    category      VARCHAR(50) NOT NULL,
    difficulty    challenge_difficulty DEFAULT 'medium',
    target_value  INT NOT NULL,               -- Threshold: 7 days, 50 miles saved, etc.
    metric_type   VARCHAR(50) NOT NULL,       -- 'days', 'miles', 'meals', 'kwh'
    co2e_reward   NUMERIC(6, 2),              -- Estimated kg CO2e reduction on completion
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
-- 8. NOTIFICATIONS â€” SCHEDULED NUDGE & ALERT LEDGER
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
-- 9. ORGANIZATIONS â€” B2B WORKSPACE ACCOUNTS
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
-- TRIGGER 1: Calculate CO2e on log insert/update
--   Priority: user region â†’ GLOBAL fallback â†’ NULL with WARNING
-- ================================================================
CREATE OR REPLACE FUNCTION calculate_log_co2e()
RETURNS TRIGGER AS $$
DECLARE
    v_factor_id    INT;
    v_factor       NUMERIC(8, 4);
    v_user_region  VARCHAR(10);
BEGIN
    -- Resolve the logging user's region preference
    SELECT region_code INTO v_user_region FROM users WHERE id = NEW.user_id;
    v_user_region := COALESCE(v_user_region, 'GLOBAL');

    -- Attempt region-specific factor lookup first
    SELECT id, co2e_per_unit
      INTO v_factor_id, v_factor
      FROM emission_factors
     WHERE activity_type = NEW.activity_type
       AND region_code   = v_user_region
       AND (valid_to IS NULL OR valid_to >= CURRENT_DATE);

    -- Fallback: try GLOBAL factor if region-specific not found
    IF v_factor IS NULL AND v_user_region <> 'GLOBAL' THEN
        SELECT id, co2e_per_unit
          INTO v_factor_id, v_factor
          FROM emission_factors
         WHERE activity_type = NEW.activity_type
           AND region_code   = 'GLOBAL'
           AND (valid_to IS NULL OR valid_to >= CURRENT_DATE);

        IF v_factor IS NOT NULL THEN
            NEW.is_estimated := TRUE;  -- Flag: GLOBAL fallback applied
        END IF;
    END IF;

    IF v_factor IS NOT NULL THEN
        NEW.total_co2e        := NEW.quantity * v_factor;
        NEW.emission_factor_id := v_factor_id;
    ELSE
        -- Unknown activity_type: surface warning; leave total_co2e NULL
        RAISE WARNING
            'No emission factor for activity_type=% region=% â€” total_co2e left NULL',
            NEW.activity_type, v_user_region;
        NEW.total_co2e        := NULL;
        NEW.is_estimated      := TRUE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calculate_co2e
BEFORE INSERT OR UPDATE ON daily_logs
FOR EACH ROW EXECUTE FUNCTION calculate_log_co2e();

-- ================================================================
-- TRIGGER 2: Auto-retire previous baseline when a new one is inserted
-- ================================================================
CREATE OR REPLACE FUNCTION deactivate_old_baseline()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE baselines
       SET is_current = FALSE
     WHERE user_id   = NEW.user_id
       AND id       <> NEW.id
       AND is_current = TRUE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_deactivate_old_baseline
AFTER INSERT ON baselines
FOR EACH ROW EXECUTE FUNCTION deactivate_old_baseline();
```

---

## 6. Google Cloud Integration Architecture

### 6.1 High-Level Service Map

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                        CLIENT LAYER                             â”‚
â”‚   Next.js App (Cloud Run)                                       â”‚
â”‚   â”œâ”€â”€ Firebase Auth SDK     â†’ Authentication                    â”‚
â”‚   â”œâ”€â”€ Firebase FCM SDK      â†’ Push notification subscription    â”‚
â”‚   â”œâ”€â”€ Material Web (M3)     â†’ UI component system               â”‚
â”‚   â””â”€â”€ Google Maps JS SDK    â†’ Geocoding / Routes / Air Quality  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚ HTTPS / REST / gRPC
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                        API LAYER                                â”‚
â”‚   FastAPI / Express Backend (Cloud Run)                         â”‚
â”‚   â”œâ”€â”€ Firebase Admin SDK    â†’ Token verification                â”‚
â”‚   â”œâ”€â”€ Gemini API Client     â†’ AI coaching + NL log parsing      â”‚
â”‚   â”œâ”€â”€ Maps Server SDK       â†’ Geocoding, Routes (server-side)   â”‚
â”‚   â”œâ”€â”€ FCM Admin SDK         â†’ Server-triggered push dispatch    â”‚
â”‚   â””â”€â”€ Secret Manager Client â†’ Runtime secret injection          â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                      DATA & ASYNC LAYER                         â”‚
â”‚   â”œâ”€â”€ Cloud SQL (PostgreSQL) â†’ Primary relational store         â”‚
â”‚   â”œâ”€â”€ Cloud Storage          â†’ Avatars, exports, org logos      â”‚
â”‚   â”œâ”€â”€ Cloud Tasks            â†’ GDPR erasure, digest queuing     â”‚
â”‚   â”œâ”€â”€ Cloud Scheduler        â†’ Cron: streaks, digest, expiry    â”‚
â”‚   â””â”€â”€ BigQuery (Datastream)  â†’ Analytics export for Looker      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

### 6.2 Service Integration Details

#### Firebase Authentication
- **Providers enabled:** Email/Password, Google, Apple
- **Token flow:** Client obtains Firebase ID token â†’ sent as `Authorization: Bearer <token>` on every API request â†’ backend verifies via `firebase-admin` SDK
- **Schema bridge:** On first login, backend upserts a `users` row using decoded `uid` as `provider_user_id` and sets `auth_provider` accordingly
- **Session strategy:** Short-lived ID tokens (1 hour) auto-refreshed by the Firebase SDK; no custom session cookie needed at MVP

#### Firebase Cloud Messaging (FCM)
- **Web push flow:** User grants notification permission â†’ FCM SDK registers device token â†’ token stored in `notifications` table `metadata` field â†’ backend dispatches via FCM Admin SDK targeting stored token
- **Service worker:** `firebase-messaging-sw.js` at web root handles background push receipt and notification display
- **Notification routing:** Cloud Scheduler triggers Cloud Run endpoint â†’ endpoint queries `notifications` table for `scheduled_at <= NOW() AND sent_at IS NULL` â†’ batch-dispatches via FCM â†’ updates `sent_at`

#### Gemini API
- **Weekly digest (`gemini-2.0-flash`):** Cloud Scheduler fires Sunday 06:00 UTC â†’ Cloud Tasks fan-out per user â†’ each task calls Gemini with a prompt containing the user's weekly `daily_logs` summary â†’ response written to `notifications` table as `type='weekly_digest'` + sent via FCM/email
- **Conversational log entry (`gemini-2.0-flash` structured output):** User submits free-text â†’ backend sends to Gemini with JSON schema of `{activity_type, quantity, category}` â†’ response auto-inserts into `daily_logs`
- **Model routing:** Flash for all latency-sensitive paths; Pro reserved for complex multi-turn coaching sessions (Phase 2)

#### Google Maps Platform
- **Geocoding API (server-side):** Called once on user signup to resolve IP/entered location â†’ writes `region_code` to `users` table
- **Routes API:** Called when user selects "log commute" â€” origin + destination â†’ distance in miles â†’ pre-fills `quantity` in the log form
- **Air Quality API:** Fetched client-side on the Transportation dashboard â†’ displayed alongside the user's daily transport emission total for contextual framing
- **Solar API (Phase 2):** Called on the Energy pillar when user enters their home address â†’ returns `maxArrayAreaMeters2` and `yearlyEnergyDcKwh` â†’ converted to potential annual COâ‚‚e savings for the recommendation engine

#### Cloud SQL
- **Edition:** PostgreSQL 15, Enterprise edition (for read replicas at Phase 2 scale)
- **Access pattern:** Cloud Run backend connects via Cloud SQL Auth Proxy sidecar â€” no public IP required
- **Connection pooling:** `pgBouncer` sidecar or `asyncpg` connection pool (FastAPI) / `pg-pool` (Node.js)
- **Backup policy:** Automated daily backups, 7-day retention; point-in-time recovery enabled

#### Cloud Storage
- **Buckets:** `avatars-{project-id}` (public read), `exports-{project-id}` (private, signed URLs)
- **GDPR export flow:** User requests export â†’ Cloud Tasks job queries all user data â†’ writes JSON to `exports-{project-id}/{user_id}/{timestamp}.json` â†’ signed URL (72-hour TTL) emailed to user

---

### 6.3 Environment Variable Manifest

All secrets injected at Cloud Run runtime via Secret Manager. Never committed to source control.

```env
# Firebase
FIREBASE_PROJECT_ID=
FIREBASE_CLIENT_EMAIL=
FIREBASE_PRIVATE_KEY=
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
NEXT_PUBLIC_FIREBASE_VAPID_KEY=        # FCM web push VAPID key

# Google Cloud / APIs
GOOGLE_MAPS_API_KEY=                   # Server-side only (Routes, Geocoding, Air Quality)
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=       # Client-side Maps JS SDK
GEMINI_API_KEY=
GOOGLE_CLOUD_PROJECT=
GCS_BUCKET_AVATARS=
GCS_BUCKET_EXPORTS=

# Database
DATABASE_URL=                          # postgresql://user:pass@/dbname?host=/cloudsql/...

# Emission API (external)
CLIMATIQ_API_KEY=
