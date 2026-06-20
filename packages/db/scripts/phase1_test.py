"""
packages/db/scripts/phase1_test.py
Phase 1 gate test: apply schema, seed, and rigorously verify all 3 triggers.
Run from project root: python packages/db/scripts/phase1_test.py
"""

import sys
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://carbon_user:carbon_pass@localhost:5432/carbon_db"
)

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "..", "schema.sql")
SEED_FILE   = os.path.join(os.path.dirname(__file__), "..", "seed", "emission_factors.sql")

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

results = []


def connect():
    return psycopg2.connect(DATABASE_URL)


def log(symbol, msg):
    print(f"{symbol} {msg}")
    results.append((symbol, msg))


# ── Step 0: Drop + Recreate (idempotent reset before each run) ────────────────

def step_reset_db():
    print("\n=== Step 0: Resetting DB (drop all objects for clean run) ===")
    with connect() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            # Drop everything in reverse dependency order
            cur.execute("""
                DROP TABLE IF EXISTS
                    organization_members, organizations, notifications,
                    user_challenges, eco_challenges, daily_logs, user_goals,
                    baselines, emission_factors, users
                CASCADE;
            """)
            cur.execute("""
                DROP TYPE IF EXISTS
                    auth_provider_type, challenge_status, challenge_difficulty,
                    notification_type, notification_channel, org_role
                CASCADE;
            """)
            cur.execute("DROP FUNCTION IF EXISTS calculate_log_co2e() CASCADE;")
            cur.execute("DROP FUNCTION IF EXISTS deactivate_old_baseline() CASCADE;")
    log(INFO, "DB objects dropped -- ready for clean schema apply")


# ── Step 1.1: Apply Schema ─────────────────────────────────────────────────────

def step_apply_schema():
    print("\n=== Step 1.1: Apply Schema ===")
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with connect() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            try:
                cur.execute(schema_sql)
                log(PASS, "Schema applied successfully")
            except psycopg2.errors.DuplicateObject as e:
                log(INFO, f"Schema objects already exist (idempotent): {e.pgerror.strip()}")
                conn.rollback()
            except Exception as e:
                log(FAIL, f"Schema application failed: {e}")
                sys.exit(1)


# ── Step 1.2: Apply Seed ───────────────────────────────────────────────────────

def step_apply_seed():
    print("\n=== Step 1.2: Apply Seed Data ===")
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        seed_sql = f.read()

    with connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(seed_sql)
                conn.commit()
                cur.execute("SELECT COUNT(*) FROM emission_factors;")
                count = cur.fetchone()[0]
                log(PASS, f"Seed applied — {count} emission factors in database")
            except Exception as e:
                conn.rollback()
                log(FAIL, f"Seed failed: {e}")
                sys.exit(1)


# ── Step 1.3: Trigger Tests ────────────────────────────────────────────────────

def setup_test_fixtures(cur):
    """Create a throwaway test user for trigger tests."""
    cur.execute("""
        INSERT INTO users (email, password_hash, auth_provider, first_name, region_code)
        VALUES ('test_trigger@carbon.test', 'hashed_pw', 'email', 'Trigger', 'GLOBAL')
        ON CONFLICT (email) DO UPDATE SET updated_at = NOW()
        RETURNING id, region_code;
    """)
    row = cur.fetchone()
    return row[0]  # user_id


def cleanup_test_fixtures(cur, user_id):
    """Remove all test data for the test user."""
    cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))


def test_trigger1_known_factor(cur, user_id):
    """
    TEST 1: Insert a log with a known activity_type.
    Expect: total_co2e = quantity * co2e_per_unit, is_estimated = FALSE
    """
    # gas_car_mile = 0.4040 kg/mile, quantity = 10 miles -> 4.040 kg CO2e
    cur.execute("""
        INSERT INTO daily_logs (user_id, log_date, category, activity_type, quantity)
        VALUES (%s, CURRENT_DATE, 'transportation', 'gas_car_mile', 10)
        ON CONFLICT (user_id, log_date, activity_type) DO UPDATE SET quantity = 10
        RETURNING total_co2e, is_estimated, emission_factor_id;
    """, (user_id,))
    row = cur.fetchone()
    total_co2e, is_estimated, factor_id = row

    expected = round(10 * 0.4040, 3)
    if total_co2e is not None and abs(float(total_co2e) - expected) < 0.01 and not is_estimated and factor_id:
        log(PASS, f"Trigger 1a (known factor): total_co2e={total_co2e} kg (expected ~{expected}), is_estimated=False, factor_id={factor_id}")
    else:
        log(FAIL, f"Trigger 1a: got total_co2e={total_co2e}, is_estimated={is_estimated}, factor_id={factor_id} | expected ~{expected}")


