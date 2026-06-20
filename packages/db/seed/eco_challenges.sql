-- Seeds the eco_challenges table with sample challenges
-- Safe to run multiple times

INSERT INTO eco_challenges (title, description, category, difficulty, target_value, metric_type, co2e_reward)
VALUES 
  (
    'Bike to Work Commute', 
    'Commute to work or school using a bicycle instead of driving a fossil-fueled car.', 
    'transportation', 
    'medium', 
    50, 
    'miles', 
    20.20
  ),
  (
    'Plant-Powered Week', 
    'Eat vegetarian or vegan meals for 7 consecutive days to lower your diet footprint.', 
    'diet', 
    'medium', 
    7, 
    'days', 
    15.50
  ),
  (
    'Vampire Power Sweep', 
    'Unplug standby appliances (chargers, game consoles, TVs) when not in use for a week.', 
    'energy', 
    'easy', 
    7, 
    'days', 
    4.50
  ),
  (
    'Thrift Shop First', 
    'Only buy second-hand clothing for your next three fashion additions.', 
    'consumption', 
    'easy', 
    3, 
    'meals', 
    12.00
  ),
  (
    'Cooler Winter, Cooler Planet', 
    'Reduce your home heating thermostat by 2 degrees Celsius for a month.', 
    'energy', 
    'hard', 
    30, 
    'days', 
    25.00
  ),
  (
    'No Beef This Month', 
    'Avoid red meat (beef, pork, lamb) for 30 consecutive days.', 
    'diet', 
    'hard', 
    30, 
    'days', 
    45.00
  )
ON CONFLICT DO NOTHING;
