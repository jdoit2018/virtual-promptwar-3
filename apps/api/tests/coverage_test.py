"""
apps/api/tests/coverage_test.py
Additional test cases to maximize code coverage by hitting error paths and fallback logic.
"""

import asyncio
import os
import sys
from datetime import date, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import delete

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import AsyncSessionLocal
from main import app
from models.db_models import User, Baseline, UserGoal, EcoChallenge, UserChallenge, DailyLog

auth_headers = {"Authorization": "Bearer mock-token"}


async def run_coverage_tests():
    print("=" * 60)
    print("  COVERAGE TEST SUITE")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(delete(User).where(User.provider_user_id == 'mock-user-uid'))
            await session.execute(delete(DailyLog))
            await session.execute(delete(UserGoal))
            await session.execute(delete(UserChallenge))
            await session.execute(delete(Baseline))
            
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Auth Sync
        resp = await client.post("/api/auth/sync", headers=auth_headers)
        assert resp.status_code == 200
        
        # 1. Baseline Service Fallbacks
        # Pass weird or unrecognized strings to trigger the default fallback branches in baseline_service
        quiz_data_fallback = {
            "quiz_responses": {
                "property_type": "mansion",       # Unrecognized -> fallback
                "heating_type": "fusion_reactor", # Unrecognized -> fallback
                "household_size": 1, 
                "transport_mode": "teleportation",# Unrecognized -> fallback
                "weekly_mileage": "lightspeed",   # Unrecognized -> fallback
                "flights_profile": "frequent",    
                "diet_type": "carnivore",         # Unrecognized -> fallback
                "fashion_frequency": "always",    # Unrecognized -> fallback
                "electronics_frequency": "many"   # Unrecognized -> fallback
            }
        }
        resp = await client.post("/api/baselines", json=quiz_data_fallback, headers=auth_headers)
        assert resp.status_code == 200
        
        # 2. Get active goals when none exist (empty list)
        resp = await client.get("/api/goals/active", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["goal"] is None
        
        # 3. Create Goal logic
        goal_data = {"target_year": 2030, "target_co2e": 5.0}
        resp = await client.post("/api/goals", json=goal_data, headers=auth_headers)
        assert resp.status_code == 200
        
        # Duplicate goal (should deactivate the old one)
        resp = await client.post("/api/goals", json=goal_data, headers=auth_headers)
        assert resp.status_code == 200
        
        # 4. GET logs with skip/limit pagination
        resp = await client.get("/api/logs?skip=0&limit=5", headers=auth_headers)
        assert resp.status_code == 200
        
        # 5. Invalid Log fetching
        resp = await client.get("/api/logs/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert resp.status_code == 404
        
        # 6. Bad Log Creation
        bad_log = {
            "log_date": "2026-06-20",
            "category": "transportation",
            "activity_type": "gas_car_mile",
            "quantity": -10.0,
            "metadata": {}
        }
        resp = await client.post("/api/logs", json=bad_log, headers=auth_headers)
        assert resp.status_code == 200
        
        # 7. Challenge Error Paths
        resp = await client.post("/api/challenges/00000000-0000-0000-0000-000000000000/start", headers=auth_headers)
        assert resp.status_code == 404
        
        # Find a valid challenge ID to test double-enrollment and failure
        resp = await client.get("/api/challenges", headers=auth_headers)
        challenges = resp.json()
        if challenges:
            c_id = challenges[0]["id"]
            # Start
            await client.post(f"/api/challenges/{c_id}/start", headers=auth_headers)
            # Start again (should be 400)
            resp = await client.post(f"/api/challenges/{c_id}/start", headers=auth_headers)
            assert resp.status_code == 400
            
            # Fail challenge
            resp = await client.patch(f"/api/challenges/{c_id}/progress", json={"progress": -1}, headers=auth_headers)
            assert resp.status_code == 200
            
        # 8. Notifications GET error? Actually just empty list
        resp = await client.get("/api/notifications", headers=auth_headers)
        assert resp.status_code == 200
        
        # 10. GET Weekly Summary with end_date out of bounds or missing logs
        resp = await client.get("/api/logs/summary/weekly?end_date=2020-01-01", headers=auth_headers)
        assert resp.status_code == 200
        
        print("[OK] Coverage tests executed successfully")
        
if __name__ == "__main__":
    asyncio.run(run_coverage_tests())