def test_trigger1_unknown_factor(cur, user_id):
    """
    TEST 2: Insert a log with an UNKNOWN activity_type.
    Expect: total_co2e = NULL, is_estimated = TRUE
    """
    import warnings
    cur.execute("""
        INSERT INTO daily_logs (user_id, log_date, category, activity_type, quantity)
        VALUES (%s, CURRENT_DATE - 1, 'transportation', 'unicorn_powered_spaceship', 5)
        RETURNING total_co2e, is_estimated;
    """, (user_id,))
    row = cur.fetchone()
    total_co2e, is_estimated = row

    if total_co2e is None and is_estimated:
        log(PASS, "Trigger 1b (unknown factor): total_co2e=NULL, is_estimated=True -- correct behaviour")
    else:
        log(FAIL, f"Trigger 1b: got total_co2e={total_co2e}, is_estimated={is_estimated} | expected NULL + True")


def test_trigger1_update_recalculates(cur, user_id):
    """
    TEST 3: UPDATE quantity on existing log -> trigger recalculates total_co2e.
    """
    cur.execute("""
        UPDATE daily_logs
           SET quantity = 20
         WHERE user_id = %s AND activity_type = 'gas_car_mile'
        RETURNING total_co2e, is_estimated;
    """, (user_id,))
    row = cur.fetchone()
    if not row:
        log(FAIL, "Trigger 1c: no row found to update")
        return
    total_co2e, is_estimated = row
    expected = round(20 * 0.4040, 3)
    if total_co2e is not None and abs(float(total_co2e) - expected) < 0.01:
        log(PASS, f"Trigger 1c (UPDATE recalculate): total_co2e={total_co2e} after qty=20 (expected ~{expected})")
    else:
        log(FAIL, f"Trigger 1c: got total_co2e={total_co2e} | expected ~{expected}")


def test_trigger1_diet_factor(cur, user_id):
    """
    TEST 4: Insert a diet log entry.
    beef_serving = 6.6100, qty = 1 -> 6.610 kg CO2e
    """
    cur.execute("""
        INSERT INTO daily_logs (user_id, log_date, category, activity_type, quantity)
        VALUES (%s, CURRENT_DATE - 2, 'diet', 'beef_serving', 1)
        RETURNING total_co2e, is_estimated;
    """, (user_id,))
    row = cur.fetchone()
    total_co2e, is_estimated = row
    expected = round(1 * 6.6100, 3)
    if total_co2e is not None and abs(float(total_co2e) - expected) < 0.01:
        log(PASS, f"Trigger 1d (diet factor): total_co2e={total_co2e} for beef_serving x1 (expected ~{expected})")
    else:
        log(FAIL, f"Trigger 1d: got total_co2e={total_co2e} | expected ~{expected}")


def test_trigger2_baseline_deactivation(cur, user_id):
    """
    TEST 5: Insert two baselines for the same user.
    The BEFORE INSERT trigger must deactivate the first before the second is committed.
    After both inserts:
      - baseline1.is_current must be FALSE
      - baseline2.is_current must be TRUE
    """
    cur.execute("""
        INSERT INTO baselines (user_id, total_co2e, housing_co2e, transport_co2e, diet_co2e, consumption_co2e)
        VALUES (%s, 12.50, 4.00, 3.50, 4.00, 1.00)
        RETURNING id;
    """, (user_id,))
    b1_id = cur.fetchone()[0]

    # This second INSERT must succeed (trigger deactivates b1 BEFORE unique index fires)
    cur.execute("""
        INSERT INTO baselines (user_id, total_co2e, housing_co2e, transport_co2e, diet_co2e, consumption_co2e)
        VALUES (%s, 10.20, 3.50, 2.80, 3.50, 0.40)
        RETURNING id;
    """, (user_id,))
    b2_id = cur.fetchone()[0]

    cur.execute("SELECT id, is_current FROM baselines WHERE user_id = %s ORDER BY created_at;", (user_id,))
    rows = cur.fetchall()

    b1_current = next((r[1] for r in rows if r[0] == b1_id), None)
    b2_current = next((r[1] for r in rows if r[0] == b2_id), None)

    if b1_current is False and b2_current is True:
        log(PASS, f"Trigger 2 (baseline deactivation): baseline1.is_current=False, baseline2.is_current=True")
    else:
        log(FAIL, f"Trigger 2: b1_current={b1_current}, b2_current={b2_current} | expected False, True")


