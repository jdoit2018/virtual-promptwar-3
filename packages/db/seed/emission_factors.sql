-- ================================================================
-- EMISSION FACTORS SEED DATA — GLOBAL BASELINE CONSTANTS
-- Sources: DEFRA 2024 GHG Conversion Factors, EPA GHG Equivalencies
-- region_code = 'GLOBAL' for universal fallbacks
-- All values in kg CO2e per unit
-- ================================================================

INSERT INTO emission_factors (category, activity_type, unit, co2e_per_unit, region_code, source, valid_from) VALUES

-- ── TRANSPORTATION ────────────────────────────────────────────────
('transportation', 'gas_car_mile',       'mile',    0.4040, 'GLOBAL', 'EPA 2024',   '2024-01-01'),
('transportation', 'diesel_car_mile',    'mile',    0.4320, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('transportation', 'ev_car_mile',        'mile',    0.0960, 'GLOBAL', 'EPA 2024',   '2024-01-01'),
('transportation', 'hybrid_car_mile',    'mile',    0.2120, 'GLOBAL', 'EPA 2024',   '2024-01-01'),
('transportation', 'bus_mile',           'mile',    0.0890, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('transportation', 'rail_mile',          'mile',    0.0350, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('transportation', 'flight_short_km',    'km',      0.2550, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('transportation', 'flight_long_km',     'km',      0.1950, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('transportation', 'motorcycle_mile',    'mile',    0.2140, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('transportation', 'taxi_mile',          'mile',    0.2900, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),

-- ── DIET ──────────────────────────────────────────────────────────
('diet', 'beef_serving',                'serving', 6.6100, 'GLOBAL', 'Poore & Nemecek 2018', '2024-01-01'),
('diet', 'lamb_serving',                'serving', 6.0000, 'GLOBAL', 'Poore & Nemecek 2018', '2024-01-01'),
('diet', 'pork_serving',                'serving', 2.1500, 'GLOBAL', 'Poore & Nemecek 2018', '2024-01-01'),
('diet', 'chicken_serving',             'serving', 1.2900, 'GLOBAL', 'Poore & Nemecek 2018', '2024-01-01'),
('diet', 'fish_serving',                'serving', 1.3400, 'GLOBAL', 'Poore & Nemecek 2018', '2024-01-01'),
('diet', 'dairy_serving',               'serving', 0.9400, 'GLOBAL', 'Poore & Nemecek 2018', '2024-01-01'),
('diet', 'eggs_serving',                'serving', 0.4500, 'GLOBAL', 'Poore & Nemecek 2018', '2024-01-01'),
('diet', 'vegetables_serving',          'serving', 0.0700, 'GLOBAL', 'Poore & Nemecek 2018', '2024-01-01'),
('diet', 'legumes_serving',             'serving', 0.0900, 'GLOBAL', 'Poore & Nemecek 2018', '2024-01-01'),
('diet', 'food_waste_kg',               'kg',      2.5000, 'GLOBAL', 'WRAP 2023',  '2024-01-01'),

-- ── ENERGY ────────────────────────────────────────────────────────
('energy', 'kwh_grid_coal',             'kwh',     0.8200, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('energy', 'kwh_grid_average',          'kwh',     0.2330, 'GLOBAL', 'EPA 2024',   '2024-01-01'),
('energy', 'kwh_grid_renewables',       'kwh',     0.0150, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('energy', 'natural_gas_kwh',           'kwh',     0.2030, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('energy', 'heating_oil_litre',         'litre',   2.5200, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('energy', 'lpg_litre',                 'litre',   1.5550, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('energy', 'solar_kwh',                 'kwh',     0.0480, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),

-- ── CONSUMPTION ───────────────────────────────────────────────────
('consumption', 'clothing_item',        'item',    8.1000, 'GLOBAL', 'WRAP 2023',  '2024-01-01'),
('consumption', 'smartphone_unit',      'unit',   70.0000, 'GLOBAL', 'Apple LCA 2023', '2024-01-01'),
('consumption', 'laptop_unit',          'unit',  400.0000, 'GLOBAL', 'Dell LCA 2023',  '2024-01-01'),
('consumption', 'tv_unit',              'unit',  450.0000, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('consumption', 'washing_machine_unit', 'unit',  210.0000, 'GLOBAL', 'DEFRA 2024', '2024-01-01'),
('consumption', 'online_order_parcel',  'parcel',  0.4500, 'GLOBAL', 'DEFRA 2024', '2024-01-01')

ON CONFLICT (activity_type, region_code) DO UPDATE
  SET co2e_per_unit = EXCLUDED.co2e_per_unit,
      source        = EXCLUDED.source,
      updated_at    = CURRENT_TIMESTAMP;
