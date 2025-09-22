"""Garmin Connect authentication module using production-tested garmin_login approach."""

import os
import sys
import logging
import requests
from pathlib import Path
from typing import Optional
from garminconnect import Garmin, GarminConnectAuthenticationError
from garth.exc import GarthHTTPError

logger = logging.getLogger(__name__)


class GarminAuthenticator:
    def __init__(self, email: str, password: str, token_dir: str = "~/.garminconnect", is_cn: bool = False):
        self.email = email
        self.password = password
        self.token_dir = Path(token_dir).expanduser()
        self.is_cn = is_cn
        self.api: Optional[Garmin] = None

    def authenticate(self) -> Garmin:
        """
        Authenticate using production-tested garmin_login approach.
        Returns authenticated Garmin API client.
        """
        return self.garmin_login()

    def garmin_login(self) -> Garmin:
        """
        Production-tested login approach from garmin-grafana and similar projects.
        """
        try:
            logger.info(f"Trying to login to Garmin Connect using token data from directory '{self.token_dir}'...")
            garmin = Garmin()
            garmin.login(str(self.token_dir))
            logger.info("Login to Garmin Connect successful using stored session tokens.")

        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
            logger.warning("Session is expired or login information not present/incorrect. You'll need to log in again...")
            logger.info("Login with your Garmin Connect credentials to generate them.")

            try:
                user_email = self.email or input("Enter Garmin Connect Login e-mail: ")
                user_password = self.password or input("Enter Garmin Connect password (characters will be visible): ")

                garmin = Garmin(
                    email=user_email,
                    password=user_password,
                    is_cn=self.is_cn,
                    return_on_mfa=True
                )

                result1, result2 = garmin.login()

                if result1 == "needs_mfa":  # MFA is required
                    mfa_code = input("MFA one-time code (via email or SMS): ")
                    garmin.resume_login(result2, mfa_code)

                # Ensure token directory exists
                self.token_dir.mkdir(parents=True, exist_ok=True)

                # Save tokens for future use
                garmin.garth.dump(str(self.token_dir))
                logger.info(f"OAuth tokens stored in '{self.token_dir}' directory for future use")

                # Set secure permissions on token directory
                os.chmod(self.token_dir, 0o700)
                for token_file in self.token_dir.glob("*"):
                    os.chmod(token_file, 0o600)

                # Re-login using stored tokens to verify
                garmin.login(str(self.token_dir))
                logger.info("Login to Garmin Connect successful using stored session tokens.")
                logger.info("Saved logins will be used automatically for future sessions.")

            except (
                FileNotFoundError,
                GarthHTTPError,
                GarminConnectAuthenticationError,
                requests.exceptions.HTTPError,
            ) as err:
                logger.error(f"Authentication error: {str(err)}")
                raise Exception("Session is expired: please login again and restart the script")

        # Verify API access
        try:
            user_profile = garmin.get_full_name()
            logger.info(f"✓ Connected as: {user_profile}")
        except Exception as e:
            logger.warning(f"Could not get user profile: {e}")
            logger.info("✓ Authenticated (profile verification skipped)")

        self.api = garmin
        return garmin

    def logout(self):
        """Clear stored authentication tokens."""
        try:
            if self.token_dir.exists():
                for token_file in self.token_dir.glob("*"):
                    token_file.unlink()
                logger.info("✓ Cleared authentication tokens")
        except Exception as e:
            logger.error(f"Error clearing tokens: {e}")

    def is_authenticated(self) -> bool:
        """Check if we have valid authentication."""
        try:
            garmin = Garmin()
            garmin.login(str(self.token_dir))
            return True
        except:
            return False