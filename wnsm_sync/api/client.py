"""Contains the Smartmeter API Client."""
import json
import logging
from datetime import datetime, timedelta, date
from urllib import parse
from typing import List, Dict, Any, Tuple, Optional

import requests
from dateutil.relativedelta import relativedelta
from lxml import html

from . import constants as const
from .errors import (
    SmartmeterConnectionError,
    SmartmeterLoginError,
    SmartmeterQueryError,
)

logger = logging.getLogger(__name__)


class Smartmeter:
    """Smartmeter client for accessing the API."""

    def __init__(self, username: str, password: str):
        """Initialize the Smartmeter API client.

        Args:
            username (str): Username used for API login.
            password (str): Password used for API login.
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._access_token = None
        self._refresh_token = None
        self._api_gateway_token = None
        self._access_token_expiration = None
        self._refresh_token_expiration = None
        self._api_gateway_b2b_token = None

    def reset(self):
        """Reset the session and tokens."""
        self.session = requests.Session()
        self._access_token = None
        self._refresh_token = None
        self._api_gateway_token = None
        self._access_token_expiration = None
        self._refresh_token_expiration = None
        self._api_gateway_b2b_token = None

    def is_login_expired(self) -> bool:
        """Check if the login has expired.
        
        Returns:
            bool: True if access token has expired, False otherwise.
        """
        return self._access_token_expiration is not None and datetime.now() >= self._access_token_expiration

    def is_logged_in(self) -> bool:
        """Check if the client is currently logged in.
        
        Returns:
            bool: True if logged in with a valid token, False otherwise.
        """
        return self._access_token is not None and not self.is_login_expired()

    def load_login_page(self) -> str:
        """Load the login page and extract the encoded login URL.
        
        Returns:
            str: The extracted login action URL.
            
        Raises:
            SmartmeterConnectionError: If loading the login page fails.
        """
        login_url = const.AUTH_URL + "auth?" + parse.urlencode(const.LOGIN_ARGS)
        try:
            result = self.session.get(login_url)
        except Exception as exception:
            raise SmartmeterConnectionError("Could not load login page") from exception
        
        if result.status_code != 200:
            raise SmartmeterConnectionError(
                f"Could not load login page. HTTP status: {result.status_code}"
            )
        
        try:
            tree = html.fromstring(result.content)
            action = tree.xpath("(//form/@action)")[0]
            return action
        except (IndexError, ValueError) as exception:
            raise SmartmeterConnectionError("Could not extract login form action URL") from exception

    def credentials_login(self, url: str) -> str:
        """Login with credentials using the provided login URL.
        
        Args:
            url (str): The login form action URL.
            
        Returns:
            str: The authorization code from the redirect.
            
        Raises:
            SmartmeterConnectionError: If connection fails.
            SmartmeterLoginError: If login fails.
        """
        try:
            # First step: Submit username
            result = self.session.post(
                url,
                data={"username": self.username, "login": " "},
                allow_redirects=False,
            )

            if result.status_code not in [200, 302]:
                raise SmartmeterLoginError(f"Initial login step failed with status {result.status_code}")

            # Extract form data for password submission
            tree = html.fromstring(result.content)
            form_inputs = tree.xpath("//form//input[@name]")
            
            # Build form data dynamically
            form_data = {el.attrib['name']: el.attrib.get('value', '') for el in form_inputs}
            if 'username' in form_data:
                form_data['username'] = self.username
            if 'password' in form_data:
                form_data['password'] = self.password
                
            # Extract the form action URL
            action = tree.xpath("(//form/@action)")
            if not action:
                raise SmartmeterLoginError("Could not find password form action URL")
                
            # Submit password form
            result = self.session.post(
                action[0],
                data=form_data,
                allow_redirects=False,
            )

        except Exception as exception:
            logger.error("Login error: %s", str(exception))
            raise SmartmeterConnectionError("Could not login with credentials") from exception

        if "Location" not in result.headers:
            raise SmartmeterLoginError("Login failed. Check username/password.")
            
        location = result.headers["Location"]
        parsed_url = parse.urlparse(location)

        try:
            fragment_dict = dict(
                [
                    x.split("=")
                    for x in parsed_url.fragment.split("&")
                    if len(x.split("=")) == 2
                ]
            )
            
            if "code" not in fragment_dict:
                raise SmartmeterLoginError("Login failed. Authorization code not found in redirect URL.")
                
            return fragment_dict["code"]
            
        except Exception as exception:
            raise SmartmeterLoginError(
                "Failed to extract authorization code from redirect."
            ) from exception

    def load_tokens(self, code: str) -> dict:
        """Load access and refresh tokens using the authorization code.
        
        Args:
            code (str): The authorization code from the login process.
            
        Returns:
            dict: The token response containing access_token, refresh_token, etc.
            
        Raises:
            SmartmeterConnectionError: If obtaining the token fails.
            SmartmeterLoginError: If the token is invalid.
        """
        try:
            result = self.session.post(
                const.AUTH_URL + "token",
                data=const.build_access_token_args(code=code),
            )
        except Exception as exception:
            raise SmartmeterConnectionError("Could not obtain access token") from exception

        if result.status_code != 200:
            raise SmartmeterConnectionError(
                f"Could not obtain access token. Status code: {result.status_code}"
            )
            
        try:
            tokens = result.json()
        except ValueError as exception:
            raise SmartmeterConnectionError("Could not parse token response") from exception
            
        if tokens.get("token_type") != "Bearer":
            raise SmartmeterLoginError(f"Invalid token type: {tokens.get('token_type')}")
            
        return tokens

    def login(self):
        """Perform the login process with credentials specified in constructor.
        
        Returns:
            Smartmeter: The client instance for chaining.
            
        Raises:
            SmartmeterLoginError: If login fails.
        """
        if self.is_login_expired():
            logger.debug("Access token expired, resetting session")
            self.reset()
            
        if not self.is_logged_in():
            logger.debug("Not logged in, starting login process")
            try:
                url = self.load_login_page()
                code = self.credentials_login(url)
                tokens = self.load_tokens(code)
                
                self._access_token = tokens["access_token"]
                self._refresh_token = tokens["refresh_token"]
                now = datetime.now()
                self._access_token_expiration = now + timedelta(seconds=tokens["expires_in"])
                self._refresh_token_expiration = now + timedelta(
                    seconds=tokens["refresh_expires_in"]
                )

                logger.debug("Access Token valid until %s", self._access_token_expiration)

                self._api_gateway_token, self._api_gateway_b2b_token = self._get_api_key(
                    self._access_token
                )
                
            except (SmartmeterConnectionError, SmartmeterLoginError) as error:
                logger.error("Login failed: %s", str(error))
                raise
                
        return self

    def _access_valid_or_raise(self):
        """Check if the access token is still valid or raise an exception.
        
        Raises:
            SmartmeterConnectionError: If access token is expired.
        """
        if self._access_token is None:
            raise SmartmeterConnectionError("No access token available, please login first")
            
        if datetime.now() >= self._access_token_expiration:
            raise SmartmeterConnectionError("Access Token expired, please login again")

    def _get_api_key(self, token: str) -> Tuple[str, str]:
        """Get API keys using the provided access token.
        
        Args:
            token (str): The access token.
            
        Returns:
            Tuple[str, str]: The b2c and b2b API keys.
            
        Raises:
            SmartmeterConnectionError: If obtaining API keys fails.
        """
        self._access_valid_or_raise()

        headers = {"Authorization": f"Bearer {token}"}
        try:
            result = self.session.get(const.API_CONFIG_URL, headers=headers)
            result.raise_for_status()
            config_data = result.json()
        except Exception as exception:
            raise SmartmeterConnectionError("Could not obtain API key") from exception

        # Check for required keys
        find_keys = ["b2cApiKey", "b2bApiKey"]
        for key in find_keys:
            if key not in config_data:
                raise SmartmeterConnectionError(f"{key} not found in API config response")

        # Update API URLs if changed in the response
        if "b2cApiUrl" in config_data and config_data["b2cApiUrl"] != const.API_URL:
            const.API_URL = config_data["b2cApiUrl"]
            logger.warning("The b2cApiUrl has changed to %s", const.API_URL)
            
        if "b2bApiUrl" in config_data and config_data["b2bApiUrl"] != const.API_URL_B2B:
            const.API_URL_B2B = config_data["b2bApiUrl"]
            logger.warning("The b2bApiUrl has changed to %s", const.API_URL_B2B)

        return (config_data[key] for key in find_keys)

    def export_session(self) -> dict:
        """Export reusable session state for external scripts.
        
        Returns:
            dict: Dictionary containing session state data.
        """
        return {
            "cookies": requests.utils.dict_from_cookiejar(self.session.cookies),
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "api_gateway_token": self._api_gateway_token,
            "access_token_expiration": self._access_token_expiration.isoformat() if self._access_token_expiration else None,
            "refresh_token_expiration": self._refresh_token_expiration.isoformat() if self._refresh_token_expiration else None,
            "api_gateway_b2b_token": self._api_gateway_b2b_token,
        }

    def restore_session(self, session_data: dict):
        """Restore previously exported session.
        
        Args:
            session_data (dict): Session data from export_session.
        """
        try:
            self.session.cookies = requests.utils.cookiejar_from_dict(session_data["cookies"])
            self._access_token = session_data["access_token"]
            self._refresh_token = session_data["refresh_token"]
            self._api_gateway_token = session_data["api_gateway_token"]
            self._api_gateway_b2b_token = session_data["api_gateway_b2b_token"]
            
            if session_data["access_token_expiration"]:
                self._access_token_expiration = datetime.fromisoformat(session_data["access_token_expiration"])
            else:
                self._access_token_expiration = None
                
            if session_data["refresh_token_expiration"]:
                self._refresh_token_expiration = datetime.fromisoformat(session_data["refresh_token_expiration"])
            else:
                self._refresh_token_expiration = None
                
        except (KeyError, ValueError) as exception:
            logger.warning("Failed to restore session: %s", str(exception))
            self.reset()

    @staticmethod
    def _dt_string(datetime_obj: datetime) -> str:
        """Convert datetime to API date format string.
        
        Args:
            datetime_obj (datetime): The datetime object to convert.
            
        Returns:
            str: Formatted datetime string.
        """
        return datetime_obj.strftime(const.API_DATE_FORMAT)[:-3] + "Z"

    def _call_api(
        self,
        endpoint: str,
        base_url: str = None,
        method: str = "GET",
        data: dict = None,
        query: dict = None,
        return_response: bool = False,
        timeout: float = 60.0,
        extra_headers: dict = None,
    ):
        """Make an API call to the specified endpoint.
        
        Args:
            endpoint (str): API endpoint to call.
            base_url (str, optional): Base URL. Defaults to API_URL.
            method (str, optional): HTTP method. Defaults to "GET".
            data (dict, optional): Request body data. Defaults to None.
            query (dict, optional): Query parameters. Defaults to None.
            return_response (bool, optional): Return response object instead of JSON. Defaults to False.
            timeout (float, optional): Request timeout. Defaults to 60.0.
            extra_headers (dict, optional): Additional headers. Defaults to None.
            
        Returns:
            dict or Response: API response as JSON or Response object.
            
        Raises:
            SmartmeterConnectionError: If connection fails or token is invalid.
        """
        self._access_valid_or_raise()

        if base_url is None:
            base_url = const.API_URL
        url = parse.urljoin(base_url, endpoint)

        if query:
            url += ("?" if "?" not in endpoint else "&") + parse.urlencode(query)

        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }

        # Add appropriate API key based on the URL
        if base_url == const.API_URL:
            headers["X-Gateway-APIKey"] = self._api_gateway_token
        elif base_url == const.API_URL_B2B:
            headers["X-Gateway-APIKey"] = self._api_gateway_b2b_token

        if extra_headers:
            headers.update(extra_headers)

        if data:
            headers["Content-Type"] = "application/json"

        try:
            response = self.session.request(
                method, url, headers=headers, json=data, timeout=timeout
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exception:
            status_code = getattr(exception.response, "status_code", None)
            content = getattr(exception.response, "content", b"").decode("utf-8", errors="ignore")
            raise SmartmeterConnectionError(
                f"API request failed: {url} - Status: {status_code}, Error: {content}"
            ) from exception

        if return_response:
            return response

        try:
            return response.json()
        except ValueError as exception:
            raise SmartmeterConnectionError(f"Failed to parse API response as JSON: {response.content}") from exception

    def get_zaehlpunkt(self, zaehlpunkt: str = None) -> Tuple[str, str, const.AnlagenType]:
        """Get zaehlpunkt details.
        
        Args:
            zaehlpunkt (str, optional): Zaehlpunkt number. Defaults to None.
            
        Returns:
            Tuple[str, str, const.AnlagenType]: Customer ID, Zaehlpunkt number, and AnlagenType.
            
        Raises:
            SmartmeterQueryError: If zaehlpunkt not found.
        """
        contracts = self.zaehlpunkte()
        
        if not contracts:
            raise SmartmeterQueryError("No contracts found")
        
        if zaehlpunkt is None:
            # Get first zaehlpunkt if none specified
            try:
                customer_id = contracts[0]["geschaeftspartner"]
                zp = contracts[0]["zaehlpunkte"][0]["zaehlpunktnummer"]
                anlagetype = contracts[0]["zaehlpunkte"][0]["anlage"]["typ"]
            except (IndexError, KeyError) as exception:
                raise SmartmeterQueryError("First zaehlpunkt data structure invalid") from exception
        else:
            # Find specified zaehlpunkt
            customer_id = zp = anlagetype = None
            for contract in contracts:
                zp_details = [z for z in contract["zaehlpunkte"] if z["zaehlpunktnummer"] == zaehlpunkt]
                if len(zp_details) > 0:
                    anlagetype = zp_details[0]["anlage"]["typ"]
                    zp = zp_details[0]["zaehlpunktnummer"]
                    customer_id = contract["geschaeftspartner"]
                    break
            
            if customer_id is None:
                raise SmartmeterQueryError(f"Zaehlpunkt {zaehlpunkt} not found")
                
        return customer_id, zp, const.AnlagenType.from_str(anlagetype)

    def zaehlpunkte(self) -> list:
        """Get zaehlpunkte for the currently logged in user.
        
        Returns:
            list: List of zaehlpunkte data.
        """
        return self._call_api("zaehlpunkte")

    def consumptions(self) -> dict:
        """Get energy consumption data.
        
        Returns:
            dict: Consumption data from API.
        """
        return self._call_api("zaehlpunkt/consumptions")

    def base_information(self) -> dict:
        """Get base information about the meter.
        
        Returns:
            dict: Base information data from API.
        """
        return self._call_api("zaehlpunkt/baseInformation")

    def meter_readings(self) -> dict:
        """Get meter readings data.
        
        Returns:
            dict: Meter readings data from API.
        """
        return self._call_api("zaehlpunkt/meterReadings")

    def verbrauch(
        self,
        customer_id: str = None,
        zaehlpunkt: str = None,
        date_from: datetime = None,
        resolution: const.Resolution = const.Resolution.HOUR
    ) -> dict:
        """Get energy usage data with hourly or quarter-hour resolution.
        
        This returns consumptions for a single day (24 hours after date_from).

        Args:
            customer_id (str, optional): Customer ID. Defaults to None.
            zaehlpunkt (str, optional): Zaehlpunkt ID. Defaults to None.
            date_from (datetime, optional): Start date. Defaults to None (current day).
            resolution (const.Resolution, optional): Time resolution. Defaults to HOUR.
            
        Returns:
            dict: Energy usage data.
        """
        if date_from is None:
            date_from = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
        if zaehlpunkt is None or customer_id is None:
            customer_id, zaehlpunkt, anlagetype = self.get_zaehlpunkt()
            
        endpoint = f"messdaten/{customer_id}/{zaehlpunkt}/verbrauch"
        query = const.build_verbrauchs_args(
            dateFrom=self._dt_string(date_from),
            dayViewResolution=resolution.value
        )
        return self._call_api(endpoint, query=query)

    def verbrauchRaw(
        self,
        customer_id: str = None,
        zaehlpunkt: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
    ) -> dict:
        """Get daily energy usage data for a longer period.
        
        This can be used to query consumption for months or weeks.
        Minimal resolution is a single day.

        Args:
            customer_id (str, optional): Customer ID. Defaults to None.
            zaehlpunkt (str, optional): Zaehlpunkt ID. Defaults to None.
            date_from (datetime, optional): Start date. Defaults to None (three months ago).
            date_to (datetime, optional): End date. Defaults to None (current date).
            
        Returns:
            dict: Energy usage data.
        """
        if date_to is None:
            date_to = datetime.now()
        
        if date_from is None:
            date_from = date_to - relativedelta(months=3)
            
        if zaehlpunkt is None or customer_id is None:
            customer_id, zaehlpunkt, anlagetype = self.get_zaehlpunkt()
            
        endpoint = f"messdaten/{customer_id}/{zaehlpunkt}/verbrauchRaw"
        query = {
            "dateFrom": self._dt_string(date_from),
            "dateTo": self._dt_string(date_to),
            "granularity": "DAY",
        }
        return self._call_api(endpoint, query=query)

    def profil(self) -> dict:
        """Get profile of the logged-in user.
        
        Returns:
            dict: User profile data.
        """
        return self._call_api("user/profile", const.API_URL_ALT)

    def find_valid_obis_data(self, zaehlwerke: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find and validate data with valid OBIS codes.
        
        Args:
            zaehlwerke (List[Dict[str, Any]]): List of zaehlwerke data.
            
        Returns:
            Dict[str, Any]: First valid zaehlwerk data.
            
        Raises:
            SmartmeterQueryError: If no valid OBIS codes found.
        """
        if not zaehlwerke:
            raise SmartmeterQueryError("Empty zaehlwerke data provided")
        
        # Check if any OBIS codes exist
        all_obis_codes = [zaehlwerk.get("obisCode") for zaehlwerk in zaehlwerke]
        if not any(all_obis_codes):
            logger.debug("Returned zaehlwerke: %s", zaehlwerke)
            raise SmartmeterQueryError("No OBIS codes found in the provided data")
        
        # Filter data for valid OBIS codes
        valid_data = [
            zaehlwerk for zaehlwerk in zaehlwerke
            if zaehlwerk.get("obisCode") in const.VALID_OBIS_CODES
        ]
        
        if not valid_data:
            logger.debug("Returned zaehlwerke: %s", zaehlwerke)
            raise SmartmeterQueryError(
                f"No valid OBIS code found. OBIS codes in data: {all_obis_codes}"
            )
        
        # Check for empty or missing messwerte
        for zaehlwerk in valid_data:
            if not zaehlwerk.get("messwerte"):
                obis = zaehlwerk.get("obisCode")
                logger.debug(
                    "Valid OBIS code '%s' has empty or missing messwerte. "
                    "Data is probably not available yet.", obis
                )
                
        # Log a warning if multiple valid OBIS codes are found        
        if len(valid_data) > 1:
            found_valid_obis = [zaehlwerk["obisCode"] for zaehlwerk in valid_data]
            logger.warning(
                "Multiple valid OBIS codes found: %s. Using the first one.",
                found_valid_obis
            )

        return valid_data[0]

    def historical_data(
        self,
        zaehlpunktnummer: str = None,
        date_from: date = None,
        date_until: date = None,
        valuetype: const.ValueType = const.ValueType.METER_READ
    ) -> Dict[str, Any]:
        """Query historical data in batch.
        
        Args:
            zaehlpunktnummer (str, optional): Zaehlpunkt number. Defaults to None.
            date_from (date, optional): Start date. Defaults to None (3 years ago).
            date_until (date, optional): End date. Defaults to None (today).
            valuetype (const.ValueType, optional): Value type. Defaults to METER_READ.
            
        Returns:
            Dict[str, Any]: Valid OBIS data.
            
        Raises:
            SmartmeterQueryError: If data validation fails.
        """
        # Resolve Zaehlpunkt
        if zaehlpunktnummer is None:
            customer_id, zaehlpunkt, anlagetype = self.get_zaehlpunkt()
        else:
            customer_id, zaehlpunkt, anlagetype = self.get_zaehlpunkt(zaehlpunktnummer)

        # Set date range defaults
        if date_until is None:
            date_until = date.today()
            
        if date_from is None:
            date_from = date_until - relativedelta(years=3)

        # Query parameters
        query = {
            "datumVon": date_from.strftime("%Y-%m-%d"),
            "datumBis": date_until.strftime("%Y-%m-%d"),
            "wertetyp": valuetype.value,
        }
        
        extra = {
            "Accept": "application/json"
        }

        # API Call
        try:
            data = self._call_api(
                f"zaehlpunkte/{customer_id}/{zaehlpunkt}/messwerte",
                base_url=const.API_URL_B2B,
                query=query,
                extra_headers=extra,
            )
        except Exception as exception:
            raise SmartmeterQueryError(
                f"Historical data query failed: {str(exception)}"
            ) from exception

        # Sanity check: Validate returned zaehlpunkt
        if data.get("zaehlpunkt") != zaehlpunkt:
            logger.debug("Returned data: %s", data)
            raise SmartmeterQueryError("Returned data does not match given zaehlpunkt!")

        # Validate and extract valid OBIS data
        zaehlwerke = data.get("zaehlwerke")
        if not zaehlwerke:
            logger.debug("Returned data: %s", data)
            raise SmartmeterQueryError("Returned data does not contain any zaehlwerke or is empty.")

        return self.find_valid_obis_data(zaehlwerke)

    def bewegungsdaten(
        self,
        zaehlpunktnummer: str = None,
        date_from: date = None,
        date_until: date = None,
        valuetype: const.ValueType = const.ValueType.QUARTER_HOUR,
        aggregat: str = None,
    ) -> Dict[str, Any]:
        """Query energy movement data.
        
        Args:
            zaehlpunktnummer (str, optional): Zaehlpunkt number. Defaults to None.
            date_from (date, optional): Start date. Defaults to None (3 years ago).
            date_until (date, optional): End date. Defaults to None (today).
            valuetype (const.ValueType, optional): Value type. Defaults to QUARTER_HOUR.
            aggregat (str, optional): Aggregation type. Defaults to None.
            
        Returns:
            Dict[str, Any]: Bewegungsdaten response.
            
        Raises:
            SmartmeterQueryError: If data validation fails.
        """
        customer_id, zaehlpunkt, anlagetype = self.get_zaehlpunkt(zaehlpunktnummer)

        # Determine role based on anlage type and value type
        if anlagetype == const.AnlagenType.FEEDING:
            if valuetype == const.ValueType.DAY:
                rolle = const.RoleType.DAILY_FEEDING.value
            else:
                rolle = const.RoleType.QUARTER_HOURLY_FEEDING.value
        else:
            if valuetype == const.ValueType.DAY:
                rolle = const.RoleType.DAILY_CONSUMING.value
            else:
                rolle = const.RoleType.QUARTER_HOURLY_CONSUMING.value

        # Set date range defaults
        if date_until is None:
            date_until = date.today()

        if date_from is None:
            date_from = date_until - relativedelta(years=3)

        # Query parameters
        query = {
            "geschaeftspartner": customer_id,
            "zaehlpunktnummer": zaehlpunkt,
            "rolle": rolle,
            "zeitpunktVon": date_from.strftime("%Y-%m-%dT%H:%M:00.000Z"),
            "zeitpunktBis": date_until.strftime("%Y-%m-%dT23:59:59.999Z"),
            "aggregat": aggregat or "NONE"
        }

        extra = {
            "Accept": "application/json"
        }

        try:
            data = self._call_api(
                f"user/messwerte/bewegungsdaten",
                base_url=const.API_URL_ALT,
                query=query,
                extra_headers=extra,
            )
        except Exception as exception:
            raise SmartmeterQueryError(
                f"Bewegungsdaten query failed: {str(exception)}"
            ) from exception
            
        # Validate returned data
        if data.get("descriptor", {}).get("zaehlpunktnummer") != zaehlpunkt:
            raise SmartmeterQueryError("Returned data does not match given zaehlpunkt!")
            
        return data
