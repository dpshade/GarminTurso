"""
Data processing module for chart generation.
Handles database queries and data aggregation for health reports.
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from ..core.database import TursoDatabase

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Processes Garmin data for chart generation.
    Provides aggregated data for various chart types and time windows.
    """

    def __init__(self, db: TursoDatabase):
        self.db = db

    def get_30_day_trend_data(self, metric: str, user_id: int = 1) -> Dict[str, Any]:
        """
        Get 30-day trend data for a specific metric.

        Args:
            metric: The metric to retrieve (rhr, respiratory_rate, sleep_duration, etc.)
            user_id: User ID (defaults to 1)

        Returns:
            Dictionary containing daily values, reference band, and average
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        reference_start = end_date - timedelta(days=180)  # 6-month reference

        try:
            if metric == "resting_heart_rate":
                return self._get_rhr_trend_data(start_date, end_date, reference_start, user_id)
            elif metric == "respiratory_rate":
                return self._get_respiratory_trend_data(start_date, end_date, reference_start, user_id)
            elif metric == "sleep_duration":
                return self._get_sleep_duration_trend_data(start_date, end_date, reference_start, user_id)
            elif metric == "aerobic_activity":
                return self._get_aerobic_activity_trend_data(start_date, end_date, reference_start, user_id)
            else:
                logger.warning(f"Unknown metric: {metric}")
                return {}

        except Exception as e:
            logger.error(f"Error retrieving {metric} trend data: {e}")
            return {}

    def get_180_day_monthly_averages(self, metric: str, user_id: int = 1) -> Dict[str, Any]:
        """
        Get 180-day monthly averages for a specific metric.

        Args:
            metric: The metric to retrieve
            user_id: User ID (defaults to 1)

        Returns:
            Dictionary containing monthly averages and overall average
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=180)

        try:
            if metric == "resting_heart_rate":
                return self._get_rhr_monthly_averages(start_date, end_date, user_id)
            elif metric == "respiratory_rate":
                return self._get_respiratory_monthly_averages(start_date, end_date, user_id)
            elif metric == "sleep_duration":
                return self._get_sleep_monthly_averages(start_date, end_date, user_id)
            elif metric == "aerobic_activity":
                return self._get_aerobic_monthly_averages(start_date, end_date, user_id)
            else:
                logger.warning(f"Unknown metric: {metric}")
                return {}

        except Exception as e:
            logger.error(f"Error retrieving {metric} monthly averages: {e}")
            return {}

    def get_activity_frequency_data(self, user_id: int = 1, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get most frequently logged activities.

        Args:
            user_id: User ID (defaults to 1)
            days_back: Number of days to analyze

        Returns:
            List of activities with frequency counts
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)

        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT
                    activity_type,
                    COUNT(*) as frequency
                FROM activities
                WHERE user_id = ?
                    AND DATE(start_time_local) BETWEEN ? AND ?
                    AND activity_type IS NOT NULL
                GROUP BY activity_type
                ORDER BY frequency DESC
                LIMIT 10
            """, (user_id, str(start_date), str(end_date)))

            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'activity_type': row[0],
                    'frequency': row[1]
                })

            return activities

        except Exception as e:
            logger.error(f"Error retrieving activity frequency data: {e}")
            return []

    def _get_rhr_trend_data(self, start_date, end_date, reference_start, user_id) -> Dict[str, Any]:
        """Get resting heart rate trend data."""
        cursor = self.db.conn.cursor()

        # Get 30-day data
        cursor.execute("""
            SELECT date, resting_heart_rate
            FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
                AND resting_heart_rate IS NOT NULL
            ORDER BY date
        """, (user_id, str(start_date), str(end_date)))

        daily_data = []
        for row in cursor.fetchall():
            daily_data.append({
                'date': row[0],
                'value': row[1]
            })

        # Get 6-month reference data for band
        cursor.execute("""
            SELECT MIN(resting_heart_rate), MAX(resting_heart_rate), AVG(resting_heart_rate)
            FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
                AND resting_heart_rate IS NOT NULL
        """, (user_id, str(reference_start), str(end_date)))

        ref_row = cursor.fetchone()
        reference_min = ref_row[0] if ref_row[0] else 60
        reference_max = ref_row[1] if ref_row[1] else 80

        # Calculate 30-day average
        values = [d['value'] for d in daily_data if d['value'] is not None]
        average = sum(values) / len(values) if values else 0

        return {
            'daily_data': daily_data,
            'reference_band': {'min': reference_min, 'max': reference_max},
            'average': round(average, 1),
            'unit': 'BPM'
        }

    def _get_respiratory_trend_data(self, start_date, end_date, reference_start, user_id) -> Dict[str, Any]:
        """Get respiratory rate trend data."""
        cursor = self.db.conn.cursor()

        # Get 30-day data
        cursor.execute("""
            SELECT date, respiration_avg
            FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
                AND respiration_avg IS NOT NULL
            ORDER BY date
        """, (user_id, str(start_date), str(end_date)))

        daily_data = []
        for row in cursor.fetchall():
            daily_data.append({
                'date': row[0],
                'value': row[1]
            })

        # Get 6-month reference data
        cursor.execute("""
            SELECT MIN(respiration_avg), MAX(respiration_avg), AVG(respiration_avg)
            FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
                AND respiration_avg IS NOT NULL
        """, (user_id, str(reference_start), str(end_date)))

        ref_row = cursor.fetchone()
        reference_min = ref_row[0] if ref_row[0] else 12
        reference_max = ref_row[1] if ref_row[1] else 20

        # Calculate 30-day average
        values = [d['value'] for d in daily_data if d['value'] is not None]
        average = sum(values) / len(values) if values else 0

        return {
            'daily_data': daily_data,
            'reference_band': {'min': reference_min, 'max': reference_max},
            'average': round(average, 1),
            'unit': 'RPM'
        }

    def _get_sleep_duration_trend_data(self, start_date, end_date, reference_start, user_id) -> Dict[str, Any]:
        """Get sleep duration trend data with nap and night sleep."""
        cursor = self.db.conn.cursor()

        # Get 30-day sleep data
        cursor.execute("""
            SELECT
                calendar_date,
                COALESCE(deep_sleep_seconds, 0) + COALESCE(light_sleep_seconds, 0) + COALESCE(rem_sleep_seconds, 0) as night_sleep_seconds
            FROM sleep_data
            WHERE user_id = ? AND calendar_date BETWEEN ? AND ?
            ORDER BY calendar_date
        """, (user_id, str(start_date), str(end_date)))

        daily_data = []
        for row in cursor.fetchall():
            night_hours = row[1] / 3600 if row[1] else 0
            daily_data.append({
                'date': row[0],
                'night_sleep_hours': night_hours,
                'nap_hours': 0  # TODO: Add nap data when available
            })

        # Calculate average
        total_hours = [d['night_sleep_hours'] + d['nap_hours'] for d in daily_data]
        average = sum(total_hours) / len(total_hours) if total_hours else 0

        return {
            'daily_data': daily_data,
            'reference_line': 7.0,  # Recommended 7 hours
            'average': round(average, 2),
            'unit': 'hours'
        }

    def _get_aerobic_activity_trend_data(self, start_date, end_date, reference_start, user_id) -> Dict[str, Any]:
        """Get aerobic activity minutes trend data."""
        cursor = self.db.conn.cursor()

        # Get 30-day activity data
        # Note: This is a simplified version - actual implementation would need
        # to calculate moderate/vigorous minutes from heart rate zones
        cursor.execute("""
            SELECT
                date,
                COALESCE(highly_active_seconds, 0) / 60 as vigorous_minutes,
                COALESCE(active_seconds, 0) / 60 as moderate_minutes
            FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """, (user_id, str(start_date), str(end_date)))

        daily_data = []
        for row in cursor.fetchall():
            daily_data.append({
                'date': row[0],
                'vigorous_minutes': min(row[1], 100),  # Cap for display
                'moderate_minutes': min(row[2], 100)   # Cap for display
            })

        # Calculate average
        total_minutes = [(d['vigorous_minutes'] + d['moderate_minutes']) for d in daily_data]
        average = sum(total_minutes) / len(total_minutes) if total_minutes else 0

        return {
            'daily_data': daily_data,
            'reference_lines': {
                'moderate_weekly': 150,  # 150 min/week moderate
                'vigorous_weekly': 75    # 75 min/week vigorous
            },
            'average': round(average, 1),
            'unit': 'minutes'
        }

    def _get_rhr_monthly_averages(self, start_date, end_date, user_id) -> Dict[str, Any]:
        """Get monthly RHR averages."""
        cursor = self.db.conn.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y-%m', date) as month,
                AVG(resting_heart_rate) as avg_rhr
            FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
                AND resting_heart_rate IS NOT NULL
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """, (user_id, str(start_date), str(end_date)))

        monthly_data = []
        for row in cursor.fetchall():
            monthly_data.append({
                'month': row[0],
                'average': round(row[1], 1)
            })

        # Overall average
        values = [d['average'] for d in monthly_data]
        overall_average = sum(values) / len(values) if values else 0

        return {
            'monthly_data': monthly_data,
            'overall_average': round(overall_average, 1),
            'unit': 'BPM'
        }

    def _get_respiratory_monthly_averages(self, start_date, end_date, user_id) -> Dict[str, Any]:
        """Get monthly respiratory rate averages."""
        cursor = self.db.conn.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y-%m', date) as month,
                AVG(respiration_avg) as avg_respiratory
            FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
                AND respiration_avg IS NOT NULL
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """, (user_id, str(start_date), str(end_date)))

        monthly_data = []
        for row in cursor.fetchall():
            monthly_data.append({
                'month': row[0],
                'average': round(row[1], 1)
            })

        # Overall average
        values = [d['average'] for d in monthly_data]
        overall_average = sum(values) / len(values) if values else 0

        return {
            'monthly_data': monthly_data,
            'overall_average': round(overall_average, 1),
            'unit': 'RPM'
        }

    def _get_sleep_monthly_averages(self, start_date, end_date, user_id) -> Dict[str, Any]:
        """Get monthly sleep duration averages."""
        cursor = self.db.conn.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y-%m', calendar_date) as month,
                AVG((COALESCE(deep_sleep_seconds, 0) + COALESCE(light_sleep_seconds, 0) + COALESCE(rem_sleep_seconds, 0)) / 3600.0) as avg_sleep_hours
            FROM sleep_data
            WHERE user_id = ? AND calendar_date BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m', calendar_date)
            ORDER BY month
        """, (user_id, str(start_date), str(end_date)))

        monthly_data = []
        for row in cursor.fetchall():
            monthly_data.append({
                'month': row[0],
                'average': round(row[1], 1)
            })

        # Overall average
        values = [d['average'] for d in monthly_data]
        overall_average = sum(values) / len(values) if values else 0

        return {
            'monthly_data': monthly_data,
            'overall_average': round(overall_average, 1),
            'recommended': 7.0,
            'unit': 'hours'
        }

    def _get_aerobic_monthly_averages(self, start_date, end_date, user_id) -> Dict[str, Any]:
        """Get monthly aerobic activity averages."""
        cursor = self.db.conn.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y-%m', date) as month,
                AVG((COALESCE(highly_active_seconds, 0) + COALESCE(active_seconds, 0)) / 60.0) as avg_activity_minutes
            FROM daily_stats
            WHERE user_id = ? AND date BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """, (user_id, str(start_date), str(end_date)))

        monthly_data = []
        for row in cursor.fetchall():
            monthly_data.append({
                'month': row[0],
                'average': round(row[1], 1)
            })

        # Overall average
        values = [d['average'] for d in monthly_data]
        overall_average = sum(values) / len(values) if values else 0

        return {
            'monthly_data': monthly_data,
            'overall_average': round(overall_average, 1),
            'unit': 'minutes'
        }