# Carbon Footprint Awareness Platform
## Software Requirement Specification & Technical Blueprint

This document defines the complete product scope, functional/non-functional specifications, technical stack, onboarding quiz architecture, and database relational layout for the Carbon Footprint Awareness Platform.

---

## 1. Product Scope & Vision
The Carbon Footprint Awareness Platform is a data-driven web application designed to empower individuals to calculate, track, and systematically reduce their daily environmental footprints. Instead of relying on static one-time estimations, the platform focuses on behavioral science—utilizing atomic micro-habits, dynamic gamification, and contextually relatable insights to turn generic environmental awareness into measurable, sustained reductions in carbon emissions.

---

## 2. Core Functional Requirements

### User Accounts & Onboarding
* **Authentication:** Secure registration and multi-provider login using Email/Password alongside Google and Apple OAuth integrations.
* **Baseline Calculator:** A swift, 3-minute onboarding questionnaire designed to approximate historical averages (housing infrastructure, transit modes, dietary habits) to calculate a working initial annual $CO_2e$ baseline without creating high user drop-off or friction.

### Footprint Tracking (The Analytical Engine)
* **Daily Log UI:** A streamlined entry system allowing users to track specific daily activities across four key pillars:
    * *Transportation:* Travel mileage, vehicle propulsion types, public transit durations, commercial flights.
    * *Diet:* Red meat frequency, poultry/fish consumption, plant-based substitutions, food waste logging.
    * *Energy:* Household utility consumption (kWh), domestic heating sources, usage of renewable/solar energy.
    * *Consumption:* Fast-fashion purchases, major personal electronics, or substantial household goods.
* **Automated Estimation Pipeline:** Decoupled backend architecture that interfaces with carbon calculation engines (e.g., Climatiq, Carbon Interface, or local calculation triggers) to translate physical units into precise emission statistics.

### Actionable Insights & Gamification
* **Recommendation Engine:** Dynamic, localized eco-challenges surfaced algorithmically using high-impact nodes from a user's logged history (e.g., if commuting emissions dominate, recommend "Bike to Work" or "Carpool Matcher" goals).
* **Streaks & Retention Mechanics:** Progression metrics honoring consecutive low-carbon targets met or specific curated challenges completed.
* **Impact Equivalencies:** Transparent translations converting raw metric tons ($MT\space CO_2e$) or kilograms ($kg\space CO_2e$) into contextually visual metrics (e.g., *"Your reductions this week equal the carbon offset of planting 3 mature trees"*).

### Goal Setting & Forecasting
* **Personal Reduction Target:** Users declare an annual CO₂e reduction goal as either a percentage (e.g., *"Reduce by 20%"*) or an absolute metric-ton figure, anchored to their current active baseline.
* **Pace-to-Goal Projection:** A dynamic forecast curve comparing the user's logged emission trajectory against their declared target, surfacing early-warning signals when trending off-pace.
* **Recommended Action Plan:** Algorithmic gap analysis ranking the highest-leverage behavioral changes by impact-to-effort ratio required to close the remaining reduction gap.

### Notification & Nudge Engine
* **Daily Log Reminders:** User-configurable push and email notifications prompting activity entry at a preferred local time window.
* **Streak-at-Risk Alerts:** Proactive warnings dispatched when a user has not logged within their customary daily window, protecting earned streak metrics.
* **Weekly Carbon Digest:** Automated Sunday summary presenting the week's totals, per-category breakdown, streak status, and one personalized behavioural tip.
* **Achievement Notifications:** Real-time in-app and push alerts triggered on challenge completions, badge unlocks, or personal-best emission records.

### Social & Community Layer
* **Friend Graph:** Opt-in peer connections allowing private weekly footprint comparisons between mutually confirmed contacts.
* **Team Challenges:** Household or workplace groups form collective challenge units, pooling individual progress toward a shared CO₂e reduction goal.
* **Opt-in Public Leaderboards:** Regional and national rankings of anonymized or named users, filterable by category and rolling time window.
* **Challenge Share Cards:** Open Graph–formatted visual cards for completed challenges, enabling organic social distribution.