def test_trigger2_partial_unique_index(cur, user_id):
    """
    TEST 6: The partial unique index should block a direct UPDATE
    that would create two is_current=TRUE baselines for the same user.
    This tests the index independently from the INSERT trigger.
    """
    # First ensure the user has exactly one is_current=TRUE baseline
    cur.execute("SELECT id FROM baselines WHERE user_id = %s AND is_current = TRUE;", (user_id,))
    active_rows = cur.fetchall()
    if len(active_rows) != 1:
        log(FAIL, f"Trigger 2b precondition: expected 1 active baseline, got {len(active_rows)}")
        return

    # Get a deactivated baseline (is_current=FALSE)
    cur.execute("SELECT id FROM baselines WHERE user_id = %s AND is_current = FALSE LIMIT 1;", (user_id,))
    inactive_row = cur.fetchone()
    if not inactive_row:
        log(FAIL, "Trigger 2b: no deactivated baseline found to test UPDATE block")
        return
    inactive_id = inactive_row[0]

    # Attempt to UPDATE the inactive baseline back to is_current=TRUE
    # The partial unique index must block this
    try:
        cur.execute("UPDATE baselines SET is_current = TRUE WHERE id = %s;", (inactive_id,))
        # If we reach here, the unique index did NOT fire -- this is a FAIL
        log(FAIL, "Trigger 2b: partial unique index did NOT block a second is_current=TRUE baseline via UPDATE")
    except psycopg2.errors.UniqueViolation:
        log(PASS, "Trigger 2b (partial unique index): correctly blocked duplicate is_current=TRUE baseline via UPDATE")
    except Exception as e:
        log(FAIL, f"Trigger 2b: unexpected error: {e}")


def step_run_trigger_tests():
    print("\n=== Step 1.3: Trigger & Constraint Tests ===")
    with connect() as conn:
        with conn.cursor() as cur:
            user_id = setup_test_fixtures(cur)
            conn.commit()
            log(INFO, f"Test user created: id={user_id}")

            # Run all tests in their own savepoints so one failure doesn't block others
            for test_fn in [
                test_trigger1_known_factor,
                test_trigger1_unknown_factor,
                test_trigger1_update_recalculates,
                test_trigger1_diet_factor,
                test_trigger2_baseline_deactivation,
                test_trigger2_partial_unique_index,
            ]:
                sp = f"sp_{test_fn.__name__}"
                cur.execute(f"SAVEPOINT {sp};")
                try:
                    test_fn(cur, user_id)
                    conn.commit()
                except Exception as e:
                    log(FAIL, f"{test_fn.__name__} raised exception: {e}")
                    cur.execute(f"ROLLBACK TO SAVEPOINT {sp};")

            # Cleanup
            cleanup_test_fixtures(cur, user_id)
            conn.commit()
            log(INFO, "Test fixtures cleaned up")


# ── Step 1.4: Schema Object Verification ──────────────────────────────────────

def step_verify_schema_objects():
    print("\n=== Step 1.4: Schema Object Count Verification ===")
    with connect() as conn:
        with conn.cursor() as cur:

            # Tables
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """)
            table_count = cur.fetchone()[0]
            expected_tables = 10  # 9 domain tables + organization_members
            if table_count >= expected_tables:
                log(PASS, f"Tables: {table_count} found (expected >= {expected_tables})")
            else:
                log(FAIL, f"Tables: {table_count} found (expected >= {expected_tables})")

            # Triggers
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.triggers
                WHERE trigger_schema = 'public';
            """)
            trigger_count = cur.fetchone()[0]
            if trigger_count >= 2:
                log(PASS, f"Triggers: {trigger_count} found (expected >= 2)")
            else:
                log(FAIL, f"Triggers: {trigger_count} found (expected >= 2)")

            # Indexes
            cur.execute("""
                SELECT COUNT(*) FROM pg_indexes
                WHERE schemaname = 'public' AND indexname LIKE 'idx_%';
            """)
            index_count = cur.fetchone()[0]
            if index_count >= 7:
                log(PASS, f"Indexes: {index_count} found (expected >= 7)")
            else:
                log(FAIL, f"Indexes: {index_count} found (expected >= 7)")

            # Emission factors
            cur.execute("SELECT COUNT(*) FROM emission_factors;")
            factor_count = cur.fetchone()[0]
            if factor_count >= 30:
                log(PASS, f"Emission factors: {factor_count} seeded (expected >= 30)")
            else:
                log(FAIL, f"Emission factors: {factor_count} seeded (expected >= 30)")

            # Enums
            cur.execute("""
                SELECT COUNT(*) FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typtype = 'e' AND n.nspname = 'public';
            """)
            enum_count = cur.fetchone()[0]
            if enum_count >= 6:
                log(PASS, f"Enum types: {enum_count} found (expected >= 6)")
            else:
                log(FAIL, f"Enum types: {enum_count} found (expected >= 6)")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  PHASE 1 -- DATABASE FOUNDATION TEST SUITE")
    print("=" * 60)

    step_reset_db()
    step_apply_schema()
    step_apply_seed()
    step_run_trigger_tests()
    step_verify_schema_objects()

    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r[0] == PASS)
    failed = sum(1 for r in results if r[0] == FAIL)
    total  = passed + failed
    print(f"  RESULTS: {passed}/{total} tests passed  |  {failed} failed")
    print("=" * 60)

    if failed > 0:
        print("\nFailed tests:")
        for sym, msg in results:
            if sym == FAIL:
                print(f"  {sym} {msg}")
        sys.exit(1)
    else:
        print("\nAll Phase 1 gate tests PASSED.")
        sys.exit(0)
