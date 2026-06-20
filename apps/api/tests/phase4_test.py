"""
apps/api/tests/phase4_test.py
Phase 4 integration tests for streaks, Gemini service, and cron tasks.
Run from apps/api/ directory: python tests/phase4_test.py
"""

import asyncio
import os
import sys
from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy import delete

# Ensure the parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from core.database import AsyncSessionLocal
from main import app
from models.db_models import User

auth_headers = {"Authorization": "Bearer mock-token"}
cron_headers = {"Authorization": f"Bearer {settings.CRON_SECRET}"}


async def run_all_tests():
    print("=" * 60)
    print("  PHASE 4 -- ADMINISTRATIVE & STREAKS INTEGRATION TEST SUITE")
    print("=" * 60)

    # Clean up mock user from previous runs to ensure test isolation
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(delete(User).where(User.provider_user_id == 'mock-user-uid'))
    print("[INFO] Cleaned up mock user from database")

    async with AsyncClient(app=app, base_url="http://test") as client:

        # 1. First sync user.
        resp = await client.post("/api/auth/sync", headers=auth_headers)
        assert resp.status_code == 200, f"Sync failed: {resp.text}"
        print("[OK] Test 01: Auth user synced successfully")

        # 2. Reset user's streak to 0 for initial test boundary.
        # We can just fetch user me and check initial state.
        resp = await client.get("/api/users/me", headers=auth_headers)
        assert resp.status_code == 200
        initial_streak = resp.json().get("current_streak", 0)
        print(f"[INFO] Initial streak is {initial_streak}")

        # 3. Log an activity for yesterday.
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()
        log_yesterday = {
            "log_date": yesterday_str,
            "category": "transportation",
            "activity_type": "gas_car_mile",
            "quantity": 5.0,
            "metadata": {}
        }
        resp = await client.post("/api/logs", json=log_yesterday, headers=auth_headers)
        assert resp.status_code == 200, f"Logging for yesterday failed: {resp.text}"
        print(f"[OK] Test 02: Logged 5 miles for yesterday ({yesterday_str})")

        # 4. Log an activity for today.
        today_str = date.today().isoformat()
        log_today = {
            "log_date": today_str,
            "category": "diet",
            "activity_type": "meal_vegetarian",
            "quantity": 1.0,
            "metadata": {}
        }
        resp = await client.post("/api/logs", json=log_today, headers=auth_headers)
        assert resp.status_code == 200, f"Logging for today failed: {resp.text}"
        print(f"[OK] Test 03: Logged vegetarian meal for today ({today_str})")

        # 5. Verify the streak has incremented to at least 2.
        resp = await client.get("/api/users/me", headers=auth_headers)
        assert resp.status_code == 200
        profile = resp.json()
        assert profile["current_streak"] >= 2, f"Expected streak >= 2, got {profile['current_streak']}"
        print(f"[OK] Test 04: Streak incremented successfully to {profile['current_streak']}")

        # 6. Test cron endpoints reject without proper CRON_SECRET.
        resp = await client.post("/api/internal/streak-check", headers={"Authorization": "Bearer bad-secret"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("[OK] Test 05: /api/internal/streak-check rejected bad secret")

        # 7. Test cron endpoint streak-check runs successfully.
        resp = await client.post("/api/internal/streak-check", headers=cron_headers)
        assert resp.status_code == 200, f"Cron execution failed: {resp.text}"
        res_data = resp.json()
        assert res_data["status"] == "success"
        print(f"[OK] Test 06: /api/internal/streak-check ran successfully: {res_data}")

        # 8. Test cron endpoint digest runs successfully.
        resp = await client.post("/api/internal/digest", headers=cron_headers)
        assert resp.status_code == 200, f"Weekly digest cron execution failed: {resp.text}"
        res_data = resp.json()
        assert res_data["status"] == "success"
        print(f"[OK] Test 07: /api/internal/digest generated digest: {res_data}")

        # 9. Verify that a weekly digest notification was written to database.
        resp = await client.get("/api/notifications", headers=auth_headers)
        assert resp.status_code == 200
        notifications = resp.json()
        # Find any weekly_digest notification
        digest_notifs = [n for n in notifications if n["type"] == "weekly_digest"]
        assert len(digest_notifs) >= 1, "No weekly digest notifications found in database"
        print(f"[OK] Test 08: Verified notification written: '{digest_notifs[0]['body']}'")

    print("\n" + "=" * 60)
    print("  ALL PHASE 4 TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
