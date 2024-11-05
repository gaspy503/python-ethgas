import json
import logging
import sys
import threading
import traceback

import requests
from eth_account import messages
from requests import JSONDecodeError
from urllib3.exceptions import ProtocolError
from web3.auto import w3

from ethgas.rest import api_constants
from ethgas.utils import exceptions, constants
from ethgas.utils import helper
from ethgas.utils.exceptions import RequestErrorCodeError


class APIClient:
    """
    API Client
    """

    def __init__(self, rest_url: str, chain_id: str, account_address: str = None, private_key: str = None,
                 verify_tls: bool = True, refresh_interval: int = 3600, re_login_interval: int = 604800,
                 user_agent: str = None, logger: logging.Logger = None):
        """
        Initialize the EthGas API Client.
        Args:
            rest_url: EthGas REST API URL
            chain_id: EthGas chain ID
            account_address: account address
            private_key: account private key
            verify_tls: Verify TLS certs. (default: True)
            refresh_interval: JWT token refresh interval in seconds. (default: 3600 seconds = 1 hour)
            re_login_interval: JWT token re-login interval in seconds. (default: 604800 seconds = 7 days)
            user_agent: User agent. (optional)
            logger: Logger. (optional)
        """
        self.__logger = logger
        self.__user_agent = user_agent
        self.__rest_url = rest_url
        self.__chain_id = chain_id
        self.__verify_tls = verify_tls
        self.__is_login = False
        self.__account_address = account_address
        self.__private_key = private_key

        self.__login_session = None
        self.__public_session = None
        self.__private_session = None
        self.__access_token = None
        self.__last_refresh_timestamp = None
        self.__refresh_interval = refresh_interval
        self.__re_login_interval = re_login_interval
        self.__session_lock = threading.Lock()
        self.__refresh_event = None
        self.__re_login_event = None

        if logger is None:
            self.__logger = helper.get_default_logger()
        if self.__user_agent is None:
            self.__user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

        # start
        self.__user_id = None
        self.__accounts = []
        self.__default_trading_account = None
        self.__public_session = self._init_session()
        if self.__private_key is not None:
            self._login()
            if self.__is_login:
                self.__logger.info("Login success.")
                self.__private_session = self._init_session()
                if self.__refresh_event is None:
                    self.__refresh_event = helper.RepeatTimer(self.__refresh_interval, self._refresh_access_token)
                    self.__refresh_event.start()
                if self.__re_login_event is None:
                    self.__re_login_event = helper.RepeatTimer(self.__re_login_interval, self._re_login)
                    self.__re_login_event.start()
                self.get_user_info()
                self.__set_default_trading_account()
            else:
                self.__logger.error("Login failed.")

    # region Login
    def _init_session(self) -> requests.Session:
        """
        Initialize an EthGas Login HTTP session.

        Creates and configures a requests Session object to be used for making
        API calls to the EthGas Login endpoints.

        Sets up the session with proper headers, TLS verification, and the
        user agent string.

        Returns:
            requests.Session: The configured HTTP session object.

        """
        self.__logger.info("Initializing HTTP session for EthGas.")
        session = requests.Session()
        session.verify = self.__verify_tls
        return session

    def close_all_session(self) -> None:
        """
        Close all the EthGas HTTP session.
        """
        self.__refresh_event.cancel()
        self.__re_login_event.cancel()
        if self.__session_lock.locked():
            self.__session_lock.release()
        self.__login_session.close()
        self.__private_session.close()
        self.__public_session.close()
        self.__logger.info("All the HTTP session are closed on ETHGAS.")

    def _login(self) -> None:
        """
        Perform login, verify and get access token.

        Sends login request using account address and chain ID, then verifies the login response.
        After login is verified, saves access token if login succeeds.

        Raises:
            LoginError: If login failed.
        """
        start_t = helper.get_current_utc_timestamp()
        if self.__private_key is None:
            sys.exit("please provide private key. exit.")
        # region get user login verify info
        try:
            # public session for login
            self.__login_session = self._init_session()
            params = {constants.ADDRESS: self.__account_address, constants.CHAIN_ID: self.__chain_id}
            verify_info = self._send_request(session_type=constants.SessionType.Login,
                                             method=constants.RequestMethod.POST,
                                             url=api_constants.LOGIN_ENDPOINT, params=params)
            verify_info = verify_info.get('data', {})
            nonce = verify_info.get("nonceHash", None)
            eip712_message = verify_info.get("eip712Message", None)
            if nonce is None:
                raise Exception
            if eip712_message is None:
                raise Exception
            else:
                eip712_message = json.loads(eip712_message)
        except Exception as e:
            sys.exit(f"Cannot get verify information to login, Error: {e}")
        # endregion
        # region get user signature
        try:
            encoded_message = messages.encode_typed_data(full_message=eip712_message)
            signed_message = w3.eth.account.sign_message(encoded_message, private_key=self.__private_key)
            signature = w3.to_hex(signed_message.signature)
        except Exception as e:
            sys.exit(f"Fail to get user login signature, error:{e}")
        # endregion
        # region sign in with user signature and get access token
        try:
            params = {constants.ADDRESS: self.__account_address, constants.NONCE_HASH: nonce,
                      constants.SIGNATURE: signature}
            login_info = self._send_request(session_type=constants.SessionType.Login,
                                            method=constants.RequestMethod.POST,
                                            url=api_constants.VERIFY_LOGIN_ENDPOINT, params=params)
            login_info = login_info.get('data', {})
            self.__access_token = login_info.get("accessToken", {}).get("token", None)
            if self.__access_token is None:
                self.__logger.error("Fail to get access token when login")
                raise Exception
            self.__last_refresh_timestamp = helper.get_current_utc_timestamp()
            self.__is_login = True
            time_spent = helper.get_current_utc_timestamp() - start_t
            self.__logger.info(f"User logged in, time spent = {time_spent} seconds.")
        except Exception as e:
            sys.exit(f"Cannot sign in with user signature, error: {e}")
        # endregion

    def _refresh_access_token(self) -> None:
        """
        Refresh access token to extend expiration.

        Sends refresh token request to get new access token.
        Saves new token if refresh succeeds.

        Raises:
            RefreshError: If refresh request failed.
        """
        if self.__session_lock.locked():
            self.__logger.info("session is re-logging in or refreshing, ignore access token refresh.")
            return
        if self.__access_token is None:
            self.__logger.error(f"cannot find access token to refresh. Error: {traceback.format_exc()}")
        else:
            with self.__session_lock:
                start_t = helper.get_current_utc_timestamp()
                try:
                    body = {constants.REFRESH_TOKEN: self.__access_token}
                    refresh_info = self._send_request(session_type=constants.SessionType.Login,
                                                      method=constants.RequestMethod.POST,
                                                      url=api_constants.REFRESH_ENDPOINT, data=body)
                    refresh_info = refresh_info.get('data', {})
                    self.__access_token = refresh_info.get("accessToken", {}).get("token", None)
                    if self.__access_token is None:
                        self.__logger.error("Fail to get refreshed access token")
                        raise Exception
                    self.__last_refresh_timestamp = helper.get_current_utc_timestamp()
                    time_spent = helper.get_current_utc_timestamp() - start_t
                    self.__logger.info(f"refreshed JWT token, time spent = {time_spent} seconds.")
                    self.__is_login = True
                except Exception as e:
                    self.__logger.error("cannot refresh access token on EthGas", exc_info=e)

    def is_logged_in(self) -> bool:
        """
        Check if user is logged in.
        Returns: True if user is logged in, False otherwise.

        """
        return self.__is_login

    def _re_login(self) -> None:
        """
        Re-login to EthGas.

        Performs full login flow to re-login and retrieve a new access token.
        Saves new access token if re-login succeeds.

        Raises:
            LoginError: If re-login failed.

        """
        if self.__session_lock.locked():
            self.__logger.debug("EthGas RESTful API Client is re-logging in, ignore duplicate re-login request.")
        else:
            self.__logger.info("re-logging in...")
            with self.__session_lock:
                start_t = helper.get_current_utc_timestamp()
                try:
                    self.__refresh_event.cancel()
                    self.__refresh_event = None
                    self.__is_login = False
                    self._login()
                    if self.__refresh_event is None:
                        self.__refresh_event = helper.RepeatTimer(self.__refresh_interval, self._refresh_access_token)
                        self.__refresh_event.start()
                except Exception as e:
                    self.__logger.error("cannot re-login", exc_info=e)
                finally:
                    time_spent = helper.get_current_utc_timestamp() - start_t
                    self.__logger.debug(f"re-logged in, time spent = {time_spent} seconds")

    def get_access_token(self) -> str:
        """
        Get access token.
        Returns: Access token
        """
        return self.__access_token

    # endregion
    # region Public APIs
    def get_all_ip_markets(self) -> dict | Exception:
        """
        Get all inclusion preconf market info.
        Returns: Dictionary of all inclusion preconf market info.
        Raises:
            Exception: If request failed.
        """
        return self._send_request(session_type=constants.SessionType.PUBLIC, method=constants.RequestMethod.GET,
                                  url=api_constants.GET_ALL_IP_MARKETS_ENDPOINT)

    def get_all_wb_markets(self) -> dict | Exception:
        """
        Get all whole block market info.
        Returns:
            Dictionary of all whole block market info.
        Raises:
            Exception: If request failed.

        """
        return self._send_request(session_type=constants.SessionType.PUBLIC, method=constants.RequestMethod.GET,
                                  url=api_constants.GET_ALL_WB_MARKETS_ENDPOINT)

    def get_ip_public_txs(self, instrument_id) -> dict | Exception:
        """
        Get all inclusion preconf public transactions from specified instrument.
        Args:
            instrument_id: Instrument ID.
        Returns:
            Dictionary of all inclusion preconf public transactions from specified instrument.
        Raises:
            Exception: If request failed.

        """
        params = {
            "instrumentId": instrument_id
        }
        return self._send_request(session_type=constants.SessionType.PUBLIC, method=constants.RequestMethod.GET,
                                  url=api_constants.GET_IP_PUBLIC_TXS_ENDPOINT, params=params)

    def get_wb_public_txs(self, instrument_id) -> dict | Exception:
        """
        Get all whole block public transactions from specified instrument.
        Args:
            instrument_id: Instrument ID.
        Returns:
            Dictionary of all whole block public transactions from specified instrument.
        Raises:
            Exception: If request failed.
        """
        params = {
            "instrumentId": instrument_id
        }
        return self._send_request(session_type=constants.SessionType.PUBLIC, method=constants.RequestMethod.GET,
                                  url=api_constants.GET_WB_PUBLIC_TXS_ENDPOINT, params=params)

    # endregion

    # region Private APIs
    def get_user_info(self) -> dict | Exception:
        """
        Get user information.
        Returns:
            Dictionary of user information.
        Raises:
            Exception: If request failed.
        """
        response = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.GET,
                                      url=api_constants.GET_USER_INFO_ENDPOINT)
        response = response.get("data", {})
        user_info = response.get("user", {})
        self.__user_id = user_info.get("userId")
        self.__accounts = user_info.get("accounts", [])
        return response

    def get_account_info(self) -> dict | Exception:
        """
        Get account information.
        Returns:
            Dictionary of account information.
        Raises:
            Exception: If request failed.
        """
        response = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.GET,
                                      url=api_constants.GET_ACCOUNT_INFO_ENDPOINT + f'/{self.__default_trading_account}')
        return response

    def get_user_accounts(self) -> list | Exception:
        """
        Get user accounts.
        Returns:
            List of user accounts.
        Raises:
            Exception: If request failed.
        """
        return self.__accounts

    def __set_default_trading_account(self, account_id: int | None = None) -> None:
        """
        Set default trading account.
        Args:
            account_id: Acccount ID.
        Returns:
            None
        """
        if account_id is None:
            for acc in self.__accounts:
                if acc.get("type") == 2:
                    self.__default_trading_account = acc.get("accountId")
                    break
        else:
            self.__default_trading_account = account_id

    def get_default_trading_account(self) -> int:
        """
        Get default trading account.
        Returns:
            Default trading account.
        """
        return self.__default_trading_account

    def create_user_account(self) -> None:
        """
        Create user account.
        Returns:
            None
        """
        params = {
            "userId": self.__user_id
        }
        response = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.POST,
                                      url=api_constants.CREATE_USER_ACCOUNT_ENDPOINT, params=params)
        response = response.get("data", {})
        new_account = response.get("account")
        if new_account:
            self.__accounts.append(new_account)

    def create_ip_order(self, instrument_id: str, side: bool, order_type: int, quantity: float,
                        price: float | None = None,
                        account_id: int | None = None, client_order_id: str | None = None,
                        passive: bool = False) -> dict | Exception:
        """
        Create inclusion preconf order.
        Args:
            instrument_id: Instrument ID.
            side: Buy or sell.
            order_type: Limit or market.
            quantity: Quantity.
            price: Price.
            account_id: Account ID.
            client_order_id: Client order ID.
            passive: Passive order.

        Returns:
            Dictionary of created order.
        Raises:
            Exception: If request failed.
        """
        data = {
            "instrumentId": instrument_id,
            "side": side,
            "orderType": order_type,
            "quantity": quantity,
            "accountId": self.__default_trading_account,
            "passive": passive
        }
        if price:
            data["price"] = str(price)
        if account_id:
            data["accountId"] = account_id
        if client_order_id:
            data["clientOrderId"] = client_order_id
        return self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.POST,
                                  url=api_constants.CREATE_IP_ORDER_ENDPOINT, json=data)

    def create_wb_order(self, instrument_id: str, side: bool, order_type: int,
                        price: float | None = None,
                        account_id: int | None = None, client_order_id: str | None = None,
                        passive: bool = False) -> dict | Exception:
        """
        Create whole block order.
        Args:
            instrument_id: Instrument ID.
            side: Buy or sell.
            order_type: Limit or market.
            price: Price.
            account_id: Account ID.
            client_order_id: Client order ID.
            passive: Passive order.

        Returns:
            Dictionary of created order.
        Raises:
            Exception: If request failed.

        """
        data = {
            "instrumentId": instrument_id,
            "side": side,
            "orderType": order_type,
            "accountId": self.__default_trading_account,
            "passive": passive
        }
        if price:
            data["price"] = str(price)
        if account_id:
            data["accountId"] = account_id
        if client_order_id:
            data["clientOrderId"] = client_order_id
        return self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.POST,
                                  url=api_constants.CREATE_WB_ORDER_ENDPOINT, json=data)

    def cancel_ip_order(self, instrument_id: str, client_order_id: str,
                        account_id: int | None = None) -> dict | Exception:
        """
        Cancel inclusion preconf order.
        Args:
            instrument_id: Instrument ID.
            client_order_id: Client order ID.
            account_id: Account ID.

        Returns:
            Dictionary of canceled inclusion preoconf order.
        Raises:
            Exception: If request failed.

        """
        data = {
            "instrumentId": instrument_id,
            "accountId": self.__default_trading_account,
            "clientOrderId": client_order_id
        }
        if account_id:
            data["accountId"] = account_id
        res = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.POST,
                                 url=api_constants.CANCEL_IP_ORDER_ENDPOINT, json=data)
        return res

    def cancel_wb_order(self, instrument_id: str, client_order_id: str,
                        account_id: int | None = None) -> dict | Exception:
        """
        Cancel whole block order.
        Args:
            instrument_id: Instrument ID.
            client_order_id: Client order ID.
            account_id: Account ID.

        Returns:
            Dictionary of canceled whole block order.
        Raises:
            Exception: If request failed.

        """
        data = {
            "instrumentId": instrument_id,
            "accountId": self.__default_trading_account,
            "clientOrderId": client_order_id
        }
        if account_id:
            data["accountId"] = account_id
        res = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.POST,
                                 url=api_constants.CANCEL_WB_ORDER_ENDPOINT, json=data)
        return res

    def cancel_all_orders(self, instrument_id: str, account_id: int | None = None) -> dict | Exception:
        """
        Cancel all orders on specified instrument.
        Args:
            instrument_id: Instrument ID.
            account_id: Account ID.

        Returns:
            Dictionary of canceled orders.
        Raises:
            Exception: If request failed.

        """
        data = {
            "instrumentId": instrument_id,
            "accountId": self.__default_trading_account,
        }
        if account_id:
            data["accountId"] = account_id
        res = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.POST,
                                 url=api_constants.CANCEL_ALL_IP_ORDERS_ENDPOINT, json=data)
        return res

    def cancel_batch_ip_orders(self, instrument_id: str, client_order_ids: list[str],
                               account_id: int | None = None) -> dict | Exception:
        """
        Batch cancel inclusion preconf orders on specified instrument.
        Args:
            instrument_id: Instrument ID.
            client_order_ids: List of client order IDs.
            account_id: Account ID.

        Returns:
            Dictionary of canceled orders.
        Raises:
            Exception: If request failed.
        """
        data = {
            "instrumentId": instrument_id,
            "accountId": self.__default_trading_account,
            "clientOrderIds": client_order_ids
        }
        if account_id:
            data["accountId"] = account_id
        res = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.POST,
                                 url=api_constants.BATCH_CANCEL_IP_ORDERS_ENDPOINT, json=data)
        return res

    def cancel_batch_wb_orders(self, instrument_id: str, client_order_ids: list[str], account_id: int | None = None):
        """
        Batch cancel whole block orders on specified instrument.
        Args:
            instrument_id: Instrument ID.
            client_order_ids: List of client order IDs.
            account_id: Account ID.

        Returns:
            Dictionary of canceled orders.
        Raises:
            Exception: If request failed.

        """
        data = {
            "instrumentId": instrument_id,
            "accountId": self.__default_trading_account,
            "clientOrderIds": client_order_ids
        }
        if account_id:
            data["accountId"] = account_id
        res = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.POST,
                                 url=api_constants.BATCH_CANCEL_WB_ORDERS_ENDPOINT, json=data)
        return res

    def get_account_ip_orders(self, account_id: int | None = None, instrument_id=None,
                              pending=True) -> dict | Exception:
        """
        Get account's inclusion preconf orders on specified instrument.
        Args:
            account_id: Account ID.
            instrument_id: Instrument ID.
            pending: Is pending orders.

        Returns:
            Dictionary of account's inclusion preconf orders.
        Raises:
            Exception: If request failed.
        """
        params = {
            "accountId": self.__default_trading_account,
            "pending": pending,
            "limit": 1000,
        }
        if instrument_id:
            params["instrumentId"] = instrument_id
        if account_id:
            params["accountId"] = account_id
        return self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.GET,
                                  url=api_constants.GET_USER_IP_ORDERS_ENDPOINT, params=params)

    def get_account_wb_orders(self, account_id: int | None = None, instrument_id=None,
                              pending=True) -> dict | Exception:
        """
        Get account's whole block orders on specified instrument.
        Args:
            account_id: Account ID.
            instrument_id: Instrument ID.
            pending: Is pending orders.

        Returns:
            Dictionary of account's whole block orders.
        Raises:
            Exception: If request failed.
        """
        params = {
            "accountId": self.__default_trading_account,
            "pending": pending,
            "limit": 1000,
        }
        if instrument_id:
            params["instrumentId"] = instrument_id
        if account_id:
            params["accountId"] = account_id
        return self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.GET,
                                  url=api_constants.GET_USER_WB_ORDERS_ENDPOINT, params=params)

    def get_ip_positions(self) -> dict | Exception:
        """
        Get account's inclusion preconf positions.
        Returns:
            Dictionary of account's inclusion preconf positions.
        Raises:
            Exception: If request failed.

        """
        params = {
            "limit": 100
        }
        res = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.GET,
                                 url=api_constants.GET_USER_IP_POSITIONS_ENDPOINT, params=params)
        position_dict = {}
        for position in res['data']['positions']:
            instrument_id = "ETH-PC-" + str(position['slot'])
            position['instrument_id'] = instrument_id
            position_dict[position['instrument_id']] = position
        return position_dict

    def get_wb_positions(self) -> dict | Exception:
        """
        Get account's whole block positions.
        Returns:
            Dictionary of account's whole block positions.
        Raises:
            Exception: If request failed.
        """
        params = {
            "limit": 100,
            # "enable": True
        }
        res = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.GET,
                                 url=api_constants.GET_USER_WB_POSITIONS_ENDPOINT, params=params)
        position_dict = {}
        for position in res['data']['positions']:
            instrument_id = "ETH-WB-" + str(position['slot'])
            position['instrument_id'] = instrument_id
            position_dict[instrument_id] = position
        return position_dict

    def submit_bundle(self, slot_num, replacement_uuid, bundle):
        """
        Submit an inclusion preconf bundle.
        Args:
            slot_num: Slot number.
            replacement_uuid: Replacement UUID.
            bundle: Bundle.

        Returns:
            Dictionary of response.
        Raises:
            Exception: If request failed.
        """
        params = {
            'slotNumber': slot_num,
            'replacementUuid': replacement_uuid,
            'trxs': bundle
        }

        res = self._send_request(session_type=constants.SessionType.PRIVATE, method=constants.RequestMethod.POST,
                                 url=api_constants.POST_INCLUSION_PRECONF_SEND_BUNDLE, json=params)
        return res

    # endregion

    def _send_request(self, session_type: constants.SessionType, method: str, **kwargs) -> dict | Exception:
        """
        Send API request to EthGas.
        Args:
            session_type: Session type.
            method: Method.
            **kwargs: Other parameters.

        Returns:
            Dictionary of response.
        Raises:
            Exception: If request failed.
        """
        try:
            if self.__rest_url is None:
                raise ValueError("REST API domain cannot be None")

            kwargs["url"] = self.__rest_url + kwargs.get("url", "")
            headers = {"Content-Type": "application/json", "User-Agent": self.__user_agent}
            if session_type == constants.SessionType.Login:
                request_session = self.__login_session
            elif session_type == constants.SessionType.PRIVATE:
                request_session = self.__private_session
                headers.update({"Authorization": "Bearer " + self.__access_token})
            else:
                request_session = self.__public_session
            call = getattr(request_session, method)
            response = call(**kwargs, headers=headers)
            self.__logger.info(
                f"{session_type} session request to {kwargs}")
            return self._handle_response(request_param=json.dumps(kwargs), response=response, session_type=session_type)
        except Exception as e:
            self.__logger.error(f"{session_type} session fail to send request", exc_info=e)
            raise e

    def _handle_response(self, request_param, response: requests.Response,
                         session_type: constants.SessionType) -> dict | Exception | RequestErrorCodeError:
        """
        Handle response from EthGas.
        Args:
            request_param: Request parameters.
            response: Response.
            session_type: Session type.

        Returns:
            Dictionary of response.
        Raises:
            Exception: If request failed.

        """
        try:
            if not str(response.status_code).startswith("2"):
                # self.__logger.error(f"_handle_response error {request_param=} {response=} {session_type=}")
                trace_msg = traceback.format_exc()
                error_message = f" {session_type} request to EthGas failed, full response {response.text}, traceback: {trace_msg}"
                if str(response.status_code) == "400":
                    raise exceptions.BadRequestError(response=response,
                                                     message=request_param + "Bad request error [400]" + error_message)
                elif str(response.status_code) == "401":
                    raise exceptions.UnauthorizedError(response=response,
                                                       message=request_param + "Unauthorized error [401]" + error_message)
                elif str(response.status_code) == "403":
                    raise exceptions.ForbiddenError(response=response,
                                                    message=request_param + "Forbidden error [403]" + error_message)
                elif str(response.status_code) == "500":
                    raise exceptions.InternalServerError(response=response,
                                                         message=request_param + "Internal server error [500]" + error_message)
                elif str(response.status_code) == "503":
                    raise exceptions.ServiceUnavailableError(response=response,
                                                             message=request_param + "Service unavailable error [503]" + error_message)
                else:
                    raise exceptions.UnknownError(response=response,
                                                  message=request_param + f"Unknown error [{str(response.status_code)}]" + error_message)

            res = response.json()

            if type(res) is list:
                response_success = res[0].get("success", None) if res else "success"
            else:
                response_success = res.get("success", None)

            if response_success is not None:
                if response_success is False:
                    error_code = res["errorCode"]
                    error_msg_key = res["errorMsgKey"]
                    raise RequestErrorCodeError(response=response, error_code=error_code,
                                                error_msg_key=error_msg_key,
                                                message=request_param + f"EthGas request unsuccessful. Check the error code and "
                                                                        f"error message key for details. {error_code=}, {error_msg_key=}.")

            self.__logger.debug(f"receive response {res}")
            # by default return full response, unless it has the "data" attribute, then this is returned
            return res
        except exceptions.UnauthorizedError as e:
            self.__logger.error(
                f"{session_type} REST session fail to send request due to connection error={e}, will re-login.")
            self._re_login()
            return {}
        except (ProtocolError, requests.exceptions.ConnectionError) as e:
            self.__logger.error(f"{session_type} REST session fail to send request due to connection error={e}")
            raise e
        except (ValueError, JSONDecodeError) as e:
            self.__logger.error(f"Error occurs when handling REST {session_type} response = {response.text}",
                                exc_info=e)
            raise e
        except Exception as e:
            self.__logger.error(f"Unknown error occurs when handling REST {session_type} response = {response.text}",
                                exc_info=e)
            raise e
