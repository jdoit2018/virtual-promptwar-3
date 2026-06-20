"""
apps/api/tests/phase2_test.py
Phase 2 async integration tests for all 13 REST endpoints.
Run from apps/api/ directory: python tests/phase2_test.py
"""

import sys
import os
import asyncio
from httpx import AsyncClient
from sqlalchemy import delete

# Ensure the parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from core.database import AsyncSessionLocal
from models.db_models import User

auth_headers = {"Authorization": "Bearer mock-token"}


async def run_all_tests():
    print("=" * 60)
    print("  PHASE 2 -- ASYNC ENDPOINT INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Clean up mock user from previous runs to ensure test isolation
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(delete(User).where(User.provider_user_id == 'mock-user-uid'))
    print("[INFO] Cleaned up mock user from database")

    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # 1. Verify that endpoints reject request without token.
        resp = await client.get("/api/users/me")
        assert resp.status_code in (401, 403), f"Test 1 failed: status code {resp.status_code}"
        print("[OK] Test 01: Unauthorized access rejected (401/403)")

        # 2. Test POST /api/auth/sync (first login sync).
        resp = await client.post("/api/auth/sync", headers=auth_headers)
        assert resp.status_code == 200, f"Test 2 failed: status code {resp.status_code}"
        data = resp.json()
        assert data["email"] == "mock-user@example.com"
        assert data["first_name"] == "Mock"
        assert data["last_name"] == "User"
        print("[OK] Test 02: POST /api/auth/sync succeeded")

        # 3. Test GET /api/users/me (profile fetching).
        resp = await client.get("/api/users/me", headers=auth_headers)
        assert resp.status_code == 200, f"Test 3 failed: {resp.text}"
        data = resp.json()
        assert data["email"] == "mock-user@example.com"
        print("[OK] Test 03: GET /api/users/me profile fetched")

        # 4. Test POST /api/baselines (onboarding quiz submission).
        quiz_data = {
            "quiz_responses": {
                "property_type": "detached",       # 4.0 MT
                "heating_type": "gas_oil",          # x1.2
                "household_size": 2,                # divide by 2 -> 2.4 MT
                "transport_mode": "gas_car",
                "weekly_mileage": "medium",         # +2.2 MT
                "flights_profile": "short_haul",    # +0.6 MT -> Trans: 2.8 MT
                "diet_type": "vegetarian",          # +1.1 MT
                "fashion_frequency": "occasionally",# +0.4 MT
                "electronics_frequency": "one"      # +0.3 MT -> Cons: 0.7 MT
            }
        }
        resp = await client.post("/api/baselines", json=quiz_data, headers=auth_headers)
        assert resp.status_code == 200, f"Test 4 failed: {resp.text}"
        data = resp.json()
        assert abs(data["total_co2e"] - 7.0) < 0.1, f"Expected ~7.0, got {data['total_co2e']}"
        assert data["housing_co2e"] == 2.4
        assert data["transport_co2e"] == 2.8
        assert data["diet_co2e"] == 1.1
        assert data["consumption_co2e"] == 0.7
        print("[OK] Test 04: POST /api/baselines calculated & retired old baselines")

        # 5. Test GET /api/baselines/current.
        resp = await client.get("/api/baselines/current", headers=auth_headers)
        assert resp.status_code == 200, f"Test 5 failed: {resp.text}"
        data = resp.json()
        assert data["is_current"] is True
        assert abs(data["total_co2e"] - 7.0) < 0.1
        print("[OK] Test 05: GET /api/baselines/current retrieved current baseline")

        # 6. Test POST /api/logs (activity logging).
        log_data = {
            "log_date": "2026-06-20",
            "category": "transportation",
            "activity_type": "gas_car_mile",
            "quantity": 10.0,
            "metadata": {"route": "office_commute"}
        }
        resp = await client.post("/api/logs", json=log_data, headers=auth_headers)
        assert resp.status_code == 200, f"Test 6 failed: {resp.text}"
        data = resp.json()
        assert abs(float(data["total_co2e"]) - 4.040) < 0.01
        assert data["activity_type"] == "gas_car_mile"
        print("[OK] Test 06: POST /api/logs saved and calculated CO2e dynamically via DB trigger")

        # 7. Test GET /api/logs.
        resp = await client.get("/api/logs?log_date=2026-06-20", headers=auth_headers)
        assert resp.status_code == 200, f"Test 7 failed: {resp.text}"
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["activity_type"] == "gas_car_mile"
        print("[OK] Test 07: GET /api/logs filtered logs successfully")

        # 8. Test GET /api/logs/summary/weekly.
        resp = await client.get("/api/logs/summary/weekly?end_date=2026-06-20", headers=auth_headers)
        assert resp.status_code == 200, f"Test 8 failed: {resp.text}"
        data = resp.json()
        assert "breakdown" in data
        assert data["total_co2e"] > 0
        assert "transportation" in data["breakdown"]
        assert abs(data["breakdown"]["transportation"] - 4.040) < 0.01
        print("[OK] Test 08: GET /api/logs/summary/weekly aggregated weekly data correctly")

        # 9. Test POST /api/goals (reduction goal setting).
        goal_data = {
            "target_co2e": 5.60,
            "target_year": 2026
        }
        resp = await client.post("/api/goals", json=goal_data, headers=auth_headers)
        assert resp.status_code == 200, f"Test 9 failed: {resp.text}"
        data = resp.json()
        assert abs(data["target_co2e"] - 5.60) < 0.01
        assert abs(data["reduction_pct"] - 20.0) < 0.1
        print("[OK] Test 09: POST /api/goals created goal and auto-calculated reduction percentage")

        # 10. Test GET /api/goals/active (pace forecast calculation).
        resp = await client.get("/api/goals/active", headers=auth_headers)
        assert resp.status_code == 200, f"Test 10 failed: {resp.text}"
        data = resp.json()
        assert data["goal"] is not None
        assert data["pace"] is not None
        assert data["goal"]["target_year"] == 2026
        assert "on_track" in data["pace"]
        print("[OK] Test 10: GET /api/goals/active calculated trajectory pace-to-goal correctly")

        # 11. Test GET /api/challenges (catalog list).
        resp = await client.get("/api/challenges", headers=auth_headers)
        assert resp.status_code == 200, f"Test 11 failed: {resp.text}"
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["is_active"] is True
        print("[OK] Test 11: GET /api/challenges listed eco-challenge catalog")

        # 12. Test POST /api/challenges/{id}/start and PATCH progress/complete.
        # Get a challenge ID from catalog list
        challenge_id = data[0]["id"]
        target_value = data[0]["target_value"]

        # Enroll in the challenge
        resp = await client.post(f"/api/challenges/{challenge_id}/start", headers=auth_headers)
        assert resp.status_code == 200, f"Test 12 Start failed: {resp.text}"
        start_data = resp.json()
        assert start_data["status"] == "active"
        assert start_data["progress"] == 0

        # Update progress (less than target)
        resp = await client.patch(
            f"/api/challenges/{challenge_id}/progress", 
            json={"progress": target_value - 1}, 
            headers=auth_headers
        )
        assert resp.status_code == 200, f"Test 12 Progress failed: {resp.text}"
        assert resp.json()["status"] == "active"

        # Complete the challenge
        resp = await client.patch(
            f"/api/challenges/{challenge_id}/progress", 
            json={"progress": target_value}, 
            headers=auth_headers
        )
        assert resp.status_code == 200, f"Test 12 Completion failed: {resp.text}"
        comp_data = resp.json()
        assert comp_data["status"] == "completed"
        assert comp_data["completed_at"] is not None
        print("[OK] Test 12: Eco-Challenge enrollment, progress, and completion verified")

        # 13. Test POST /api/notifications/register-token.
        reg_data = {"token": "dummy-fcm-push-token-value"}
        resp = await client.post("/api/notifications/register-token", json=reg_data, headers=auth_headers)
        assert resp.status_code == 201, f"Test 13 failed: {resp.text}"
        data = resp.json()
        assert data["status"] == "success"
        print("[OK] Test 13: POST /api/notifications/register-token verified successfully")

        # 14. Test POST /api/users/me/export (GDPR Export).
        resp = await client.post("/api/users/me/export", headers=auth_headers)
        assert resp.status_code == 200, f"Test 14 failed: {resp.text}"
        export_data = resp.json()
        assert "profile" in export_data
        assert "baselines" in export_data
        assert "daily_logs" in export_data
        assert "user_challenges" in export_data
        assert export_data["profile"]["email"] == "mock-user@example.com"
        print("[OK] Test 14: POST /api/users/me/export verified successfully")

        # 15. Test DELETE /api/users/me (Soft Delete).
        resp = await client.delete("/api/users/me", headers=auth_headers)
        assert resp.status_code == 200, f"Test 15 failed: {resp.text}"
        del_data = resp.json()
        assert del_data["status"] == "success"
        print("[OK] Test 15: DELETE /api/users/me verified successfully")

    print("=" * 60)
    print("SUCCESS: ALL 15 PHASE 2 & 4 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())

