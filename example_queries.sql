-- GarminTurso Example SQL Queries
-- Use these with the MCP server or directly with SQLite

-- ============================================
-- DAILY HEALTH SUMMARIES
-- ============================================

-- Last 7 days overview
SELECT
    date,
    total_steps,
    calories_total,
    active_seconds / 60 as active_minutes,
    resting_heart_rate,
    sleep_score,
    body_battery_highest,
    avg_stress_level
FROM daily_stats
ORDER BY date DESC
LIMIT 7;

-- Weekly averages comparison
SELECT
    strftime('%Y-%W', date) as week,
    AVG(total_steps) as avg_steps,
    AVG(calories_total) as avg_calories,
    AVG(resting_heart_rate) as avg_rhr,
    AVG(sleep_score) as avg_sleep_score,
    AVG(avg_stress_level) as avg_stress
FROM daily_stats
GROUP BY week
ORDER BY week DESC
LIMIT 8;

-- Best performance days
SELECT
    date,
    total_steps,
    active_seconds / 60 as active_minutes,
    body_battery_highest,
    sleep_score
FROM daily_stats
WHERE total_steps > (SELECT AVG(total_steps) * 1.2 FROM daily_stats)
ORDER BY total_steps DESC
LIMIT 10;

-- ============================================
-- ACTIVITY ANALYSIS
-- ============================================

-- Activity type distribution
SELECT
    activity_type,
    COUNT(*) as count,
    SUM(duration_seconds) / 3600.0 as total_hours,
    AVG(distance_meters / 1000.0) as avg_distance_km,
    AVG(calories) as avg_calories,
    AVG(avg_heart_rate) as avg_hr
FROM activities
GROUP BY activity_type
ORDER BY count DESC;

-- Personal records (longest/fastest activities)
SELECT
    activity_name,
    activity_type,
    DATE(start_time_local) as date,
    distance_meters / 1000.0 as distance_km,
    duration_seconds / 60.0 as duration_minutes,
    CASE
        WHEN distance_meters > 0
        THEN (duration_seconds / 60.0) / (distance_meters / 1000.0)
        ELSE NULL
    END as pace_min_per_km,
    calories
FROM activities
WHERE distance_meters = (
    SELECT MAX(distance_meters)
    FROM activities a2
    WHERE a2.activity_type = activities.activity_type
)
ORDER BY distance_km DESC;

-- Weekly activity volume
SELECT
    strftime('%Y-%W', start_time_local) as week,
    COUNT(*) as activities,
    SUM(duration_seconds) / 3600.0 as total_hours,
    SUM(distance_meters) / 1000.0 as total_km,
    SUM(calories) as total_calories
FROM activities
GROUP BY week
ORDER BY week DESC
LIMIT 12;

-- Morning vs Evening workouts
SELECT
    CASE
        WHEN CAST(strftime('%H', start_time_local) AS INTEGER) < 12 THEN 'Morning'
        WHEN CAST(strftime('%H', start_time_local) AS INTEGER) < 17 THEN 'Afternoon'
        ELSE 'Evening'
    END as time_of_day,
    COUNT(*) as count,
    AVG(duration_seconds / 60.0) as avg_duration_min,
    AVG(calories) as avg_calories
FROM activities
GROUP BY time_of_day;

-- ============================================
-- SLEEP PATTERNS
-- ============================================

-- Sleep quality trends
SELECT
    calendar_date,
    (deep_sleep_seconds + light_sleep_seconds + rem_sleep_seconds) / 3600.0 as total_sleep_hours,
    deep_sleep_seconds / 3600.0 as deep_hours,
    rem_sleep_seconds / 3600.0 as rem_hours,
    overall_sleep_score,
    sleep_quality_score,
    avg_respiration_value,
    avg_spo2_value
FROM sleep_data
ORDER BY calendar_date DESC
LIMIT 30;

-- Sleep consistency analysis
SELECT
    strftime('%w', calendar_date) as day_of_week,
    CASE strftime('%w', calendar_date)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END as day_name,
    AVG((deep_sleep_seconds + light_sleep_seconds + rem_sleep_seconds) / 3600.0) as avg_sleep_hours,
    AVG(overall_sleep_score) as avg_score,
    COUNT(*) as nights
FROM sleep_data
GROUP BY day_of_week
ORDER BY day_of_week;

-- Poor sleep nights (need attention)
SELECT
    calendar_date,
    (deep_sleep_seconds + light_sleep_seconds + rem_sleep_seconds) / 3600.0 as total_hours,
    overall_sleep_score,
    awake_seconds / 60.0 as awake_minutes,
    restless_moments_count
FROM sleep_data
WHERE overall_sleep_score < 60
    OR (deep_sleep_seconds + light_sleep_seconds + rem_sleep_seconds) < 6 * 3600
ORDER BY calendar_date DESC;

-- ============================================
-- HEART RATE & STRESS
-- ============================================

-- Daily heart rate ranges
SELECT
    DATE(timestamp) as date,
    MIN(heart_rate) as min_hr,
    AVG(heart_rate) as avg_hr,
    MAX(heart_rate) as max_hr,
    COUNT(*) as measurements
