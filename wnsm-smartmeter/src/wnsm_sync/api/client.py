"""WN Smart Meter API Client using OAuth2 client credentials."""

import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

import requests

from . import constants as const
from .errors import AuthenticationError, MeteringPointNotFoundError, WNSMApiError

logger = logging.getLogger(__name__)


class WNSMApiClient:
    """Client for the official Wiener Netze Smart Meter REST API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        api_key: str,
        use_mock: bool = False,
        timeout: int = 60,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = api_key
        self.use_mock = use_mock
        self.timeout = timeout
        self._access_token: Optional[str] = None
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> None:
        """Obtain an OAuth2 access token via client credentials flow."""
        logger.info("Authenticating with WN Smart Meter API")
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": const.TOKEN_SCOPE,
        }
        try:
            response = self._session.post(
                const.TOKEN_URL,
                data=data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data.get("access_token")
            if not self._access_token:
                raise AuthenticationError("No access_token in token response")
            logger.info("Authentication successful")
        except requests.HTTPError as exc:
            raise AuthenticationError(
                f"Authentication failed: {exc}", code=exc.response.status_code
            ) from exc
        except requests.RequestException as exc:
            raise AuthenticationError(f"Authentication request failed: {exc}") from exc

    def is_authenticated(self) -> bool:
        """Return True if an access token is available."""
        return self._access_token is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "x-Gateway-APIKey": self.api_key,
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an authenticated API request, refreshing token on 401."""
        if not self.is_authenticated():
            self.authenticate()

        url = f"{const.BASE_URL}/{path.lstrip('/')}"
        response = self._session.request(
            method,
            url,
            headers=self._get_headers(),
            params=params,
            timeout=self.timeout,
        )

        if response.status_code == 401:
            logger.info("Token expired, re-authenticating")
            self.authenticate()
            response = self._session.request(
                method,
                url,
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout,
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise WNSMApiError(
                f"API request failed: {exc}", code=exc.response.status_code
            ) from exc

        return response.json()

    # ------------------------------------------------------------------
    # API methods
    # ------------------------------------------------------------------

    def get_metering_points(self) -> List[Dict[str, Any]]:
        """Return all metering points (Zählpunkte) for the authenticated account."""
        logger.info("Fetching metering points")
        return self._request("GET", "zaehlpunkte")

    def get_consumption(
        self,
        zaehlpunkt: str,
        date_from: date,
        date_to: date,
        wertetyp: str = const.DEFAULT_WERTETYP,
    ) -> Dict[str, Any]:
        """Fetch consumption data for a metering point.

        Args:
            zaehlpunkt: The metering point identifier (Zählpunktnummer).
            date_from: Start date (inclusive).
            date_to: End date (inclusive).
            wertetyp: Resolution type, e.g. "QUARTER_HOUR" or "DAY".

        Returns:
            Raw API response dict.
        """
        if self.use_mock:
            return self._mock_consumption(zaehlpunkt, date_from, date_to)

        params = {
            "datumVon": date_from.isoformat(),
            "datumBis": date_to.isoformat(),
            "wertetyp": wertetyp,
        }
        logger.info(
            "Fetching consumption for %s from %s to %s (wertetyp=%s)",
            zaehlpunkt,
            date_from,
            date_to,
            wertetyp,
        )
        return self._request("GET", f"zaehlpunkte/{zaehlpunkt}/messwerte", params=params)

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------

    def _mock_consumption(
        self, zaehlpunkt: str, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """Return mock consumption data for testing."""
        import random
        from datetime import timedelta, timezone

        logger.info("Returning MOCK consumption data")
        messwerte = []
        current = datetime.combine(date_from, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        end = datetime.combine(date_to, datetime.min.time()).replace(
            tzinfo=timezone.utc
        ) + timedelta(days=1)

        while current < end:
            messwerte.append(
                {
                    "zeitVon": current.isoformat(),
                    "zeitBis": (current + timedelta(minutes=15)).isoformat(),
                    "messwert": round(random.uniform(50, 500), 1),
                    "qualitaet": "VAL",
                }
            )
            current += timedelta(minutes=15)

        return {
            "zaehlpunkt": zaehlpunkt,
            "zaehlwerke": [
                {
                    "obisCode": "1-1:1.9.0",
                    "messwerte": messwerte,
                }
            ],
        }
