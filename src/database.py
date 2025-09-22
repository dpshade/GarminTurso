"""Database schema and management for Garmin data storage in Turso DB."""

import libsql_experimental as libsql
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TursoDatabase:
    def __init__(self, db_path: str = "./data/garmin.db"):
        self.db_path = db_path
        self.conn: Optional[libsql.Connection] = None

    def connect(self) -> libsql.Connection:
        """Establish database connection."""
        self.conn = libsql.connect(self.db_path)
        logger.info(f"Connected to Turso DB at {self.db_path}")
        return self.conn

    def create_schema(self):
        """Create all necessary tables for Garmin data storage."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()

        # User profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                garmin_user_id TEXT UNIQUE,
                display_name TEXT,
                full_name TEXT,
                profile_image_url TEXT,
                locale TEXT,
                timezone TEXT,
                measurement_system TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Daily summary statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                user_id INTEGER,

                -- Activity metrics
                total_steps INTEGER,
                total_distance_meters REAL,
                active_seconds INTEGER,
                highly_active_seconds INTEGER,
                sedentary_seconds INTEGER,
                calories_total INTEGER,
                calories_active INTEGER,
                floors_climbed INTEGER,

                -- Heart rate metrics
                resting_heart_rate INTEGER,
                min_heart_rate INTEGER,
                max_heart_rate INTEGER,
                avg_stress_level INTEGER,
                max_stress_level INTEGER,

                -- Body battery and energy
                body_battery_charged INTEGER,
                body_battery_drained INTEGER,
                body_battery_highest INTEGER,
                body_battery_lowest INTEGER,

                -- Sleep metrics (summary)
                sleep_score INTEGER,
                total_sleep_seconds INTEGER,
                deep_sleep_seconds INTEGER,
                light_sleep_seconds INTEGER,
                rem_sleep_seconds INTEGER,
                awake_seconds INTEGER,

                -- Wellness
                hydration_ml INTEGER,
                respiration_avg REAL,
                spo2_avg REAL,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, user_id),
                FOREIGN KEY (user_id) REFERENCES user_profile(id)
            )
        """)

        # Activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,

                -- Basic info
                activity_name TEXT,
                activity_type TEXT,
                sport_type TEXT,
                start_time_local DATETIME,
                start_time_gmt DATETIME,
                duration_seconds INTEGER,

                -- Distance and movement
                distance_meters REAL,
                elevation_gain_meters REAL,
                elevation_loss_meters REAL,
                avg_speed_mps REAL,
                max_speed_mps REAL,

                -- Heart rate
                avg_heart_rate INTEGER,
                max_heart_rate INTEGER,

                -- Performance
                calories INTEGER,
                avg_power_watts INTEGER,
                max_power_watts INTEGER,
                training_effect_aerobic REAL,
                training_effect_anaerobic REAL,
                training_stress_score REAL,
                intensity_factor REAL,

                -- Location
                start_latitude REAL,
                start_longitude REAL,
                end_latitude REAL,
                end_longitude REAL,

                -- Additional data
                has_polyline BOOLEAN,
                has_splits BOOLEAN,
                manual_activity BOOLEAN,
                favorite BOOLEAN,
                pr_flag BOOLEAN,
                parent_id TEXT,
                device_id TEXT,

                raw_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profile(id)
            )
        """)

        # Heart rate intraday data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS heart_rate_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp DATETIME NOT NULL,
                heart_rate INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profile(id)
            )
        """)

        # Sleep detailed data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sleep_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sleep_id TEXT UNIQUE,
                user_id INTEGER,
                calendar_date DATE NOT NULL,

                -- Times
                sleep_start_timestamp_gmt DATETIME,
                sleep_end_timestamp_gmt DATETIME,
                sleep_start_timestamp_local DATETIME,
                sleep_end_timestamp_local DATETIME,

                -- Durations in seconds
                unmeasurable_seconds INTEGER,
                deep_sleep_seconds INTEGER,
                light_sleep_seconds INTEGER,
                rem_sleep_seconds INTEGER,
                awake_seconds INTEGER,

                -- Scores and quality
                overall_sleep_score INTEGER,
                sleep_quality_score INTEGER,
                sleep_recovery_score INTEGER,
                sleep_restfulness_score INTEGER,
                sleep_duration_score INTEGER,
                sleep_interruptions_score INTEGER,

                -- Physiological metrics
                avg_respiration_value REAL,
                avg_spo2_value REAL,
                lowest_spo2_value REAL,
                highest_spo2_value REAL,
                avg_hrv REAL,

                -- Movement
                time_to_fall_asleep_seconds INTEGER,
                restless_moments_count INTEGER,

                raw_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(calendar_date, user_id),
                FOREIGN KEY (user_id) REFERENCES user_profile(id)
            )
        """)

        # Body composition
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS body_composition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                measurement_date DATETIME NOT NULL,

                weight_kg REAL,
                bmi REAL,
                body_fat_percentage REAL,
                body_water_percentage REAL,
                bone_mass_kg REAL,
                muscle_mass_kg REAL,
                physique_rating INTEGER,
                visceral_fat_rating INTEGER,
                metabolic_age INTEGER,

                source_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profile(id)
            )
        """)

        # Stress data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stress_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp DATETIME NOT NULL,
                stress_level INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profile(id)
            )
        """)

        # Collection metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_type TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                status TEXT NOT NULL,
                records_collected INTEGER,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sync metadata for tracking last sync times
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_start ON activities(start_time_gmt)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_heart_rate_timestamp ON heart_rate_data(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep_data(calendar_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stress_timestamp ON stress_data(timestamp)")

        self.conn.commit()
        logger.info("Database schema created successfully")

    def insert_collection_log(self, record: dict):
        """Insert collection log record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO collection_log (collection_type, start_time, end_time, status, records_collected)
            VALUES (?, ?, ?, ?, ?)
        """, (
            record.get('collection_type', 'comprehensive'),
            record.get('start_time'),
            record.get('end_time'),
            record.get('status', 'success'),
            record.get('records_collected', 0)
        ))
        self.conn.commit()

    def get_sync_metadata(self, key: str) -> Optional[str]:
        """Get sync metadata value by key."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM sync_metadata WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result[0] if result else None

    def set_sync_metadata(self, key: str, value: str):
        """Set sync metadata value."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        self.conn.commit()

    def get_last_sync_time(self) -> Optional[datetime]:
        """Get the last successful sync timestamp."""
        sync_time_str = self.get_sync_metadata('last_sync_time')
        if sync_time_str:
            try:
                return datetime.fromisoformat(sync_time_str)
            except ValueError:
                logger.warning(f"Invalid sync time format in database: {sync_time_str}")
        return None

    def update_last_sync_time(self, sync_time: datetime):
        """Update the last successful sync timestamp."""
        self.set_sync_metadata('last_sync_time', sync_time.isoformat())

    def insert_user_profile(self, profile_data: dict, user_id: int = 1):
        """Insert or update user profile data."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_profile
            (id, garmin_user_id, display_name, full_name, locale, timezone, measurement_system, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            user_id,
            profile_data.get('garmin_user_id'),
            profile_data.get('display_name'),
            profile_data.get('full_name'),
            profile_data.get('locale'),
            profile_data.get('timezone'),
            profile_data.get('measurement_system')
        ))
        self.conn.commit()

    def insert_daily_stats(self, stats_data: dict, user_id: int = 1):
        """Insert daily statistics."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO daily_stats
            (date, user_id, total_steps, total_distance_meters, active_seconds, highly_active_seconds,
             sedentary_seconds, calories_total, calories_active, floors_climbed, resting_heart_rate,
             min_heart_rate, max_heart_rate, avg_stress_level, max_stress_level, body_battery_charged,
             body_battery_drained, body_battery_highest, body_battery_lowest, sleep_score,
             total_sleep_seconds, deep_sleep_seconds, light_sleep_seconds, rem_sleep_seconds,
             awake_seconds, hydration_ml, respiration_avg, spo2_avg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stats_data.get('date'),
            user_id,
            stats_data.get('total_steps'),
            stats_data.get('total_distance_meters'),
            stats_data.get('active_seconds'),
            stats_data.get('highly_active_seconds'),
            stats_data.get('sedentary_seconds'),
            stats_data.get('calories_total'),
            stats_data.get('calories_active'),
            stats_data.get('floors_climbed'),
            stats_data.get('resting_heart_rate'),
            stats_data.get('min_heart_rate'),
            stats_data.get('max_heart_rate'),
            stats_data.get('avg_stress_level'),
            stats_data.get('max_stress_level'),
            stats_data.get('body_battery_charged'),
            stats_data.get('body_battery_drained'),
            stats_data.get('body_battery_highest'),
            stats_data.get('body_battery_lowest'),
            stats_data.get('sleep_score'),
            stats_data.get('total_sleep_seconds'),
            stats_data.get('deep_sleep_seconds'),
            stats_data.get('light_sleep_seconds'),
            stats_data.get('rem_sleep_seconds'),
            stats_data.get('awake_seconds'),
            stats_data.get('hydration_ml'),
            stats_data.get('respiration_avg'),
            stats_data.get('spo2_avg')
        ))
        self.conn.commit()

    def insert_activity(self, activity_data: dict, user_id: int = 1):
        """Insert activity record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO activities
            (activity_id, user_id, activity_name, activity_type, sport_type, start_time_local,
             start_time_gmt, duration_seconds, distance_meters, elevation_gain_meters,
             elevation_loss_meters, avg_speed_mps, max_speed_mps, avg_heart_rate, max_heart_rate,
             calories, avg_power_watts, max_power_watts, training_effect_aerobic, training_effect_anaerobic,
             training_stress_score, intensity_factor, start_latitude, start_longitude, end_latitude,
             end_longitude, has_polyline, has_splits, manual_activity, favorite, pr_flag,
             parent_id, device_id, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_data.get('activityId'),
            user_id,
            activity_data.get('activityName'),
            activity_data.get('activityType', {}).get('typeKey'),
            activity_data.get('sportType', {}).get('sportTypeKey'),
            activity_data.get('startTimeLocal'),
            activity_data.get('startTimeGMT'),
            activity_data.get('duration'),
            activity_data.get('distance'),
            activity_data.get('elevationGain'),
            activity_data.get('elevationLoss'),
            activity_data.get('averageSpeed'),
            activity_data.get('maxSpeed'),
            activity_data.get('averageHR'),
            activity_data.get('maxHR'),
            activity_data.get('calories'),
            activity_data.get('avgPower'),
            activity_data.get('maxPower'),
            activity_data.get('aerobicTrainingEffect'),
            activity_data.get('anaerobicTrainingEffect'),
            activity_data.get('trainingStressScore'),
            activity_data.get('intensityFactor'),
            activity_data.get('startLatitude'),
            activity_data.get('startLongitude'),
            activity_data.get('endLatitude'),
            activity_data.get('endLongitude'),
            bool(activity_data.get('hasPolyline')),
            bool(activity_data.get('hasSplits')),
            bool(activity_data.get('manual')),
            bool(activity_data.get('favorite')),
            bool(activity_data.get('pr')),
            activity_data.get('parentId'),
            activity_data.get('deviceId'),
            str(activity_data) if activity_data else None
        ))
        self.conn.commit()

    def insert_sleep_data(self, sleep_data: dict, user_id: int = 1):
        """Insert sleep record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sleep_data
            (sleep_id, user_id, calendar_date, sleep_start_timestamp_gmt, sleep_end_timestamp_gmt,
             sleep_start_timestamp_local, sleep_end_timestamp_local, unmeasurable_seconds,
             deep_sleep_seconds, light_sleep_seconds, rem_sleep_seconds, awake_seconds,
             overall_sleep_score, sleep_quality_score, sleep_recovery_score, sleep_restfulness_score,
             sleep_duration_score, sleep_interruptions_score, avg_respiration_value, avg_spo2_value,
             lowest_spo2_value, highest_spo2_value, avg_hrv, time_to_fall_asleep_seconds,
             restless_moments_count, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sleep_data.get('sleepTimeSeconds'),  # Using sleep duration as ID
            user_id,
            sleep_data.get('calendarDate'),
            sleep_data.get('sleepStartTimestampGMT'),
            sleep_data.get('sleepEndTimestampGMT'),
            sleep_data.get('sleepStartTimestampLocal'),
            sleep_data.get('sleepEndTimestampLocal'),
            sleep_data.get('unmeasurableSleepSeconds'),
            sleep_data.get('deepSleepSeconds'),
            sleep_data.get('lightSleepSeconds'),
            sleep_data.get('remSleepSeconds'),
            sleep_data.get('awakeSleepSeconds'),
            sleep_data.get('overallSleepScore'),
            sleep_data.get('sleepQualityTypePK'),
            sleep_data.get('sleepRecoveryTypePK'),
            sleep_data.get('sleepRestlessnessTypePK'),
            sleep_data.get('sleepDurationTypePK'),
            sleep_data.get('sleepInterruptionsTypePK'),
            sleep_data.get('avgRespirationValue'),
            sleep_data.get('avgSpO2Value'),
            sleep_data.get('lowestSpO2Value'),
            sleep_data.get('highestSpO2Value'),
            sleep_data.get('avgSpO2HRVariability'),
            sleep_data.get('timeToFallAsleepSeconds'),
            sleep_data.get('restlessMomentsCount'),
            str(sleep_data) if sleep_data else None
        ))
        self.conn.commit()

    def insert_heart_rate_data(self, hr_records: list, user_id: int = 1):
        """Insert multiple heart rate records."""
        cursor = self.conn.cursor()
        for record in hr_records:
            cursor.execute("""
                INSERT OR REPLACE INTO heart_rate_data (user_id, timestamp, heart_rate)
                VALUES (?, ?, ?)
            """, (
                user_id,
                record.get('datetime') or record.get('timestamp'),
                record.get('heart_rate')
            ))
        self.conn.commit()

    def insert_stress_data(self, stress_records: list, user_id: int = 1):
        """Insert multiple stress level records."""
        cursor = self.conn.cursor()
        for record in stress_records:
            cursor.execute("""
                INSERT OR REPLACE INTO stress_data (user_id, timestamp, stress_level)
                VALUES (?, ?, ?)
            """, (
                user_id,
                record.get('datetime') or record.get('timestamp'),
                record.get('stress_level')
            ))
        self.conn.commit()

    def insert_body_composition(self, body_data: dict, user_id: int = 1):
        """Insert body composition record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO body_composition
            (user_id, measurement_date, weight_kg, bmi, body_fat_percentage, body_water_percentage,
             bone_mass_kg, muscle_mass_kg, physique_rating, visceral_fat_rating, metabolic_age, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            body_data.get('measurement_date'),
            body_data.get('weight_kg'),
            body_data.get('bmi'),
            body_data.get('body_fat_percentage'),
            body_data.get('body_water_percentage'),
            body_data.get('bone_mass_kg'),
            body_data.get('muscle_mass_kg'),
            body_data.get('physique_rating'),
            body_data.get('visceral_fat_rating'),
            body_data.get('metabolic_age'),
            body_data.get('source_type', 'garmin_connect')
        ))
        self.conn.commit()

    def _validate_data(self, data: any, data_type: str) -> bool:
        """Validate data before insertion."""
        if data is None:
            logger.warning(f"Received None data for {data_type}")
            return False

        if isinstance(data, dict) and not data:
            logger.warning(f"Received empty dict for {data_type}")
            return False

        if isinstance(data, list) and not data:
            logger.warning(f"Received empty list for {data_type}")
            return False

        return True

    def _safe_json_dumps(self, data: any) -> str:
        """Safely convert data to JSON string."""
        try:
            if isinstance(data, str):
                return data
            return json.dumps(data)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to convert data to JSON: {e}")
            return json.dumps({"error": "serialization_failed", "type": str(type(data))})

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")