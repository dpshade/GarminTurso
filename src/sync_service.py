"""
Continuous sync service for GarminTurso.
Implements automatic data synchronization similar to garmin-grafana approach.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

from auth import GarminAuthenticator
from database import TursoDatabase
from garmin_collector import GarminCollector

logger = logging.getLogger(__name__)


class GarminSyncService:
    """
    Continuous sync service that automatically fetches new data from Garmin Connect.

    Features:
    - Tracks last sync time in database
    - Compares with Garmin device last sync
    - Fetches only new data since last sync
    - Handles authentication errors and retries
    - Configurable sync intervals
    """

    def __init__(self, db: TursoDatabase, email: str, password: str,
                 sync_interval_seconds: int = 300, rate_limit_seconds: int = 2):
        self.db = db
        self.email = email
        self.password = password
        self.sync_interval_seconds = sync_interval_seconds
        self.rate_limit_seconds = rate_limit_seconds
        self.api = None
        self.collector = None

    def authenticate(self):
        """Authenticate with Garmin Connect."""
        logger.info("Authenticating with Garmin Connect...")
        auth = GarminAuthenticator(self.email, self.password)
        self.api = auth.authenticate()
        self.collector = GarminCollector(self.api, self.db)
        logger.info("Authentication successful")

    def get_garmin_last_sync_time(self) -> datetime:
        """Get the last device sync time from Garmin Connect."""
        if not self.api:
            raise RuntimeError("Not authenticated with Garmin")

        sync_data = self.api.get_device_last_used()
        last_sync_timestamp = sync_data.get('lastUsedDeviceUploadTime')

        if not last_sync_timestamp:
            logger.warning("No device sync timestamp found, using current time")
            return datetime.now()

        # Convert milliseconds to datetime
        return datetime.fromtimestamp(last_sync_timestamp / 1000)

    def get_local_last_sync_time(self) -> Optional[datetime]:
        """Get the last sync time from local database."""
        return self.db.get_last_sync_time()

    def needs_sync(self) -> tuple[bool, Optional[datetime], Optional[datetime]]:
        """
        Check if sync is needed by comparing local and Garmin sync times.

        Returns:
            (needs_sync, local_sync_time, garmin_sync_time)
        """
        try:
            garmin_sync_time = self.get_garmin_last_sync_time()
            local_sync_time = self.get_local_last_sync_time()

            if local_sync_time is None:
                # First time sync - default to last 7 days
                logger.info("No previous sync found, will sync last 7 days")
                return True, None, garmin_sync_time

            needs_sync = local_sync_time < garmin_sync_time

            if needs_sync:
                logger.info(f"Sync needed: Garmin sync time {garmin_sync_time} > local sync time {local_sync_time}")
            else:
                logger.info(f"No sync needed: Local sync time {local_sync_time} >= Garmin sync time {garmin_sync_time}")

            return needs_sync, local_sync_time, garmin_sync_time

        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            return False, None, None

    def sync_data_range(self, start_date: datetime, end_date: datetime) -> bool:
        """
        Sync data for a specific date range.

        Args:
            start_date: Start date for sync
            end_date: End date for sync

        Returns:
            True if sync was successful, False otherwise
        """
        if not self.collector:
            raise RuntimeError("Collector not initialized")

        try:
            logger.info(f"Syncing data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

            current_date = end_date
            while current_date >= start_date:
                date_str = current_date.strftime('%Y-%m-%d')

                try:
                    # Collect data for this date
                    results = self.collector.collect_all_data(days_back=1)

                    # Log the collection
                    log_record = {
                        'collection_type': 'sync',
                        'start_time': datetime.now(),
                        'end_time': datetime.now(),
                        'status': 'success',
                        'records_collected': results.get('collection_stats', {}).get('total_data_points', 0)
                    }
                    self.db.insert_collection_log(log_record)

                    logger.info(f"Successfully synced data for {date_str}")

                    # Rate limiting to respect Garmin's API
                    time.sleep(self.rate_limit_seconds)

                except Exception as e:
                    logger.error(f"Error syncing data for {date_str}: {e}")
                    # Continue with next date instead of failing completely

                current_date -= timedelta(days=1)

            return True

        except Exception as e:
            logger.error(f"Error during data sync: {e}")
            return False

    def run_sync_cycle(self) -> bool:
        """
        Run a single sync cycle.

        Returns:
            True if sync was performed, False if no sync was needed
        """
        try:
            # Check if authentication is needed
            if not self.api:
                self.authenticate()

            # Check if sync is needed
            needs_sync, local_sync_time, garmin_sync_time = self.needs_sync()

            if not needs_sync:
                return False

            # Determine sync date range
            if local_sync_time is None:
                # First sync - get last 7 days
                start_date = datetime.now() - timedelta(days=7)
                end_date = datetime.now()
            else:
                # Incremental sync - from last sync to now
                start_date = local_sync_time
                end_date = garmin_sync_time or datetime.now()

            # Perform the sync
            success = self.sync_data_range(start_date, end_date)

            if success:
                # Update the last sync time
                self.db.update_last_sync_time(garmin_sync_time or datetime.now())
                logger.info(f"Sync completed successfully. Next sync in {self.sync_interval_seconds} seconds")
                return True
            else:
                logger.error("Sync failed")
                return False

        except Exception as e:
            logger.error(f"Error in sync cycle: {e}")
            return False

    def run_continuous_sync(self):
        """
        Run continuous sync loop with configurable intervals.
        """
        logger.info(f"Starting continuous sync service (interval: {self.sync_interval_seconds}s)")

        while True:
            try:
                synced = self.run_sync_cycle()

                if synced:
                    logger.info("Data sync completed")
                else:
                    logger.info("No new data to sync")

            except KeyboardInterrupt:
                logger.info("Sync service stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in sync loop: {e}")

            # Wait for next sync cycle
            logger.info(f"Waiting {self.sync_interval_seconds} seconds until next sync check...")
            time.sleep(self.sync_interval_seconds)

    def run_single_sync(self) -> bool:
        """
        Run a single sync cycle and exit.

        Returns:
            True if sync was successful, False otherwise
        """
        logger.info("Running single sync cycle")

        try:
            synced = self.run_sync_cycle()

            if synced:
                logger.info("Single sync completed successfully")
                return True
            else:
                logger.info("No new data found during single sync")
                return False

        except Exception as e:
            logger.error(f"Error during single sync: {e}")
            return False