### Carbon Offset Marketplace *(Phase 2)*
* **Curated Project Catalogue:** Vetted listings of verified offset projects (Gold Standard / Verra VCS) categorised by type (forestry, renewable energy, clean cookstoves).
* **Residual Emission Coverage:** Users directed to offset purchases after exhausting behavioural reduction options; MT CO₂e amounts pre-populated from logged totals.
* **Offset Certificates:** Post-purchase retirement certificates stored in user profiles; retired volumes netted against the user's displayed annual footprint.

### Data Retention & GDPR Compliance
* **Right to Erasure:** Self-service account deletion soft-deletes the user record and schedules irreversible PII purge within 30 days (GDPR Article 17).
* **Data Portability:** Users may request a full JSON export of all logs, baselines, and challenge history, fulfilled within 72 hours.
* **Retention Windows:** Raw daily logs retained for 3 years; aggregated annual summaries retained indefinitely; deleted-user PII purged after a 30-day cooling period.
* **Consent Audit Log:** Timestamped record of user consent events for marketing communications and third-party data sharing.

### B2B Organisation Accounts *(Phase 2)*
* **Organisation Workspaces:** Corporate accounts aggregating employee-level footprint data for scope-3 emissions reporting.
* **Admin Dashboard:** Organisation administrators view anonymised department breakdowns, set company-wide reduction targets, and manage internal challenges.
* **Role-Based Access Control:** Hierarchical roles (`admin`, `member`) governing data visibility and challenge management within an organisation.

---

## 3. Recommended Technical Stack

| Architecture Layer | Recommended Technology | Technical Justification |
| :--- | :--- | :--- |
| **Frontend Layout** | React / Next.js + Tailwind CSS | Next.js optimizes initial page asset delivery and handles metadata SEO cleanly; Tailwind maintains atomic utility styling classes for multi-device performance. |
| **Backend Engine** | Python (FastAPI) or Node.js (Express) | FastAPI offers strict, fast data runtime validation using Pydantic schemas for data calculations; Node.js is optimized for intensive concurrent external API I/O operations. |
| **Relational Storage** | PostgreSQL | Proven support for transactional operations, ACID guarantees for historic logs, index optimization for temporal data, and flexible `JSONB` data fields. |
| **Visual Analytics** | Recharts / Chart.js | Canvas/SVG client-side rendering capabilities optimized for responsive, interactive temporal data tracking. |

---

## 4. Onboarding Quiz Architecture & Calculation Logic

To balance accuracy with engagement, the onboarding framework aggregates broad parameters to calculate a regional baseline estimate.

### Part 1: Housing & Energy
* **Q1. What type of residential property do you occupy?**
  * Detached Single-Family Home *(Base weight: $4.0\text{ MT}$)*
  * Townhouse / Semi-detached Property *(Base weight: $2.5\text{ MT}$)*
  * Apartment / High-rise Condo *(Base weight: $1.5\text{ MT}$)*
* **Q2. What is your primary domestic heating utility?**
  * Natural Gas / Heating Oil Fuel *(Multiplier: $1.2$)*
  * Grid Electricity / Heat Pump Core *(Multiplier: $0.8$)*
  * Clean Renewables / On-site Solar Array *(Multiplier: $0.2$)*
* **Q3. How many individuals share this household workspace?**
  * Dropdown options: `1`, `2`, `3`, `4+`
  * *Logic:* Divide total housing baseline calculations by this variable ($N_{\text{people}}$) to determine unique individual allocations.

### Part 2: Transportation Profile
* **Q4. What represents your primary mode of daily transportation?**
  * Internal Combustion (Gas/Diesel) Vehicle *(Routes to Q5)*
  * Hybrid / Battery Electric Vehicle (EV) *(Routes to Q5)*
  * Public Transit Systems (Bus/Commuter Rail) *(Skips to Q6; assigns flat $+0.5\text{ MT}$)*
  * Pedestrian / Bicycle / Fixed Remote Work *(Skips to Q6; assigns flat $+0.0\text{ MT}$)*
* **Q5. Approximate your average weekly driving mileage:**
  * Low (<50 miles) *(Gas: $+0.8\text{ MT}$ / EV: $+0.3\text{ MT}$)*
  * Medium (50 – 150 miles) *(Gas: $+2.2\text{ MT}$ / EV: $+0.8\text{ MT}$)*
  * High (150+ miles) *(Gas: $+4.5\text{ MT}$ / EV: $+1.5\text{ MT}$)*
