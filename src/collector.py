"""Comprehensive Garmin data collector that pulls all available data."""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from garminconnect import Garmin
from database import TursoDatabase

logger = logging.getLogger(__name__)


class GarminDataCollector:
    def __init__(self, api: Garmin, db: TursoDatabase):
        self.api = api
        self.db = db
        self.rate_limit_delay = 1.5  # Seconds between API calls
        self.user_id = None

    def collect_all_available_data(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Collect all available data from Garmin Connect.
        This is the main entry point that orchestrates all data collection.
        """
        logger.info(f"🚀 Starting comprehensive data collection for {days_back} days")
        start_time = datetime.now()

        # Log collection start
        collection_id = self._log_collection_start("comprehensive", start_time)

        try:
            # First, get user profile
            self._collect_user_profile()

            # Collect all data types
            results = {
                'user_profile': True,
                'daily_stats': self._collect_daily_stats(days_back),
                'activities': self._collect_activities(days_back),
                'sleep': self._collect_sleep_data(days_back),
                'body_composition': self._collect_body_composition(days_back),
                'heart_rate': self._collect_heart_rate_data(days_back),
                'stress': self._collect_stress_data(days_back),
            }

            # Calculate total records
            total_records = sum(
                r if isinstance(r, int) else len(r) if isinstance(r, list) else 1
                for r in results.values()
            )

            # Log collection completion
            self._log_collection_end(collection_id, "success", total_records)

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Collection completed: {total_records} records in {duration:.1f}s")

            return results

        except Exception as e:
            self._log_collection_end(collection_id, "error", 0, str(e))
            logger.error(f"❌ Collection failed: {e}")
            raise

    def _collect_user_profile(self):
        """Collect and store user profile information."""
        try:
            logger.info("Collecting user profile...")

            # Get various profile data
            full_name = self.api.full_name
            display_name = self.api.display_name
            user_settings = self.api.get_user_settings() if hasattr(self.api, 'get_user_settings') else {}

            cursor = self.db.conn.cursor()

            # Check if user exists
            cursor.execute("SELECT id FROM user_profile WHERE display_name = ?", (full_name,))
            existing = cursor.fetchone()

            if existing:
                self.user_id = existing[0]
                # Update existing user
                cursor.execute("""
                    UPDATE user_profile
                    SET full_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (full_name, self.user_id))
            else:
                # Insert new user
                cursor.execute("""
                    INSERT INTO user_profile (display_name, full_name)
                    VALUES (?, ?)
                """, (
                    display_name or full_name,
                    full_name
                ))
                self.user_id = cursor.lastrowid

            self.db.conn.commit()
            logger.info(f"✓ User profile stored (ID: {self.user_id})")

        except Exception as e:
            logger.error(f"Failed to collect user profile: {e}")
            # Set default user_id if profile collection fails
            self.user_id = 1

    def _collect_daily_stats(self, days_back: int) -> int:
        """Collect daily summary statistics."""
        logger.info(f"Collecting daily stats for {days_back} days...")
        cursor = self.db.conn.cursor()
        records_collected = 0

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            try:
                # Collect various daily metrics
                stats = self.api.get_stats(date)
                body_battery = self.api.get_body_battery(date, date) if hasattr(self.api, 'get_body_battery') else None
                heart_rates = self.api.get_heart_rates(date) if hasattr(self.api, 'get_heart_rates') else None
                hydration = self.api.get_hydration(date) if hasattr(self.api, 'get_hydration') else None
                sleep_data = self.api.get_sleep_data(date) if hasattr(self.api, 'get_sleep_data') else None
                stress = self.api.get_all_day_stress(date) if hasattr(self.api, 'get_all_day_stress') else None
                steps = self.api.get_daily_steps(date, date) if hasattr(self.api, 'get_daily_steps') else None

                # Prepare data for insertion
                data = {
                    'date': date,
                    'user_id': self.user_id,
                    'total_steps': stats.get('totalSteps', 0) if stats else 0,
                    'total_distance_meters': stats.get('totalDistanceMeters', 0) if stats else 0,
                    'active_seconds': stats.get('activeSeconds', 0) if stats else 0,
                    'highly_active_seconds': stats.get('highlyActiveSeconds', 0) if stats else 0,
                    'sedentary_seconds': stats.get('sedentarySeconds', 0) if stats else 0,
                    'calories_total': stats.get('totalKilocalories', 0) if stats else 0,
                    'calories_active': stats.get('activeKilocalories', 0) if stats else 0,
                    'floors_climbed': stats.get('floorsAscended', 0) if stats else 0,
                }

                # Add heart rate data
                if heart_rates:
                    data.update({
                        'resting_heart_rate': heart_rates.get('restingHeartRate'),
                        'min_heart_rate': heart_rates.get('minHeartRate'),
                        'max_heart_rate': heart_rates.get('maxHeartRate'),
                    })

                # Add body battery data
                if body_battery:
                    bb_values = body_battery[0] if isinstance(body_battery, list) and body_battery else body_battery
                    if bb_values:
                        data.update({
                            'body_battery_charged': bb_values.get('charged'),
                            'body_battery_drained': bb_values.get('drained'),
                            'body_battery_highest': bb_values.get('max'),
                            'body_battery_lowest': bb_values.get('min'),
                        })

                # Add stress data
                if stress:
                    data.update({
                        'avg_stress_level': stress.get('averageStressLevel'),
                        'max_stress_level': stress.get('maxStressLevel'),
                    })

                # Add hydration
                if hydration:
                    data['hydration_ml'] = hydration.get('valueInML')

                # Add sleep summary
                if sleep_data:
                    sleep = sleep_data.get('dailySleepDTO', {}) if isinstance(sleep_data, dict) else {}
                    if sleep:
                        data.update({
                            'sleep_score': sleep.get('sleepScores', {}).get('overall', {}).get('qualifierKey'),
                            'total_sleep_seconds': sleep.get('sleepTimeSeconds'),
                        })

                # Insert or replace daily stats
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                cursor.execute(f"""
                    INSERT OR REPLACE INTO daily_stats ({columns})
                    VALUES ({placeholders})
                """, tuple(data.values()))

                records_collected += 1
                time.sleep(self.rate_limit_delay)

            except Exception as e:
                logger.warning(f"Failed to collect data for {date}: {e}")
                continue

        self.db.conn.commit()
        logger.info(f"✓ Collected {records_collected} daily stat records")
        return records_collected

    def _collect_activities(self, days_back: int) -> int:
        """Collect activity data."""
        logger.info(f"Collecting activities for {days_back} days...")
        cursor = self.db.conn.cursor()
        records_collected = 0

        try:
            # Get activities list
            activities = self.api.get_activities(0, 100)  # Get last 100 activities

            for activity in activities:
                if not activity:
                    continue

                activity_id = str(activity.get('activityId', ''))
                if not activity_id:
                    continue

                # Skip if already exists
                cursor.execute("SELECT id FROM activities WHERE activity_id = ?", (activity_id,))
                if cursor.fetchone():
                    continue

                # Get detailed activity data
                try:
                    time.sleep(self.rate_limit_delay)
                    detailed = self.api.get_activity_evaluation(activity_id)
                except:
                    detailed = activity

                # Prepare activity data
                data = {
                    'activity_id': activity_id,
                    'user_id': self.user_id,
                    'activity_name': activity.get('activityName'),
                    'activity_type': activity.get('activityType', {}).get('typeKey') if isinstance(activity.get('activityType'), dict) else None,
                    'sport_type': activity.get('eventType', {}).get('typeKey') if isinstance(activity.get('eventType'), dict) else None,
                    'start_time_local': activity.get('startTimeLocal'),
                    'start_time_gmt': activity.get('startTimeGMT'),
                    'duration_seconds': activity.get('duration'),
                    'distance_meters': activity.get('distance'),
                    'elevation_gain_meters': activity.get('elevationGain'),
                    'elevation_loss_meters': activity.get('elevationLoss'),
                    'avg_speed_mps': activity.get('averageSpeed'),
                    'max_speed_mps': activity.get('maxSpeed'),
                    'avg_heart_rate': activity.get('averageHR'),
                    'max_heart_rate': activity.get('maxHR'),
                    'calories': activity.get('calories'),
                    'start_latitude': activity.get('startLatitude'),
                    'start_longitude': activity.get('startLongitude'),
                    'end_latitude': activity.get('endLatitude'),
                    'end_longitude': activity.get('endLongitude'),
                    'has_polyline': activity.get('hasPolyline', False),
                    'has_splits': activity.get('hasSplits', False),
                    'manual_activity': activity.get('manual', False),
                    'favorite': activity.get('favorite', False),
                    'pr_flag': activity.get('pr', False),
                    'device_id': str(activity.get('deviceId')) if activity.get('deviceId') else None,
                    'raw_json': json.dumps(activity),
                }

                # Filter out None values and insert
                filtered_data = {k: v for k, v in data.items() if v is not None}
                columns = ', '.join(filtered_data.keys())
                placeholders = ', '.join(['?' for _ in filtered_data])

                cursor.execute(f"""
                    INSERT INTO activities ({columns})
                    VALUES ({placeholders})
                """, tuple(filtered_data.values()))

                records_collected += 1

                # Check date limit
                if activity.get('startTimeLocal'):
                    activity_date = datetime.fromisoformat(activity['startTimeLocal'].replace('Z', '+00:00'))
                    if (datetime.now() - activity_date).days > days_back:
                        break

        except Exception as e:
            logger.error(f"Failed to collect activities: {e}")

        self.db.conn.commit()
        logger.info(f"✓ Collected {records_collected} activity records")
        return records_collected

    def _collect_sleep_data(self, days_back: int) -> int:
        """Collect detailed sleep data."""
        logger.info(f"Collecting sleep data for {days_back} days...")
        cursor = self.db.conn.cursor()
        records_collected = 0

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            try:
                time.sleep(self.rate_limit_delay)
                sleep_data = self.api.get_sleep_data(date)

                if not sleep_data:
                    continue

                # Extract daily sleep DTO
                daily_sleep = sleep_data.get('dailySleepDTO', {}) if isinstance(sleep_data, dict) else {}
                if not daily_sleep:
                    continue

                # Prepare sleep record
                data = {
                    'user_id': self.user_id,
                    'calendar_date': date,
                    'sleep_start_timestamp_gmt': daily_sleep.get('sleepStartTimestampGMT'),
                    'sleep_end_timestamp_gmt': daily_sleep.get('sleepEndTimestampGMT'),
                    'sleep_start_timestamp_local': daily_sleep.get('sleepStartTimestampLocal'),
                    'sleep_end_timestamp_local': daily_sleep.get('sleepEndTimestampLocal'),
                    'unmeasurable_seconds': daily_sleep.get('unmeasurableSleepSeconds'),
                    'deep_sleep_seconds': daily_sleep.get('deepSleepSeconds'),
                    'light_sleep_seconds': daily_sleep.get('lightSleepSeconds'),
                    'rem_sleep_seconds': daily_sleep.get('remSleepSeconds'),
                    'awake_seconds': daily_sleep.get('awakeSleepSeconds'),
                    'avg_respiration_value': daily_sleep.get('averageRespirationValue'),
                    'avg_spo2_value': daily_sleep.get('averageSpO2Value'),
                    'lowest_spo2_value': daily_sleep.get('lowestSpO2Value'),
                    'highest_spo2_value': daily_sleep.get('highestSpO2Value'),
                    'time_to_fall_asleep_seconds': daily_sleep.get('sleepTimeSeconds'),
                    'restless_moments_count': daily_sleep.get('restlessMomentsCount'),
                    'raw_json': json.dumps(sleep_data),
                }

                # Add sleep scores if available
                scores = daily_sleep.get('sleepScores', {})
                if scores:
                    data.update({
                        'overall_sleep_score': scores.get('overall', {}).get('value'),
                        'sleep_quality_score': scores.get('quality', {}).get('value'),
                        'sleep_recovery_score': scores.get('recovery', {}).get('value'),
                        'sleep_restfulness_score': scores.get('restfulness', {}).get('value'),
                        'sleep_duration_score': scores.get('duration', {}).get('value'),
                        'sleep_interruptions_score': scores.get('interruptions', {}).get('value'),
                    })

                # Filter None values and insert
                filtered_data = {k: v for k, v in data.items() if v is not None}
                columns = ', '.join(filtered_data.keys())
                placeholders = ', '.join(['?' for _ in filtered_data])

                cursor.execute(f"""
                    INSERT OR REPLACE INTO sleep_data ({columns})
                    VALUES ({placeholders})
                """, tuple(filtered_data.values()))

                records_collected += 1

            except Exception as e:
                logger.warning(f"Failed to collect sleep data for {date}: {e}")
                continue

        self.db.conn.commit()
        logger.info(f"✓ Collected {records_collected} sleep records")
        return records_collected

    def _collect_body_composition(self, days_back: int) -> int:
        """Collect body composition and weight data."""
        logger.info(f"Collecting body composition for {days_back} days...")
        cursor = self.db.conn.cursor()
        records_collected = 0

        try:
            # Get weight data for date range
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

            time.sleep(self.rate_limit_delay)
            weight_data = self.api.get_body_composition(start_date, end_date)

            if weight_data and isinstance(weight_data, dict):
                weight_list = weight_data.get('dateWeightList', [])

                for entry in weight_list:
                    if not entry:
                        continue

                    data = {
                        'user_id': self.user_id,
                        'measurement_date': entry.get('date'),
                        'weight_kg': entry.get('weight'),
                        'bmi': entry.get('bmi'),
                        'body_fat_percentage': entry.get('bodyFatPercentage'),
                        'body_water_percentage': entry.get('bodyWaterPercentage'),
                        'bone_mass_kg': entry.get('boneMass'),
                        'muscle_mass_kg': entry.get('muscleMass'),
                        'physique_rating': entry.get('physiqueRating'),
                        'visceral_fat_rating': entry.get('visceralFatRating'),
                        'metabolic_age': entry.get('metabolicAge'),
                        'source_type': entry.get('sourceType'),
                    }

                    # Filter None values
                    filtered_data = {k: v for k, v in data.items() if v is not None}
                    columns = ', '.join(filtered_data.keys())
                    placeholders = ', '.join(['?' for _ in filtered_data])

                    cursor.execute(f"""
                        INSERT OR IGNORE INTO body_composition ({columns})
                        VALUES ({placeholders})
                    """, tuple(filtered_data.values()))

                    records_collected += 1

        except Exception as e:
            logger.warning(f"Failed to collect body composition: {e}")

        self.db.conn.commit()
        logger.info(f"✓ Collected {records_collected} body composition records")
        return records_collected

    def _collect_heart_rate_data(self, days_back: int) -> int:
        """Collect intraday heart rate data (limited days due to volume)."""
        logger.info(f"Collecting heart rate data for last 3 days...")
        cursor = self.db.conn.cursor()
        records_collected = 0

        # Limit to 3 days for intraday data
        days_to_collect = min(3, days_back)

        for i in range(days_to_collect):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            try:
                time.sleep(self.rate_limit_delay)
                hr_data = self.api.get_heart_rates(date)

                if hr_data and 'heartRateValues' in hr_data:
                    for hr_entry in hr_data['heartRateValues']:
                        if hr_entry and len(hr_entry) >= 2:
                            timestamp = hr_entry[0]  # Unix timestamp in milliseconds
                            heart_rate = hr_entry[1]

                            if heart_rate and heart_rate > 0:
                                # Convert timestamp
                                dt = datetime.fromtimestamp(timestamp / 1000)

                                cursor.execute("""
                                    INSERT OR IGNORE INTO heart_rate_data (user_id, timestamp, heart_rate)
                                    VALUES (?, ?, ?)
                                """, (self.user_id, dt, heart_rate))

                                records_collected += 1

            except Exception as e:
                logger.warning(f"Failed to collect heart rate for {date}: {e}")

        self.db.conn.commit()
        logger.info(f"✓ Collected {records_collected} heart rate records")
        return records_collected

    def _collect_stress_data(self, days_back: int) -> int:
        """Collect stress level data."""
        logger.info(f"Collecting stress data for last 7 days...")
        cursor = self.db.conn.cursor()
        records_collected = 0

        # Limit stress data to 7 days
        days_to_collect = min(7, days_back)

        for i in range(days_to_collect):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            try:
                time.sleep(self.rate_limit_delay)
                stress_data = self.api.get_all_day_stress(date) if hasattr(self.api, 'get_all_day_stress') else None

                if stress_data and 'stressValuesArray' in stress_data:
                    for stress_entry in stress_data['stressValuesArray']:
                        if stress_entry and len(stress_entry) >= 2:
                            timestamp = stress_entry[0]
                            stress_level = stress_entry[1]

                            if stress_level and stress_level >= 0:
                                dt = datetime.fromtimestamp(timestamp / 1000)

                                cursor.execute("""
                                    INSERT OR IGNORE INTO stress_data (user_id, timestamp, stress_level)
                                    VALUES (?, ?, ?)
                                """, (self.user_id, dt, stress_level))

                                records_collected += 1

            except Exception as e:
                logger.warning(f"Failed to collect stress for {date}: {e}")

        self.db.conn.commit()
        logger.info(f"✓ Collected {records_collected} stress records")
        return records_collected

    def _log_collection_start(self, collection_type: str, start_time: datetime) -> int:
        """Log the start of a collection run."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO collection_log (collection_type, start_time, status)
            VALUES (?, ?, 'running')
        """, (collection_type, start_time.isoformat()))
        self.db.conn.commit()
        return cursor.lastrowid

    def _log_collection_end(self, collection_id: int, status: str, records: int, error: str = None):
        """Log the completion of a collection run."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE collection_log
            SET end_time = ?, status = ?, records_collected = ?, error_message = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), status, records, error, collection_id))
        self.db.conn.commit()