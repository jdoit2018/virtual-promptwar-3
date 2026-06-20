/**
 * packages/db/scripts/seed.js
 * Seeds the emission_factors table with GLOBAL baseline constants.
 * Safe to run multiple times — uses ON CONFLICT DO UPDATE (upsert).
 * Usage: node scripts/seed.js
 */
const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

async function seed() {
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  await client.connect();
  console.log('✅ Connected to database');

  const seedFile = path.join(__dirname, '../seed/emission_factors.sql');
  const sql = fs.readFileSync(seedFile, 'utf8');
  await client.query(sql);
  console.log('✅ emission_factors seeded successfully');

  const challengesFile = path.join(__dirname, '../seed/eco_challenges.sql');
  const challengesSql = fs.readFileSync(challengesFile, 'utf8');
  await client.query(challengesSql);
  console.log('✅ eco_challenges seeded successfully');

  const { rows: factorRows } = await client.query('SELECT COUNT(*) FROM emission_factors');
  console.log(`   → ${factorRows[0].count} factors in database`);

  const { rows: challengeRows } = await client.query('SELECT COUNT(*) FROM eco_challenges');
  console.log(`   → ${challengeRows[0].count} eco-challenges in database`);

  await client.end();
}

seed().catch((err) => {
  console.error('❌ Seed failed:', err.message);
  process.exit(1);
});
