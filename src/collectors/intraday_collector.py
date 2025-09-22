"""Intraday data extraction collector based on Garmin Grafana patterns."""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from garminconnect import Garmin
from ..core.database import TursoDatabase

logger = logging.getLogger(__name__)


class IntradayGarminCollector:
    def __init__(self, api: Garmin, db: TursoDatabase):
        self.api = api
        self.db = db
        self.rate_limit_delay = 1.0
        self.user_id = 1

    def collect_intraday_data(self, days_back: int = 3) -> Dict[str, Any]:
        """
        Extract intraday data arrays from API responses like Garmin Grafana does.
        """
        logger.info(f"📊 Intraday collection for {days_back} days using array extraction")
        start_time = datetime.now()

        results = {}

        try:
            # COMPONENT 3A: Extract intraday arrays from working APIs
            results['heart_rate_intraday'] = self._extract_heart_rate_intraday(days_back)
            results['stress_and_body_battery_intraday'] = self._extract_stress_body_battery_intraday(days_back)
            results['sleep_intraday'] = self._extract_sleep_intraday(days_back)
            results['hrv_intraday'] = self._extract_hrv_intraday(days_back)
            results['respiration_intraday'] = self._extract_respiration_intraday(days_back)

            # COMPONENT 3B: Try problematic APIs with different approaches
            results['steps_intraday_attempt'] = self._attempt_steps_intraday(days_back)

            # Calculate total intraday points
            total_points = sum(
                len(v) if isinstance(v, list) else 0
                for v in results.values()
            )

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Intraday collection completed: {total_points} data points in {duration:.1f}s")

            return results

        except Exception as e:
            logger.error(f"❌ Intraday collection failed: {e}")
            raise

    def _safe_api_call_intraday(self, method_name: str, *args, **kwargs):
        """API call optimized for intraday data extraction."""
        try:
            if hasattr(self.api, method_name):
                method = getattr(self.api, method_name)
                time.sleep(self.rate_limit_delay)

                result = method(*args, **kwargs)

                if result:
                    # Log the structure for intraday analysis
                    if isinstance(result, dict):
                        keys = list(result.keys())
                        logger.debug(f"🔍 {method_name} - Dict keys: {keys[:5]}...")
                    elif isinstance(result, list):
                        logger.debug(f"🔍 {method_name} - List with {len(result)} items")

                    logger.info(f"✅ {method_name} - Success: {type(result)}")
                else:
                    logger.warning(f"📭 {method_name} - Empty result")
                return result
            else:
                logger.error(f"❌ {method_name} - Method not available")
                return None
        except Exception as e:
            logger.error(f"❌ {method_name} - Error: {str(e)}")
            return None

    # COMPONENT 3A: Extract intraday arrays from working APIs
    def _extract_heart_rate_intraday(self, days_back: int) -> List[Dict]:
        """Extract intraday heart rate data from heartRateValues array."""
        hr_intraday_points = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            hr_data = self._safe_api_call_intraday('get_heart_rates', date)
            if hr_data and isinstance(hr_data, dict):
                # Extract heartRateValues array as done in Garmin Grafana
                hr_values = hr_data.get('heartRateValues', [])
                logger.info(f"Found {len(hr_values)} HR values for {date}")

                for entry in hr_values:
                    if entry and len(entry) >= 2 and entry[1]:  # [timestamp, hr_value]
                        hr_intraday_points.append({
                            'date': date,
                            'timestamp': entry[0],  # Unix timestamp in milliseconds
                            'heart_rate': entry[1],
                            'datetime': datetime.fromtimestamp(entry[0] / 1000).isoformat()
                        })

        logger.info(f"✓ Heart rate intraday: {len(hr_intraday_points)} data points")
        return hr_intraday_points

    def _extract_stress_body_battery_intraday(self, days_back: int) -> List[Dict]:
        """Extract stress and body battery intraday data from arrays."""
        stress_bb_points = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            stress_data = self._safe_api_call_intraday('get_stress_data', date)
            if stress_data and isinstance(stress_data, dict):
                # Extract stressValuesArray
                stress_values = stress_data.get('stressValuesArray', [])
                logger.info(f"Found {len(stress_values)} stress values for {date}")

                for entry in stress_values:
                    if entry and len(entry) >= 2 and (entry[1] or entry[1] == 0):
                        stress_bb_points.append({
                            'date': date,
                            'timestamp': entry[0],
                            'stress_level': entry[1],
                            'type': 'stress',
                            'datetime': datetime.fromtimestamp(entry[0] / 1000).isoformat()
                        })

                # Extract bodyBatteryValuesArray
                bb_values = stress_data.get('bodyBatteryValuesArray', [])
                logger.info(f"Found {len(bb_values)} body battery values for {date}")

                for entry in bb_values:
                    if entry and len(entry) >= 3 and (entry[2] or entry[2] == 0):
                        stress_bb_points.append({
                            'date': date,
                            'timestamp': entry[0],
                            'body_battery_level': entry[2],
                            'type': 'body_battery',
                            'datetime': datetime.fromtimestamp(entry[0] / 1000).isoformat()
                        })

        logger.info(f"✓ Stress/Body Battery intraday: {len(stress_bb_points)} data points")
        return stress_bb_points

    def _extract_sleep_intraday(self, days_back: int) -> List[Dict]:
        """Extract detailed sleep intraday data from multiple arrays."""
        sleep_intraday_points = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            sleep_data = self._safe_api_call_intraday('get_sleep_data', date)
            if sleep_data and isinstance(sleep_data, dict):

                # Sleep movement data
                sleep_movement = sleep_data.get('sleepMovement', [])
                for entry in sleep_movement:
                    if entry and entry.get('startGMT'):
                        sleep_intraday_points.append({
                            'date': date,
                            'start_time': entry['startGMT'],
                            'end_time': entry.get('endGMT'),
                            'activity_level': entry.get('activityLevel', -1),
                            'type': 'sleep_movement'
                        })

                # Sleep levels data
                sleep_levels = sleep_data.get('sleepLevels', [])
                for entry in sleep_levels:
                    if entry and entry.get('startGMT') and (entry.get('activityLevel') is not None):
                        sleep_intraday_points.append({
                            'date': date,
                            'start_time': entry['startGMT'],
                            'end_time': entry.get('endGMT'),
                            'sleep_stage_level': entry.get('activityLevel'),
                            'type': 'sleep_stage'
                        })

                # Sleep heart rate
                sleep_hr = sleep_data.get('sleepHeartRate', [])
                for entry in sleep_hr:
                    if entry and entry.get('value') and entry.get('startGMT'):
                        sleep_intraday_points.append({
                            'date': date,
                            'timestamp': entry['startGMT'],
                            'heart_rate': entry['value'],
                            'type': 'sleep_heart_rate'
                        })

                # Sleep SpO2
                spo2_data = sleep_data.get('wellnessEpochSPO2DataDTOList', [])
                for entry in spo2_data:
                    if entry and entry.get('spo2Reading') and entry.get('epochTimestamp'):
                        sleep_intraday_points.append({
                            'date': date,
                            'timestamp': entry['epochTimestamp'],
                            'spo2_reading': entry['spo2Reading'],
                            'type': 'sleep_spo2'
                        })

                # Sleep respiration
                resp_data = sleep_data.get('wellnessEpochRespirationDataDTOList', [])
                for entry in resp_data:
                    if entry and entry.get('respirationValue') and entry.get('startTimeGMT'):
                        sleep_intraday_points.append({
                            'date': date,
                            'timestamp': entry['startTimeGMT'],
                            'respiration_value': entry['respirationValue'],
                            'type': 'sleep_respiration'
                        })

        logger.info(f"✓ Sleep intraday: {len(sleep_intraday_points)} data points")
        return sleep_intraday_points

    def _extract_hrv_intraday(self, days_back: int) -> List[Dict]:
        """Extract HRV intraday readings."""
        hrv_intraday_points = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            hrv_data = self._safe_api_call_intraday('get_hrv_data', date)
            if hrv_data and isinstance(hrv_data, dict):
                # Extract hrvReadings array
                hrv_readings = hrv_data.get('hrvReadings', [])
                logger.info(f"Found {len(hrv_readings)} HRV readings for {date}")

                for entry in hrv_readings:
                    if entry and entry.get('hrvValue') and entry.get('readingTimeGMT'):
                        hrv_intraday_points.append({
                            'date': date,
                            'reading_time': entry['readingTimeGMT'],
                            'hrv_value': entry['hrvValue'],
                            'type': 'hrv_reading'
                        })

        logger.info(f"✓ HRV intraday: {len(hrv_intraday_points)} data points")
        return hrv_intraday_points

    def _extract_respiration_intraday(self, days_back: int) -> List[Dict]:
        """Extract respiration rate intraday data."""
        respiration_points = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            resp_data = self._safe_api_call_intraday('get_respiration_data', date)
            if resp_data and isinstance(resp_data, dict):
                # Extract respirationValuesArray
                resp_values = resp_data.get('respirationValuesArray', [])
                logger.info(f"Found {len(resp_values)} respiration values for {date}")

                for entry in resp_values:
                    if entry and len(entry) >= 2 and entry[1]:
                        respiration_points.append({
                            'date': date,
                            'timestamp': entry[0],
                            'respiration_rate': entry[1],
                            'datetime': datetime.fromtimestamp(entry[0] / 1000).isoformat()
                        })

        logger.info(f"✓ Respiration intraday: {len(respiration_points)} data points")
        return respiration_points

    # COMPONENT 3B: Try problematic APIs with different approaches
    def _attempt_steps_intraday(self, days_back: int) -> List[Dict]:
        """Attempt steps intraday with different error handling."""
        steps_points = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

            # Try the steps API but handle 403 gracefully
            steps_data = self._safe_api_call_intraday('get_steps_data', date)
            if steps_data and isinstance(steps_data, list):
                logger.info(f"Found {len(steps_data)} step entries for {date}")

                for entry in steps_data:
                    if entry and entry.get('steps') is not None and entry.get('startGMT'):
                        steps_points.append({
                            'date': date,
                            'start_time': entry['startGMT'],
                            'end_time': entry.get('endGMT'),
                            'steps_count': entry['steps']
                        })

        logger.info(f"✓ Steps intraday attempt: {len(steps_points)} data points")
        return steps_points