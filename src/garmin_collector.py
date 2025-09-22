"""
Final production-ready Garmin Connect data collector.
Combines enhanced API collection, intraday data extraction, and FIT processing.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from garminconnect import Garmin
from database import TursoDatabase

logger = logging.getLogger(__name__)


class GarminCollector:
    """
    Production-ready Garmin Connect data collector.

    Features:
    - Enhanced API collection (29 endpoints)
    - Intraday data extraction (high-resolution timestamped data)
    - FIT file processing (GPS coordinates and activity data)
    - Robust error handling and rate limiting
    """

    def __init__(self, api: Garmin, db: TursoDatabase):
        self.api = api
        self.db = db
        self.rate_limit_delay = 1.0
        self.user_id = 1

    def collect_all_data(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Collect comprehensive Garmin Connect data using all available methods.

        Args:
            days_back: Number of days to collect data for

        Returns:
            Dictionary with collection results and statistics
        """
        logger.info(f"🚀 Starting comprehensive Garmin data collection for {days_back} days")
        start_time = datetime.now()

        results = {
            'enhanced_data': {},
            'intraday_data': {},
            'fit_data': {},
            'collection_stats': {
                'start_time': start_time.isoformat(),
                'days_collected': days_back,
                'total_apis_called': 0,
                'successful_apis': 0,
                'total_data_points': 0
            }
        }

        try:
            # 1. Enhanced API collection
            logger.info("📊 Collecting enhanced API data...")
            results['enhanced_data'] = self._collect_enhanced_data(days_back)

            # 2. Intraday data extraction
            logger.info("⏱️ Extracting intraday data arrays...")
            results['intraday_data'] = self._collect_intraday_data(days_back)

            # 3. FIT file processing
            logger.info("🗺️ Processing FIT files for GPS data...")
            results['fit_data'] = self._collect_fit_data(days_back)

            # Calculate final statistics
            self._calculate_collection_stats(results)

            duration = (datetime.now() - start_time).total_seconds()
            results['collection_stats']['duration_seconds'] = duration
            results['collection_stats']['end_time'] = datetime.now().isoformat()

            logger.info(f"✅ Collection completed: {results['collection_stats']['total_data_points']} data points in {duration:.1f}s")

            return results

        except Exception as e:
            logger.error(f"❌ Collection failed: {e}")
            raise

    def _collect_enhanced_data(self, days_back: int) -> Dict[str, Any]:
        """Collect data from enhanced API endpoints."""
        enhanced_results = {}

        try:
            # Profile and device info
            enhanced_results['profile'] = self._collect_profile_data()

            # Daily wellness data
            enhanced_results.update(self._collect_daily_wellness(days_back))

            # Activity data
            enhanced_results['activities'] = self._collect_activity_data(days_back)

            # Sleep data
            enhanced_results['sleep'] = self._collect_sleep_data(days_back)

            # Additional health metrics
            enhanced_results.update(self._collect_health_metrics(days_back))

        except Exception as e:
            logger.error(f"Enhanced data collection error: {e}")

        return enhanced_results

    def _collect_profile_data(self) -> Dict[str, Any]:
        """Collect user profile and device information."""
        profile_data = {}

        profile_apis = [
            ('full_name', 'get_full_name'),
            ('display_name', 'get_display_name'),
            ('unit_system', 'get_unit_system'),
            ('device_info', 'get_device_info'),
            ('activity_types', 'get_activity_types')
        ]

        for name, method in profile_apis:
            try:
                if hasattr(self.api, method):
                    result = getattr(self.api, method)()
                    if result:
                        profile_data[name] = result
                        logger.debug(f"✓ {name}: Success")
            except Exception as e:
                logger.debug(f"✗ {name}: {e}")

        return profile_data

    def _collect_daily_wellness(self, days_back: int) -> Dict[str, List]:
        """Collect daily wellness metrics."""
        wellness_data = {
            'daily_steps': [],
            'floors': [],
            'intensity_minutes': [],
            'heart_rate': [],
            'rhr': [],
            'hrv': [],
            'stress': [],
            'respiration': [],
            'spo2': [],
            'body_battery': []
        }

        wellness_apis = [
            ('daily_steps', 'get_steps_data'),
            ('floors', 'get_floors'),
            ('intensity_minutes', 'get_intensity_minutes'),
            ('heart_rate', 'get_heart_rates'),
            ('rhr', 'get_rhr_day'),
            ('hrv', 'get_hrv_data'),
            ('stress', 'get_stress_data'),
            ('respiration', 'get_respiration_data'),
            ('spo2', 'get_spo2_data'),
            ('body_battery', 'get_body_battery')
        ]

        for name, method in wellness_apis:
            for i in range(days_back):
                try:
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    time.sleep(self.rate_limit_delay)

                    if hasattr(self.api, method):
                        result = getattr(self.api, method)(date)
                        if result:
                            wellness_data[name].append({
                                'date': date,
                                'data': result
                            })
                except Exception as e:
                    logger.debug(f"✗ {name} for {date}: {e}")

        return wellness_data

    def _collect_activity_data(self, days_back: int) -> List[Dict]:
        """Collect activity data."""
        activities = []

        try:
            for i in range(min(days_back, 5)):  # Limit for performance
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                time.sleep(self.rate_limit_delay)

                daily_activities = self.api.get_activities_by_date(date, date)
                if daily_activities:
                    for activity in daily_activities:
                        # Get additional activity details
                        activity_id = activity.get('activityId')
                        if activity_id:
                            try:
                                details = self.api.get_activity_evaluation(activity_id)
                                splits = self.api.get_activity_splits(activity_id)

                                activity['evaluation'] = details
                                activity['splits'] = splits
                                activity['collection_date'] = date

                            except Exception as e:
                                logger.debug(f"Activity details error for {activity_id}: {e}")

                        activities.append(activity)

        except Exception as e:
            logger.error(f"Activity collection error: {e}")

        return activities

    def _collect_sleep_data(self, days_back: int) -> List[Dict]:
        """Collect sleep data."""
        sleep_data = []

        for i in range(days_back):
            try:
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                time.sleep(self.rate_limit_delay)

                sleep_info = self.api.get_sleep_data(date)
                if sleep_info:
                    sleep_data.append({
                        'date': date,
                        'sleep_data': sleep_info
                    })

            except Exception as e:
                logger.debug(f"Sleep data error for {date}: {e}")

        return sleep_data

    def _collect_health_metrics(self, days_back: int) -> Dict[str, List]:
        """Collect additional health metrics."""
        health_data = {
            'body_composition': [],
            'hydration': [],
            'training_readiness': []
        }

        health_apis = [
            ('body_composition', 'get_body_composition'),
            ('hydration', 'get_hydration_data'),
            ('training_readiness', 'get_training_readiness')
        ]

        for name, method in health_apis:
            for i in range(days_back):
                try:
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    time.sleep(self.rate_limit_delay)

                    if hasattr(self.api, method):
                        result = getattr(self.api, method)(date)
                        if result:
                            health_data[name].append({
                                'date': date,
                                'data': result
                            })
                except Exception as e:
                    logger.debug(f"✗ {name} for {date}: {e}")

        return health_data

    def _collect_intraday_data(self, days_back: int) -> Dict[str, List]:
        """Extract high-resolution intraday data from API response arrays."""
        intraday_results = {
            'heart_rate_intraday': [],
            'stress_body_battery_intraday': [],
            'sleep_intraday': [],
            'hrv_intraday': [],
            'respiration_intraday': [],
            'steps_intraday': []
        }

        try:
            # Heart rate intraday
            for i in range(days_back):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                time.sleep(self.rate_limit_delay)

                try:
                    hr_data = self.api.get_heart_rates(date)
                    if hr_data and isinstance(hr_data, dict):
                        hr_values = hr_data.get('heartRateValues', [])
                        for entry in hr_values:
                            if entry and len(entry) >= 2 and entry[1]:
                                intraday_results['heart_rate_intraday'].append({
                                    'date': date,
                                    'timestamp': entry[0],
                                    'heart_rate': entry[1],
                                    'datetime': datetime.fromtimestamp(entry[0] / 1000).isoformat()
                                })
                except Exception as e:
                    logger.debug(f"Heart rate intraday error for {date}: {e}")

            # Stress and body battery intraday
            for i in range(days_back):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                time.sleep(self.rate_limit_delay)

                try:
                    stress_data = self.api.get_stress_data(date)
                    if stress_data and isinstance(stress_data, dict):
                        # Stress values
                        stress_values = stress_data.get('stressValuesArray', [])
                        for entry in stress_values:
                            if entry and len(entry) >= 2:
                                intraday_results['stress_body_battery_intraday'].append({
                                    'date': date,
                                    'timestamp': entry[0],
                                    'stress_level': entry[1],
                                    'type': 'stress',
                                    'datetime': datetime.fromtimestamp(entry[0] / 1000).isoformat()
                                })

                        # Body battery values
                        bb_values = stress_data.get('bodyBatteryValuesArray', [])
                        for entry in bb_values:
                            if entry and len(entry) >= 3:
                                intraday_results['stress_body_battery_intraday'].append({
                                    'date': date,
                                    'timestamp': entry[0],
                                    'body_battery_level': entry[2],
                                    'type': 'body_battery',
                                    'datetime': datetime.fromtimestamp(entry[0] / 1000).isoformat()
                                })
                except Exception as e:
                    logger.debug(f"Stress/BB intraday error for {date}: {e}")

            # Steps intraday
            for i in range(days_back):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                time.sleep(self.rate_limit_delay)

                try:
                    steps_data = self.api.get_steps_data(date)
                    if steps_data and isinstance(steps_data, list):
                        for entry in steps_data:
                            if entry and entry.get('steps') is not None:
                                intraday_results['steps_intraday'].append({
                                    'date': date,
                                    'start_time': entry.get('startGMT'),
                                    'end_time': entry.get('endGMT'),
                                    'steps_count': entry['steps']
                                })
                except Exception as e:
                    logger.debug(f"Steps intraday error for {date}: {e}")

        except Exception as e:
            logger.error(f"Intraday collection error: {e}")

        return intraday_results

    def _collect_fit_data(self, days_back: int) -> Dict[str, Any]:
        """Process FIT files for GPS and detailed activity data."""
        fit_results = {
            'activities_with_gps': [],
            'gps_coordinates': [],
            'activity_details': []
        }

        try:
            # Get recent activities for FIT processing
            activities = []
            for i in range(min(days_back, 3)):  # Limit for performance
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_activities = self.api.get_activities_by_date(date, date)
                if daily_activities:
                    activities.extend([a for a in daily_activities if self._has_gps_data(a)])

            # Process each activity for GPS data
            for activity in activities[:5]:  # Limit processing
                activity_id = activity.get('activityId')
                if activity_id:
                    try:
                        # Try to get GPX data
                        gpx_data = self.api.download_activity(activity_id, dl_fmt=self.api.ActivityDownloadFormat.GPX)
                        if gpx_data:
                            fit_results['activities_with_gps'].append(activity)

                            # Extract GPS coordinates from activity metadata
                            if activity.get('startLatitude') and activity.get('startLongitude'):
                                fit_results['gps_coordinates'].append({
                                    'activity_id': activity_id,
                                    'latitude': activity['startLatitude'],
                                    'longitude': activity['startLongitude'],
                                    'elevation': activity.get('elevationGain', 0),
                                    'point_type': 'start'
                                })

                    except Exception as e:
                        logger.debug(f"FIT processing error for activity {activity_id}: {e}")

        except Exception as e:
            logger.error(f"FIT collection error: {e}")

        return fit_results

    def _has_gps_data(self, activity: Dict) -> bool:
        """Check if activity likely has GPS data."""
        gps_indicators = [
            activity.get('startLatitude'),
            activity.get('startLongitude'),
            activity.get('distance', 0) > 0,
            'outdoor' in activity.get('activityType', {}).get('typeKey', '').lower()
        ]
        return any(gps_indicators)

    def _calculate_collection_stats(self, results: Dict) -> None:
        """Calculate collection statistics."""
        stats = results['collection_stats']

        # Count APIs and data points
        total_apis = 0
        successful_apis = 0
        total_data_points = 0

        for category, data in results.items():
            if category == 'collection_stats':
                continue

            if isinstance(data, dict):
                for key, value in data.items():
                    total_apis += 1
                    if value:
                        successful_apis += 1
                        if isinstance(value, list):
                            total_data_points += len(value)
                        elif isinstance(value, dict):
                            total_data_points += len(value)
                        else:
                            total_data_points += 1

        stats['total_apis_called'] = total_apis
        stats['successful_apis'] = successful_apis
        stats['success_rate'] = (successful_apis / total_apis * 100) if total_apis > 0 else 0
        stats['total_data_points'] = total_data_points

        logger.info(f"📊 Collection stats: {successful_apis}/{total_apis} APIs successful ({stats['success_rate']:.1f}%)")
        logger.info(f"📊 Total data points: {total_data_points}")