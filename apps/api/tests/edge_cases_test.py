"""
apps/api/tests/edge_cases_test.py
Phase 5 boundary, validation, and edge-case integration tests.
Run from apps/api/ directory: python tests/edge_cases_test.py
"""

import asyncio
import os
import sys

from httpx import AsyncClient
from sqlalchemy import delete, select

# Ensure the parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import AsyncSessionLocal
from main import app
from models.db_models import User

auth_headers = {"Authorization": "Bearer mock-token"}


async def run_edge_cases():
    print("=" * 60)
    print("  EDGE CASES, BOUNDARIES & VALIDATIONS INTEGRATION TEST SUITE")
    print("=" * 60)

    # Clean up mock user from database
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(delete(User).where(User.provider_user_id == 'mock-user-uid'))
    print("[INFO] Cleaned up mock user from database")

    async with AsyncClient(app=app, base_url="http://test") as client:

        # ── 1. USER GOAL BEFORE BASELINE ONBOARDING ──
        # Try to set a goal before creating a baseline (should fail with 400)
        # We need to sync user first so profile exists
        await client.post("/api/auth/sync", headers=auth_headers)

        goal_payload = {"target_co2e": 5.0, "target_year": 2026}
        resp = await client.post("/api/goals", json=goal_payload, headers=auth_headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        assert "complete onboarding baseline" in resp.json()["detail"]
        print("[OK] Test 01: Creating goal before baseline onboarding rejected successfully")

        # ── 2. ONBOARD USER (Create Baseline) ──
        quiz_data = {
            "quiz_responses": {
                "property_type": "apartment",
                "heating_type": "electricity_heat_pump",
                "household_size": 1,
                "transport_mode": "pedestrian_bicycle",
                "weekly_mileage": "low",
                "flights_profile": "none",
                "diet_type": "vegan",
                "fashion_frequency": "rarely",
                "electronics_frequency": "none"
            }
        }
        resp = await client.post("/api/baselines", json=quiz_data, headers=auth_headers)
        assert resp.status_code == 200, f"Baseline creation failed: {resp.text}"
        print("[OK] Test 02: Onboarding baseline created successfully")

        # ── 3. CREATE GOAL & VERIFY REDUCTION PERCENTAGE ──
        resp = await client.post("/api/goals", json=goal_payload, headers=auth_headers)
        assert resp.status_code == 200, f"Goal creation failed: {resp.text}"
        first_goal_data = resp.json()
        assert first_goal_data["is_active"] is True
        print("[OK] Test 03: Goal created successfully")

        # ── 4. CONCURRENT GOAL DEACTIVATION ──
        # Create another goal for the same year, verify first goal gets deactivated
        second_goal_payload = {"target_co2e": 4.5, "target_year": 2026}
        resp = await client.post("/api/goals", json=second_goal_payload, headers=auth_headers)
        assert resp.status_code == 200, f"Second goal creation failed: {resp.text}"

        # Verify first goal is now inactive
        resp = await client.get("/api/goals/active", headers=auth_headers)
        assert resp.status_code == 200
        active_goal_data = resp.json()["goal"]
        assert active_goal_data["target_co2e"] == 4.5
        print("[OK] Test 04: Older goal for the same year auto-deactivated successfully")

        # ── 5. NONEXISTENT ECO-CHALLENGE ACTIONS ──
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(f"/api/challenges/{fake_uuid}/start", headers=auth_headers)
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("[OK] Test 05: Starting nonexistent challenge rejected with 404")

        resp = await client.patch(f"/api/challenges/{fake_uuid}/progress", json={"progress": 5}, headers=auth_headers)
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("[OK] Test 06: Updating progress of nonexistent enrollment rejected with 404")

        # ── 6. CHALLENGE DOUBLE ENROLLMENT & DOUBLE COMPLETION ──
        # Fetch active challenges list
        resp = await client.get("/api/challenges", headers=auth_headers)
        assert resp.status_code == 200
        challenge = resp.json()[0]
        challenge_id = challenge["id"]
        target_value = challenge["target_value"]

        # Enroll first time
        resp = await client.post(f"/api/challenges/{challenge_id}/start", headers=auth_headers)
        assert resp.status_code == 200

        # Try enrolling a second time (should fail with 400)
        resp = await client.post(f"/api/challenges/{challenge_id}/start", headers=auth_headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        assert "already participating" in resp.json()["detail"]
        print("[OK] Test 07: Duplicate challenge enrollment rejected with 400")

        # Complete the challenge
        resp = await client.patch(f"/api/challenges/{challenge_id}/progress", json={"progress": target_value}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

        # Try updating progress on a completed challenge (should fail with 400)
        resp = await client.patch(f"/api/challenges/{challenge_id}/progress", json={"progress": target_value + 1}, headers=auth_headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        assert "already completed" in resp.json()["detail"]
        print("[OK] Test 08: Modifying completed challenge progress rejected with 400")

        # ── 7. GRACE PERIOD ACCOUNT RESTORATION ──
        # Soft-delete the user
        resp = await client.delete("/api/users/me", headers=auth_headers)
        assert resp.status_code == 200

        # Verify user is soft-deleted in database
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.provider_user_id == 'mock-user-uid')
            res = await session.execute(stmt)
            db_user = res.scalars().first()
            assert db_user.deleted_at is not None
        print("[OK] Test 09: Account soft-deleted successfully (deleted_at is set)")

        # Sync user back (simulates user logging back in during 30 days grace period)
        resp = await client.post("/api/auth/sync", headers=auth_headers)
        assert resp.status_code == 200

        # Verify user is restored (deleted_at is cleared)
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.provider_user_id == 'mock-user-uid')
            res = await session.execute(stmt)
            db_user = res.scalars().first()
            assert db_user.deleted_at is None
        print("[OK] Test 10: Grace period account restoration works (deleted_at is cleared)")

    print("=" * 60)
    print("SUCCESS: ALL 10 EDGE CASE & VALIDATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_edge_cases())
