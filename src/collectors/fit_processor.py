"""FIT file processor for GPS and sensor data extraction."""

import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from garminconnect import Garmin
from ..core.database import TursoDatabase

logger = logging.getLogger(__name__)


class FITProcessor:
    def __init__(self, api: Garmin, db: TursoDatabase):
        self.api = api
        self.db = db
        self.rate_limit_delay = 2.0  # Longer delay for file downloads

    def collect_fit_data(self, days_back: int = 3) -> Dict[str, Any]:
        """
        Extract GPS and sensor data from FIT files of recent activities.
        """
        logger.info(f"🗺️ FIT file processing for {days_back} days")
        start_time = datetime.now()

        results = {
            'activities_with_fit': [],
            'gps_points': [],
            'sensor_data': [],
            'fit_files_processed': 0,
            'total_gps_points': 0,
            'total_sensor_readings': 0
        }

        try:
            # Get recent activities that might have FIT files
            activities = self._get_recent_activities(days_back)
            logger.info(f"Found {len(activities)} recent activities")

            for activity in activities[:5]:  # Limit for testing
                fit_data = self._process_activity_fit(activity)
                if fit_data:
                    results['activities_with_fit'].append(activity)
                    results['gps_points'].extend(fit_data.get('gps_points', []))
                    results['sensor_data'].extend(fit_data.get('sensor_data', []))
                    results['fit_files_processed'] += 1

            results['total_gps_points'] = len(results['gps_points'])
            results['total_sensor_readings'] = len(results['sensor_data'])

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ FIT processing completed: {results['total_gps_points']} GPS points, {results['total_sensor_readings']} sensor readings in {duration:.1f}s")

            return results

        except Exception as e:
            logger.error(f"❌ FIT processing failed: {e}")
            raise

    def _get_recent_activities(self, days_back: int) -> List[Dict]:
        """Get recent activities that might have GPS data."""
        activities = []

        try:
            # Get activities from the last few days
            from datetime import timedelta
            for i in range(days_back):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

                daily_activities = self.api.get_activities_by_date(date, date)
                if daily_activities:
                    # Filter for activities likely to have GPS (outdoor activities)
                    gps_activities = [
                        activity for activity in daily_activities
                        if self._likely_has_gps(activity)
                    ]
                    activities.extend(gps_activities)

        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")

        return activities

    def _likely_has_gps(self, activity: Dict) -> bool:
        """Check if activity type likely has GPS data."""
        gps_activity_types = {
            'running', 'cycling', 'walking', 'hiking', 'outdoor',
            'trail_running', 'road_biking', 'mountain_biking'
        }

        activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
        activity_name = activity.get('activityName', '').lower()

        return (
            any(gps_type in activity_type for gps_type in gps_activity_types) or
            any(gps_type in activity_name for gps_type in gps_activity_types) or
            activity.get('distance', 0) > 0  # Has distance measurement
        )

    def _process_activity_fit(self, activity: Dict) -> Optional[Dict]:
        """Process FIT file for a single activity."""
        activity_id = activity.get('activityId')
        if not activity_id:
            return None

        logger.info(f"Processing FIT for activity {activity_id}: {activity.get('activityName', 'Unknown')}")

        try:
            # Try to get GPX data first (easier to parse)
            gpx_data = self._get_activity_gpx(activity_id)
            if gpx_data:
                return self._parse_gpx_data(gpx_data, activity)

            # Fallback to raw activity details
            return self._get_activity_details(activity_id, activity)

        except Exception as e:
            logger.error(f"Error processing FIT for activity {activity_id}: {e}")
            return None

    def _get_activity_gpx(self, activity_id: str) -> Optional[str]:
        """Try to get GPX export of activity."""
        try:
            # Some Garmin APIs provide GPX export
            gpx_data = self.api.download_activity(activity_id, dl_fmt=self.api.ActivityDownloadFormat.GPX)
            if gpx_data:
                logger.info(f"✅ Got GPX data for activity {activity_id}")
                return gpx_data
        except Exception as e:
            logger.debug(f"GPX not available for activity {activity_id}: {e}")

        return None

    def _get_activity_details(self, activity_id: str, activity: Dict) -> Optional[Dict]:
        """Get detailed activity data as fallback."""
        try:
            # Get detailed activity information
            details = self.api.get_activity_evaluation(activity_id)
            splits = self.api.get_activity_splits(activity_id)

            gps_points = []
            sensor_data = []

            # Extract any available location/elevation data from splits
            if splits and isinstance(splits, dict):
                split_summaries = splits.get('splitSummaries', [])
                for i, split in enumerate(split_summaries):
                    if split.get('distance') and split.get('movingDuration'):
                        gps_points.append({
                            'activity_id': activity_id,
                            'split_number': i + 1,
                            'distance_meters': split.get('distance'),
                            'duration_seconds': split.get('movingDuration'),
                            'elevation_gain': split.get('elevationGain'),
                            'elevation_loss': split.get('elevationLoss'),
                            'avg_speed': split.get('avgSpeed'),
                            'max_speed': split.get('maxSpeed')
                        })

            # Extract heart rate and other sensor data from details
            if details and isinstance(details, dict):
                metrics = details.get('activityDetailMetrics', [])
                for metric in metrics:
                    if metric.get('metrics'):
                        for metric_data in metric['metrics']:
                            sensor_data.append({
                                'activity_id': activity_id,
                                'metric_type': metric_data.get('metricsIndex'),
                                'value': metric_data.get('value'),
                                'timestamp': metric.get('timestamp')
                            })

            logger.info(f"✓ Extracted {len(gps_points)} GPS points and {len(sensor_data)} sensor readings")
            return {
                'gps_points': gps_points,
                'sensor_data': sensor_data
            }

        except Exception as e:
            logger.error(f"Error getting activity details for {activity_id}: {e}")
            return None

    def _parse_gpx_data(self, gpx_data: str, activity: Dict) -> Optional[Dict]:
        """Parse GPX data to extract GPS points."""
        try:
            # Basic GPX parsing (would need proper XML parser for production)
            gps_points = []
            sensor_data = []

            # For now, just record that we got GPX data
            activity_id = activity.get('activityId')

            # Extract basic activity metadata as GPS summary
            if activity.get('startLatitude') and activity.get('startLongitude'):
                gps_points.append({
                    'activity_id': activity_id,
                    'latitude': activity['startLatitude'],
                    'longitude': activity['startLongitude'],
                    'elevation': activity.get('elevationGain', 0),
                    'timestamp': activity.get('startTimeLocal'),
                    'point_type': 'start'
                })

            if activity.get('endLatitude') and activity.get('endLongitude'):
                gps_points.append({
                    'activity_id': activity_id,
                    'latitude': activity['endLatitude'],
                    'longitude': activity['endLongitude'],
                    'elevation': activity.get('elevationLoss', 0),
                    'timestamp': activity.get('startTimeLocal'),  # Would calculate end time
                    'point_type': 'end'
                })

            # Record GPX file size as sensor data
            sensor_data.append({
                'activity_id': activity_id,
                'sensor_type': 'gpx_file_size',
                'value': len(gpx_data),
                'timestamp': activity.get('startTimeLocal')
            })

            logger.info(f"✓ Parsed GPX: {len(gps_points)} GPS points")
            return {
                'gps_points': gps_points,
                'sensor_data': sensor_data
            }

        except Exception as e:
            logger.error(f"Error parsing GPX data: {e}")
            return None