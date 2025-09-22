"""Enhanced Garmin data collector using all available API methods."""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from garminconnect import Garmin
from database import TursoDatabase

logger = logging.getLogger(__name__)


class EnhancedGarminCollector:
    def __init__(self, api: Garmin, db: TursoDatabase):
        self.api = api
        self.db = db
        self.rate_limit_delay = 1.0  # Faster for testing
        self.user_id = 1  # Assume single user

    def collect_comprehensive_data(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Collect ALL available data from Garmin Connect using proper API methods.
        """
        logger.info(f"🚀 Enhanced collection for {days_back} days using ALL available APIs")
        start_time = datetime.now()

        results = {}

        try:
            # 1. User Profile & Settings
            results['profile'] = self._collect_user_profile()

            # 2. Daily Health Metrics
            results['daily_steps'] = self._collect_daily_steps(days_back)
            results['floors'] = self._collect_floors(days_back)
            results['intensity_minutes'] = self._collect_intensity_minutes(days_back)
            results['heart_rate'] = self._collect_heart_rate_data(days_back)
            results['resting_hr'] = self._collect_resting_heart_rate(days_back)

            # 3. Advanced Health Metrics
            results['hrv'] = self._collect_hrv_data(days_back)
            results['stress'] = self._collect_stress_data(days_back)
            results['respiration'] = self._collect_respiration_data(days_back)
            results['spo2'] = self._collect_spo2_data(days_back)
            results['body_battery'] = self._collect_body_battery_data(days_back)

            # 4. Activities & Performance
            results['activities'] = self._collect_enhanced_activities(days_back)
            results['training_status'] = self._collect_training_status()
            results['training_readiness'] = self._collect_training_readiness(days_back)
            results['max_metrics'] = self._collect_max_metrics()
            results['lactate_threshold'] = self._collect_lactate_threshold()
            results['race_predictions'] = self._collect_race_predictions()
            results['endurance_score'] = self._collect_endurance_score()
            results['hill_score'] = self._collect_hill_score()

            # 5. Body Composition & Health
            results['sleep'] = self._collect_enhanced_sleep(days_back)
            results['weight'] = self._collect_weight_data(days_back)
            results['body_composition'] = self._collect_body_composition_data(days_back)
            results['blood_pressure'] = self._collect_blood_pressure(days_back)
            results['hydration'] = self._collect_hydration_data(days_back)

            # 6. Goals & Gear
            results['goals'] = self._collect_goals()
            results['gear'] = self._collect_gear_data()
            results['devices'] = self._collect_device_data()

            # 7. Achievements & Challenges
            results['badges'] = self._collect_badges()
            results['challenges'] = self._collect_challenges()

            total_records = sum(
                len(v) if isinstance(v, list) else 1 if v else 0
                for v in results.values()
            )

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Enhanced collection completed: {total_records} records in {duration:.1f}s")

            return results

        except Exception as e:
            logger.error(f"❌ Enhanced collection failed: {e}")
            raise

    def _safe_api_call(self, method_name: str, *args, **kwargs):
        """Safely call API method with error handling and rate limiting."""
        try:
            if hasattr(self.api, method_name):
                method = getattr(self.api, method_name)
                time.sleep(self.rate_limit_delay)
                result = method(*args, **kwargs)
                logger.debug(f"✓ {method_name} - Success")
                return result
            else:
                logger.warning(f"⚠️ {method_name} - Method not available")
                return None
        except Exception as e:
            logger.warning(f"❌ {method_name} - Error: {str(e)[:100]}")
            return None

    def _collect_user_profile(self) -> Dict:
        """Enhanced user profile collection."""
        profile_data = {}

        # Basic profile
        profile_data['full_name'] = self._safe_api_call('get_full_name')
        profile_data['user_profile'] = self._safe_api_call('get_user_profile')
        profile_data['user_summary'] = self._safe_api_call('get_user_summary')
        profile_data['userprofile_settings'] = self._safe_api_call('get_userprofile_settings')
        profile_data['unit_system'] = self._safe_api_call('get_unit_system')

        return {k: v for k, v in profile_data.items() if v is not None}

    def _collect_daily_steps(self, days_back: int) -> List[Dict]:
        """Collect daily step data using proper API."""
        steps_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_steps_data', date)
            if data:
                steps_data.append({
                    'date': date,
                    'steps_data': data
                })

        logger.info(f"✓ Collected {len(steps_data)} days of step data")
        return steps_data

    def _collect_floors(self, days_back: int) -> List[Dict]:
        """Collect floors climbed data."""
        floors_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_floors', date)
            if data:
                floors_data.append({
                    'date': date,
                    'floors_data': data
                })

        logger.info(f"✓ Collected {len(floors_data)} days of floors data")
        return floors_data

    def _collect_intensity_minutes(self, days_back: int) -> List[Dict]:
        """Collect intensity minutes data."""
        intensity_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_intensity_minutes_data', date)
            if data:
                intensity_data.append({
                    'date': date,
                    'intensity_data': data
                })

        logger.info(f"✓ Collected {len(intensity_data)} days of intensity minutes")
        return intensity_data

    def _collect_heart_rate_data(self, days_back: int) -> List[Dict]:
        """Collect heart rate data using proper API."""
        hr_data = []

        for i in range(min(days_back, 7)):  # Limit to avoid too much data
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_heart_rates', date)
            if data:
                hr_data.append({
                    'date': date,
                    'heart_rate_data': data
                })

        logger.info(f"✓ Collected {len(hr_data)} days of heart rate data")
        return hr_data

    def _collect_resting_heart_rate(self, days_back: int) -> List[Dict]:
        """Collect resting heart rate data."""
        rhr_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_rhr_day', date)
            if data:
                rhr_data.append({
                    'date': date,
                    'rhr_data': data
                })

        logger.info(f"✓ Collected {len(rhr_data)} days of RHR data")
        return rhr_data

    def _collect_hrv_data(self, days_back: int) -> List[Dict]:
        """Collect heart rate variability data."""
        hrv_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_hrv_data', date)
            if data:
                hrv_data.append({
                    'date': date,
                    'hrv_data': data
                })

        logger.info(f"✓ Collected {len(hrv_data)} days of HRV data")
        return hrv_data

    def _collect_stress_data(self, days_back: int) -> List[Dict]:
        """Collect stress data using proper API method."""
        stress_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_stress_data', date)
            if data:
                stress_data.append({
                    'date': date,
                    'stress_data': data
                })

        logger.info(f"✓ Collected {len(stress_data)} days of stress data")
        return stress_data

    def _collect_respiration_data(self, days_back: int) -> List[Dict]:
        """Collect respiration rate data."""
        resp_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_respiration_data', date)
            if data:
                resp_data.append({
                    'date': date,
                    'respiration_data': data
                })

        logger.info(f"✓ Collected {len(resp_data)} days of respiration data")
        return resp_data

    def _collect_spo2_data(self, days_back: int) -> List[Dict]:
        """Collect SpO2 (blood oxygen) data."""
        spo2_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_spo2_data', date)
            if data:
                spo2_data.append({
                    'date': date,
                    'spo2_data': data
                })

        logger.info(f"✓ Collected {len(spo2_data)} days of SpO2 data")
        return spo2_data

    def _collect_body_battery_data(self, days_back: int) -> List[Dict]:
        """Collect body battery data using proper API."""
        bb_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            # Try different API methods for body battery
            data = (self._safe_api_call('get_body_battery', date, date) or
                   self._safe_api_call('get_body_battery', date))
            if data:
                bb_data.append({
                    'date': date,
                    'body_battery_data': data
                })

        logger.info(f"✓ Collected {len(bb_data)} days of body battery data")
        return bb_data

    def _collect_enhanced_activities(self, days_back: int) -> List[Dict]:
        """Enhanced activity collection with detailed data."""
        activities = []

        # Get activities list
        activity_list = self._safe_api_call('get_activities', 0, days_back * 5)
        if not activity_list:
            return []

        for activity in activity_list[:50]:  # Limit for testing
            activity_id = activity.get('activityId')
            if not activity_id:
                continue

            # Get detailed data for each activity
            enhanced_activity = {
                'basic': activity,
                'details': self._safe_api_call('get_activity_details', activity_id),
                'splits': self._safe_api_call('get_activity_splits', activity_id),
                'hr_zones': self._safe_api_call('get_activity_hr_in_timezones', activity_id),
                'weather': self._safe_api_call('get_activity_weather', activity_id),
                'gear': self._safe_api_call('get_activity_gear', activity_id),
                'exercise_sets': self._safe_api_call('get_activity_exercise_sets', activity_id),
            }

            activities.append(enhanced_activity)

        logger.info(f"✓ Collected {len(activities)} enhanced activities")
        return activities

    def _collect_training_status(self) -> Dict:
        """Collect training status and load."""
        return self._safe_api_call('get_training_status') or {}

    def _collect_training_readiness(self, days_back: int) -> List[Dict]:
        """Collect training readiness data."""
        readiness_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_training_readiness', date)
            if data:
                readiness_data.append({
                    'date': date,
                    'readiness_data': data
                })

        logger.info(f"✓ Collected {len(readiness_data)} days of training readiness")
        return readiness_data

    def _collect_max_metrics(self) -> Dict:
        """Collect VO2 max and other performance metrics."""
        return self._safe_api_call('get_max_metrics') or {}

    def _collect_lactate_threshold(self) -> Dict:
        """Collect lactate threshold data."""
        return self._safe_api_call('get_lactate_threshold') or {}

    def _collect_race_predictions(self) -> Dict:
        """Collect race time predictions."""
        return self._safe_api_call('get_race_predictions') or {}

    def _collect_endurance_score(self) -> Dict:
        """Collect endurance score."""
        return self._safe_api_call('get_endurance_score') or {}

    def _collect_hill_score(self) -> Dict:
        """Collect hill score."""
        return self._safe_api_call('get_hill_score') or {}

    def _collect_enhanced_sleep(self, days_back: int) -> List[Dict]:
        """Enhanced sleep data collection."""
        sleep_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_sleep_data', date)
            if data:
                sleep_data.append({
                    'date': date,
                    'sleep_data': data
                })

        logger.info(f"✓ Collected {len(sleep_data)} days of enhanced sleep data")
        return sleep_data

    def _collect_weight_data(self, days_back: int) -> List[Dict]:
        """Collect weight and weigh-ins."""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        weight_data = []

        # Daily weigh-ins
        daily_weighins = self._safe_api_call('get_daily_weigh_ins', start_date, end_date)
        if daily_weighins:
            weight_data.extend(daily_weighins)

        # All weigh-ins
        all_weighins = self._safe_api_call('get_weigh_ins', start_date, end_date)
        if all_weighins:
            weight_data.extend(all_weighins)

        logger.info(f"✓ Collected {len(weight_data)} weight records")
        return weight_data

    def _collect_body_composition_data(self, days_back: int) -> List[Dict]:
        """Enhanced body composition collection."""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        data = self._safe_api_call('get_body_composition', start_date, end_date)
        return [data] if data else []

    def _collect_blood_pressure(self, days_back: int) -> List[Dict]:
        """Collect blood pressure data."""
        bp_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_blood_pressure', date)
            if data:
                bp_data.append({
                    'date': date,
                    'blood_pressure_data': data
                })

        logger.info(f"✓ Collected {len(bp_data)} days of blood pressure data")
        return bp_data

    def _collect_hydration_data(self, days_back: int) -> List[Dict]:
        """Collect hydration data."""
        hydration_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._safe_api_call('get_hydration_data', date)
            if data:
                hydration_data.append({
                    'date': date,
                    'hydration_data': data
                })

        logger.info(f"✓ Collected {len(hydration_data)} days of hydration data")
        return hydration_data

    def _collect_goals(self) -> Dict:
        """Collect goals and targets."""
        return self._safe_api_call('get_goals') or {}

    def _collect_gear_data(self) -> Dict:
        """Collect gear and equipment data."""
        gear_data = {}

        gear_data['gear'] = self._safe_api_call('get_gear')
        gear_data['gear_defaults'] = self._safe_api_call('get_gear_defaults')
        gear_data['gear_stats'] = self._safe_api_call('get_gear_stats')

        return {k: v for k, v in gear_data.items() if v is not None}

    def _collect_device_data(self) -> Dict:
        """Collect device information."""
        device_data = {}

        device_data['devices'] = self._safe_api_call('get_devices')
        device_data['device_settings'] = self._safe_api_call('get_device_settings')
        device_data['device_last_used'] = self._safe_api_call('get_device_last_used')
        device_data['primary_training_device'] = self._safe_api_call('get_primary_training_device')

        return {k: v for k, v in device_data.items() if v is not None}

    def _collect_badges(self) -> Dict:
        """Collect badges and achievements."""
        badge_data = {}

        badge_data['earned_badges'] = self._safe_api_call('get_earned_badges')
        badge_data['available_badges'] = self._safe_api_call('get_available_badges')
        badge_data['in_progress_badges'] = self._safe_api_call('get_in_progress_badges')

        return {k: v for k, v in badge_data.items() if v is not None}

    def _collect_challenges(self) -> Dict:
        """Collect challenges and virtual races."""
        challenge_data = {}

        challenge_data['badge_challenges'] = self._safe_api_call('get_badge_challenges')
        challenge_data['available_badge_challenges'] = self._safe_api_call('get_available_badge_challenges')
        challenge_data['adhoc_challenges'] = self._safe_api_call('get_adhoc_challenges')
        challenge_data['virtual_challenges'] = self._safe_api_call('get_inprogress_virtual_challenges')

        return {k: v for k, v in challenge_data.items() if v is not None}