FROM heart_rate_data
GROUP BY DATE(timestamp)
ORDER BY date DESC
LIMIT 7;

-- Stress patterns by hour of day
SELECT
    strftime('%H', timestamp) as hour,
    AVG(stress_level) as avg_stress,
    MIN(stress_level) as min_stress,
    MAX(stress_level) as max_stress,
    COUNT(*) as measurements
FROM stress_data
GROUP BY hour
ORDER BY hour;

-- High stress periods
SELECT
    DATE(timestamp) as date,
    strftime('%H', timestamp) as hour,
    AVG(stress_level) as avg_stress,
    COUNT(*) as measurements
FROM stress_data
WHERE stress_level > 75
GROUP BY date, hour
ORDER BY date DESC, avg_stress DESC
LIMIT 20;

-- ============================================
-- BODY COMPOSITION TRENDS
-- ============================================

-- Weight and body composition over time
SELECT
    DATE(measurement_date) as date,
    weight_kg,
    bmi,
    body_fat_percentage,
    muscle_mass_kg,
    metabolic_age
FROM body_composition
ORDER BY measurement_date DESC
LIMIT 30;

-- Monthly body composition averages
SELECT
    strftime('%Y-%m', measurement_date) as month,
    AVG(weight_kg) as avg_weight,
    AVG(bmi) as avg_bmi,
    AVG(body_fat_percentage) as avg_body_fat,
    AVG(muscle_mass_kg) as avg_muscle,
    COUNT(*) as measurements
FROM body_composition
GROUP BY month
ORDER BY month DESC;

-- ============================================
-- CORRELATIONS & INSIGHTS
-- ============================================

-- Sleep vs Next Day Performance
SELECT
    s.calendar_date as sleep_date,
    s.overall_sleep_score,
    (s.deep_sleep_seconds + s.light_sleep_seconds + s.rem_sleep_seconds) / 3600.0 as sleep_hours,
    d.total_steps as next_day_steps,
    d.active_seconds / 60 as next_day_active_minutes,
    d.body_battery_highest as next_day_battery
FROM sleep_data s
JOIN daily_stats d ON DATE(d.date, '-1 day') = s.calendar_date
WHERE s.overall_sleep_score IS NOT NULL
ORDER BY s.calendar_date DESC;

-- Activity Impact on Sleep
SELECT
    DATE(a.start_time_local) as activity_date,
    a.activity_type,
    a.duration_seconds / 60.0 as activity_minutes,
    a.calories,
    s.overall_sleep_score as same_night_sleep_score,
    (s.deep_sleep_seconds + s.light_sleep_seconds + s.rem_sleep_seconds) / 3600.0 as sleep_hours
FROM activities a
JOIN sleep_data s ON s.calendar_date = DATE(a.start_time_local)
WHERE a.duration_seconds > 1800  -- Activities longer than 30 minutes
ORDER BY activity_date DESC;

-- Weekly health score (custom metric)
SELECT
    strftime('%Y-%W', date) as week,
    AVG(total_steps) / 10000.0 * 25 as steps_score,  -- 25% weight
    AVG(CASE WHEN sleep_score IS NOT NULL THEN sleep_score ELSE 50 END) / 100.0 * 25 as sleep_score,  -- 25% weight
    (150 - AVG(CASE WHEN avg_stress_level IS NOT NULL THEN avg_stress_level ELSE 50 END)) / 100.0 * 25 as stress_score,  -- 25% weight
    AVG(CASE WHEN body_battery_highest IS NOT NULL THEN body_battery_highest ELSE 50 END) / 100.0 * 25 as battery_score,  -- 25% weight
    (
        AVG(total_steps) / 10000.0 * 25 +
        AVG(CASE WHEN sleep_score IS NOT NULL THEN sleep_score ELSE 50 END) / 100.0 * 25 +
        (150 - AVG(CASE WHEN avg_stress_level IS NOT NULL THEN avg_stress_level ELSE 50 END)) / 100.0 * 25 +
        AVG(CASE WHEN body_battery_highest IS NOT NULL THEN body_battery_highest ELSE 50 END) / 100.0 * 25
    ) as total_health_score
FROM daily_stats
GROUP BY week
ORDER BY week DESC
LIMIT 12;

-- ============================================
-- DATA QUALITY CHECKS
-- ============================================

-- Data completeness by day
SELECT
    date,
    CASE WHEN total_steps IS NOT NULL THEN '✓' ELSE '✗' END as steps,
    CASE WHEN resting_heart_rate IS NOT NULL THEN '✓' ELSE '✗' END as rhr,
    CASE WHEN sleep_score IS NOT NULL THEN '✓' ELSE '✗' END as sleep,
    CASE WHEN avg_stress_level IS NOT NULL THEN '✓' ELSE '✗' END as stress,
    CASE WHEN body_battery_highest IS NOT NULL THEN '✓' ELSE '✗' END as battery
FROM daily_stats
ORDER BY date DESC
LIMIT 14;

-- Collection statistics
SELECT
    collection_type,
    status,
    start_time,
    end_time,
    records_collected,
    ROUND((julianday(end_time) - julianday(start_time)) * 24 * 60, 2) as duration_minutes
FROM collection_log
ORDER BY start_time DESC
LIMIT 10;