* **Q6. How many round-trip commercial flights do you average annually?**
  * None *( $+0.0\text{ MT}$)*
  * 1 – 2 short-haul domestic flights *( $+0.6\text{ MT}$)*
  * 3 – 5 flights or long-haul international travel *( $+2.5\text{ MT}$)*
  * Frequent flyer profile (6+ flights per year) *( $+6.0\text{ MT}$)*

### Part 3: Dietary Fingerprint
* **Q7. Which structural profile matches your daily nutrition choices?**
  * High Meat Consumption (Regular beef, lamb, pork) *( $+3.0\text{ MT}$)*
  * Standard Omnivore (Balanced meat, dairy, vegetables) *( $+2.0\text{ MT}$)*
  * Poultry / Pescatarian (No mammalian red meat products) *( $+1.4\text{ MT}$)*
  * Vegetarian (Meat-free, includes dairy/egg components) *( $+1.1\text{ MT}$)*
  * Vegan (Strict plant-exclusive consumption) *( $+0.7\text{ MT}$)*

### Part 4: Consumption Profile
* **Q8. How frequently do you purchase new clothing or fashion items?**
  * Rarely, or exclusively second-hand *(Base weight: $+0.1\text{ MT}$)*
  * Occasionally — a few items per season *(Base weight: $+0.4\text{ MT}$)*
  * Frequently — regular fast-fashion purchases *(Base weight: $+0.9\text{ MT}$)*
* **Q9. How many major personal electronics did you purchase in the last 12 months?** *(e.g., smartphone, laptop, tablet)*
  * None *( $+0.0\text{ MT}$)*
  * One *( $+0.3\text{ MT}$)*
  * Two or more *( $+0.6\text{ MT}$)*

### Mathematical Onboarding Baseline Algorithm
$$E_{\text{total}} = \left( \frac{H_{\text{base}} \times H_{\text{heat}}}{N_{\text{people}}} \right) + T_{\text{drive}} + T_{\text{flight}} + D_{\text{diet}} + C_{\text{consumption}}$$

Where $C_{\text{consumption}} = C_{\text{fashion}} + C_{\text{electronics}}$.

---

## 5. PostgreSQL Relational Database Schema

```sql
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
-- 1. USERS — IDENTITY, PROFILE & SECURITY
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
-- 2. EMISSION FACTORS — REGION-AWARE CALCULATION CONSTANTS
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
-- 3. BASELINES — USER FOOTPRINT BASELINE HISTORY
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
-- 4. USER GOALS — PERSONAL ANNUAL REDUCTION TARGETS
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
-- 5. DAILY LOGS — HISTORICAL ACTIVITY ENTRIES
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
-- 6. ECO CHALLENGES — MASTER CHALLENGE CATALOGUE
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
-- 8. NOTIFICATIONS — SCHEDULED NUDGE & ALERT LEDGER
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
-- 9. ORGANIZATIONS — B2B WORKSPACE ACCOUNTS
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
--   Priority: user region → GLOBAL fallback → NULL with WARNING
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
            'No emission factor for activity_type=% region=% — total_co2e left NULL',
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
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│   Next.js App (Cloud Run)                                       │
│   ├── Firebase Auth SDK     → Authentication                    │
│   ├── Firebase FCM SDK      → Push notification subscription    │
│   ├── Material Web (M3)     → UI component system               │
│   └── Google Maps JS SDK    → Geocoding / Routes / Air Quality  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / REST / gRPC
┌──────────────────────────▼──────────────────────────────────────┐
│                        API LAYER                                │
│   FastAPI / Express Backend (Cloud Run)                         │
│   ├── Firebase Admin SDK    → Token verification                │
│   ├── Gemini API Client     → AI coaching + NL log parsing      │
│   ├── Maps Server SDK       → Geocoding, Routes (server-side)   │
│   ├── FCM Admin SDK         → Server-triggered push dispatch    │
│   └── Secret Manager Client → Runtime secret injection          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      DATA & ASYNC LAYER                         │
│   ├── Cloud SQL (PostgreSQL) → Primary relational store         │
│   ├── Cloud Storage          → Avatars, exports, org logos      │
│   ├── Cloud Tasks            → GDPR erasure, digest queuing     │
│   ├── Cloud Scheduler        → Cron: streaks, digest, expiry    │
│   └── BigQuery (Datastream)  → Analytics export for Looker      │
└─────────────────────────────────────────────────────────────────┘
```

