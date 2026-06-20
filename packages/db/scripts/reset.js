/**
 * packages/db/scripts/reset.js
 * Resets the database by dropping all tables, types, and triggers.
 * Usage: node scripts/reset.js
 */
const { Client } = require('pg');

async function reset() {
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  await client.connect();
  console.log('✅ Connected to database');

  await client.query(`
    DROP TABLE IF EXISTS
      organization_members, organizations, notifications,
      user_challenges, eco_challenges, daily_logs, user_goals,
      baselines, emission_factors, users
    CASCADE;
  `);

  await client.query(`
    DROP TYPE IF EXISTS
      auth_provider_type, challenge_status, challenge_difficulty,
      notification_type, notification_channel, org_role
    CASCADE;
  `);

  await client.query('DROP FUNCTION IF EXISTS calculate_log_co2e() CASCADE;');
  await client.query('DROP FUNCTION IF EXISTS deactivate_old_baseline() CASCADE;');

  console.log('✅ Database reset successfully');
  await client.end();
}

reset().catch((err) => {
  console.error('❌ Reset failed:', err.message);
  process.exit(1);
});
