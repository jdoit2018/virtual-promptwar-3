/**
 * packages/db/scripts/migrate.js
 * Applies schema.sql to the target database.
 * Usage: node scripts/migrate.js
 */
const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

async function migrate() {
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  await client.connect();
  console.log('✅ Connected to database');

  const schema = fs.readFileSync(path.join(__dirname, '../schema.sql'), 'utf8');
  await client.query(schema);
  console.log('✅ Schema applied successfully');

  await client.end();
}

migrate().catch((err) => {
  console.error('❌ Migration failed:', err.message);
  process.exit(1);
});