---

### 6.2 Service Integration Details

#### Firebase Authentication
- **Providers enabled:** Email/Password, Google, Apple
- **Token flow:** Client obtains Firebase ID token → sent as `Authorization: Bearer <token>` on every API request → backend verifies via `firebase-admin` SDK
- **Schema bridge:** On first login, backend upserts a `users` row using decoded `uid` as `provider_user_id` and sets `auth_provider` accordingly
- **Session strategy:** Short-lived ID tokens (1 hour) auto-refreshed by the Firebase SDK; no custom session cookie needed at MVP

#### Firebase Cloud Messaging (FCM)
- **Web push flow:** User grants notification permission → FCM SDK registers device token → token stored in `notifications` table `metadata` field → backend dispatches via FCM Admin SDK targeting stored token
- **Service worker:** `firebase-messaging-sw.js` at web root handles background push receipt and notification display
- **Notification routing:** Cloud Scheduler triggers Cloud Run endpoint → endpoint queries `notifications` table for `scheduled_at <= NOW() AND sent_at IS NULL` → batch-dispatches via FCM → updates `sent_at`

#### Gemini API
- **Weekly digest (`gemini-2.0-flash`):** Cloud Scheduler fires Sunday 06:00 UTC → Cloud Tasks fan-out per user → each task calls Gemini with a prompt containing the user's weekly `daily_logs` summary → response written to `notifications` table as `type='weekly_digest'` + sent via FCM/email
- **Conversational log entry (`gemini-2.0-flash` structured output):** User submits free-text → backend sends to Gemini with JSON schema of `{activity_type, quantity, category}` → response auto-inserts into `daily_logs`
- **Model routing:** Flash for all latency-sensitive paths; Pro reserved for complex multi-turn coaching sessions (Phase 2)

#### Google Maps Platform
- **Geocoding API (server-side):** Called once on user signup to resolve IP/entered location → writes `region_code` to `users` table
- **Routes API:** Called when user selects "log commute" — origin + destination → distance in miles → pre-fills `quantity` in the log form
- **Air Quality API:** Fetched client-side on the Transportation dashboard → displayed alongside the user's daily transport emission total for contextual framing
- **Solar API (Phase 2):** Called on the Energy pillar when user enters their home address → returns `maxArrayAreaMeters2` and `yearlyEnergyDcKwh` → converted to potential annual CO₂e savings for the recommendation engine

#### Cloud SQL
- **Edition:** PostgreSQL 15, Enterprise edition (for read replicas at Phase 2 scale)
- **Access pattern:** Cloud Run backend connects via Cloud SQL Auth Proxy sidecar — no public IP required
- **Connection pooling:** `pgBouncer` sidecar or `asyncpg` connection pool (FastAPI) / `pg-pool` (Node.js)
- **Backup policy:** Automated daily backups, 7-day retention; point-in-time recovery enabled

#### Cloud Storage
- **Buckets:** `avatars-{project-id}` (public read), `exports-{project-id}` (private, signed URLs)
- **GDPR export flow:** User requests export → Cloud Tasks job queries all user data → writes JSON to `exports-{project-id}/{user_id}/{timestamp}.json` → signed URL (72-hour TTL) emailed to user

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
```

---

### 6.4 Phase-Wise Rollout

| Phase | Services Activated | Milestone |
|:---|:---|:---|
| **Phase 1 — MVP** | Firebase Auth, FCM, Cloud Run, Cloud SQL, Gemini Flash, Maps Geocoding, Google Fonts + Material Web | Working auth, daily logging, AI digest, push reminders |
| **Phase 2 — Growth** | Vertex AI, Maps Routes API, Air Quality API, BigQuery + Looker Studio, GA4, Cloud Tasks, Cloud Scheduler | Recommendation engine, org dashboards, full async nudge pipeline |
| **Phase 3 — Scale** | Gemini Pro (conversational), Solar API, reCAPTCHA Enterprise, Cloud Monitoring alerts, read replicas | NL log entry, solar recommendations, abuse prevention, SLA monitoring |
