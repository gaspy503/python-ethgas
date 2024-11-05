import datetime
import json
import logging
import threading
import time
import traceback
import websocket

from ethgas.rest.api_client import APIClient
from ethgas.utils import helper
from ethgas.websocket import ws_constants


class WsClient:
    def __init__(self, ws_url: str, auto_reconnect_retries: int = 0, api_client: APIClient = None,
                 logger: logging.Logger = None):
        """
        Initialize the WebSocket client.
        Args:
            ws_url: EthGas WebSocket URL.
            auto_reconnect_retries: Number of times to attempt reconnection. (defaults to 0)
            api_client: EthGas API client. (optional)
            logger: Logger for logging. (optional)
        """
        self.__api_client = api_client
        self.__ws_thread = None
        self.__ws_id = None
        self.__ws_session = None
        self.__ws_url = ws_url
        self.__ws_request_id = 1
        self.__auto_reconnection_retries = auto_reconnect_retries
        self.__ping_timeout = 20
        self.__ping_interval = 25
        self.__reconnect_lock = threading.Lock()
        self.__reconnect_count = 0
        self.__last_reconnect_timestamp = None
        self.__ping_event = None
        self.__subscribed_channels = []
        self.__logger = logger
        if self.__logger is None:
            self.__logger = helper.get_default_logger()
        if self.__ws_url is None:
            self.__logger.error("No websocket url provided.")
            return
        self.start_ws()
        self.__received_channel_data = {}

    def start_ws(self) -> None:
        """
        Start the WebSocket client.
        Returns:
            None
        """
        self.__ws_thread = self.create_ws_thread()
        self.__ws_thread.start()
        self.__logger.info(f"Verifying websocket connection...")
        while not self.is_connected():
            time.sleep(0.1)
        self.__logger.info(f"Websocket connection (id={self.__ws_id}) is connected.")

    def create_ws_thread(self) -> threading.Thread:
        """
        Creates a thread that connects to the private EthGas server.
        User need to log in on APIClient to get access token before connecting private websocket.

        Returns:
            threading.Thread: A thread of the private WebSocket session.
        """
        self.create_ws()
        return helper.create_thread_with_kwargs(func=self.__ws_session.run_forever,
                                                kwargs={"ping_timeout": self.__ping_timeout,
                                                        "ping_interval": self.__ping_interval})

    def create_ws(self) -> None:
        """
        Creates a WebSocket session.
        Returns:
            None
        """
        self.__logger.debug(f"Creating new ethgas websocket client...")
        new_ws_id = helper.generate_uuid()
        new_ws_session = websocket.WebSocketApp(self.__ws_url,
                                                on_open=self.on_open,
                                                on_message=self.on_message,
                                                on_close=self.on_close,
                                                on_error=self.on_error,
                                                on_ping=self.on_ping,
                                                on_pong=self.on_pong)
        old_ws_session = None
        old_ws_id = None
        if self.__ws_session is not None:
            old_ws_session = self.__ws_session
            old_ws_id = self.__ws_id
            self.__logger.info(f"Expired websocket connection (id={old_ws_id}) will be renewed.")
        # update ws_id and ws_session
        self.__ws_id = new_ws_id
        self.__ws_session = new_ws_session
        # close old websocket connection
        if old_ws_session is not None:
            self.__logger.debug(f"Closing expired websocket connection (id={old_ws_id})...")
            # close old websocket connection
            old_ws_session.close()
            # wait for websocket close
            while old_ws_session.sock.connected:
                time.sleep(0.001)  # Adjust the delay as needed
            self.__logger.info(f"Expired websocket connection (id={old_ws_id}) is closed.")
        if self.__ping_event is not None:
            self.__ping_event.cancel()
        self.__ping_event = helper.RepeatTimer(interval=self.__ping_interval, function=self.send_ping)
        self.__ping_event.start()
        self.__logger.info(f"Websocket connection (id={self.__ws_id}) is created.")

    def send_ping(self) -> None:
        """
        Send a ping message to the WebSocket server.
        Returns:
            None

        """
        self.__ws_session.send("ping")

    def is_connected(self) -> bool:
        """
        Check if the WebSocket client is connected to the server.
        Returns:
            bool: True if connected, False otherwise.
        """
        if self.__ws_session is None or self.__ws_session.sock is None:
            return False
        else:
            return self.__ws_session.sock.connected

    def __re_connect_on_unexpected(self) -> None:
        """
        Re-connect to the WebSocket server if the connection is lost or closed unexpectedly.
        Returns:
            None
        """
        if self.__auto_reconnection_retries == 0:
            self.__logger.info("Auto-reconnection is disabled.")
        elif self.__reconnect_count >= self.__auto_reconnection_retries:
            self.__logger.warning("Cannot re-connect EthGas websocket, maximum retry reached.")
        else:
            self.__reconnect_count += 1
            self.__logger.warning(
                f"catch unexpected re-connection on websocket, count: {self.__reconnect_count} now: {helper.get_current_utc_timestamp()}.")
            self.__re_connect()

    def __re_connect(self) -> bool:
        """
        Re-connect to the WebSocket server.
        Returns:
            bool: True if re-connected, False otherwise.
        """
        if self.__reconnect_lock.locked():
            self.__logger.warning(f"websocket connection(id={self.__ws_id}) is being reconnected.")
            return True
        with self.__reconnect_lock:
            self.__logger.warning(f"websocket connection(id={self.__ws_id}) is reconnecting...")
            old_thread = self.__ws_thread
            new_thread = self.create_ws_thread()
            new_thread.start()
            self.__ws_thread = new_thread
            if old_thread.is_alive():
                old_thread.join()
            while not self.is_connected():
                time.sleep(0.001)
            self.resubscribe_channels()
            self.__last_reconnect_timestamp = helper.get_current_utc_timestamp()
            return True

    def resubscribe_channels(self) -> None:
        """
        Re-subscribe to the channels.
        Returns:
            None
        """
        self.__logger.info(f"Re-subscribe to channels = {self.__subscribed_channels}")
        resubscribe = {
            "op": "subscribe",
            "args": self.__subscribed_channels
        }
        self.__send_message(message=resubscribe)

    def __ws_login(self) -> None:
        """
        Login to the WebSocket server.
        Returns:
            None
        """
        login_message = {
            "op": "login",
            "args": [
                {
                    "accessToken": self.__api_client.get_access_token()
                }
            ]
        }
        self.__send_message(message=login_message)

    # region subscription events
    def subscribe_market_update(self, market_type: ws_constants.MarketType) -> None:
        """
        Subscribe to market update channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None
        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.PRECONF_MARKET_UPDATE,
                                                   market_type=market_type)
        self.__logger.debug(f"Subscribing market update, {message=}.")
        self.__send_message(message=message)

    def unsubscribe_market_update(self, market_type: ws_constants.MarketType) -> None:
        """
        Unsubscribe to market update channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None
        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.PRECONF_MARKET_UPDATE,
                                                   market_type=market_type,
                                                   unsubscribe=True)
        self.__logger.debug(f"Unsubscribing market update, {message=}.")
        self.__send_message(message=message)

    def subscribe_market_price_history(self, market_type: ws_constants.MarketType) -> None:
        """
        Subscribe to market price history channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None

        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.MARKET_PRICE_HISTORY,
                                                   market_type=market_type)
        self.__logger.debug(f"Subscribing market price history, {message=}.")
        self.__send_message(message=message)

    def unsubscribe_market_price_history(self, market_type: ws_constants.MarketType) -> None:
        """
        Unsubscribe to market price history channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None

        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.MARKET_PRICE_HISTORY,
                                                   market_type=market_type,
                                                   unsubscribe=True)
        self.__logger.debug(f"Unsubscribing market price history, {message=}.")
        self.__send_message(message=message)

    def subscribe_recent_trades(self, market_type: ws_constants.MarketType) -> None:
        """
        Subscribe to recent trades channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None

        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.RECENT_TRADES,
                                                   market_type=market_type)
        self.__logger.debug(f"Subscribing recent trades, {message=}.")
        self.__send_message(message=message)

    def unsubscribe_recent_trades(self, market_type: ws_constants.MarketType) -> None:
        """
        Unsubscribe to recent trades channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None

        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.RECENT_TRADES,
                                                   market_type=market_type,
                                                   unsubscribe=True)
        self.__logger.debug(f"Unsubscribing recent trades, {message=}.")
        self.__send_message(message=message)

    def subscribe_orderbook(self, market_type: ws_constants.MarketType) -> None:
        """
        Subscribe to orderbook channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None

        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.ORDERBOOK,
                                                   market_type=market_type)
        self.__logger.debug(f"Subscribing orderbook, {message=}.")
        self.__send_message(message=message)

    def unsubscribe_orderbook(self, market_type: ws_constants.MarketType) -> None:
        """
        Unsubscribe to orderbook channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None

        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.ORDERBOOK,
                                                   market_type=market_type,
                                                   unsubscribe=True)
        self.__logger.debug(f"Unsubscribing orderbook, {message=}.")
        self.__send_message(message=message)

    def subscribe_market_info(self, market_type: ws_constants.MarketType) -> None:
        """
        Subscribe to market info channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None

        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.MARKET_INFO,
                                                   market_type=market_type)
        self.__logger.debug(f"Subscribing orderbook, {message=}.")
        self.__send_message(message=message)

    def unsubscribe_market_info(self, market_type: ws_constants.MarketType) -> None:
        """
        Unsubscribe to market info channel.
        Args:
            market_type: inclusionPreconf or wholeBlock

        Returns:
            None

        """
        message = self.create_subscription_message(channel=ws_constants.Channel.Public.MARKET_INFO,
                                                   market_type=market_type,
                                                   unsubscribe=True)
        self.__logger.debug(f"Unsubscribing orderbook, {message=}.")
        self.__send_message(message=message)

    # endregion

    @staticmethod
    def create_query_message(query_type: ws_constants.QueryType) -> dict:
        """
        Create query message.
        Args:
            query_type: currentSlot, openOrders, currentPositions or blockSpaceSale

        Returns:
            dict: query message
        """
        arg = {"queryType": query_type.value}
        return {
            "op": "query",
            "args": [
                arg
            ]
        }

    @staticmethod
    def create_subscription_message(channel: str, market_type: ws_constants.MarketType = None,
                                    unsubscribe: bool = False) -> dict:
        """
        Create subscription message.
        Args:
            channel: Websocket channel
            market_type: inclusionPreconf or wholeBlock
            unsubscribe: bool

        Returns:
            dict: subscription message
        """
        op = "unsubscribe" if unsubscribe else "subscribe"
        arg = {"channel": channel}
        if market_type is not None:
            arg["marketType"] = market_type.value
        return {
            "op": op,
            "args": [
                arg
            ]
        }

    def __send_message(self, message: dict) -> None:
        """
        Send message to websocket server.
        Args:
            message: dict

        Returns:
            None
        """
        message["id"] = self.__ws_request_id
        self.__logger.info(f"Sending websocket message {message=}.")
        if self.is_connected():
            self.__ws_session.send(json.dumps(message))
            self.__ws_request_id += 1

    def on_open(self, ws: websocket._core.WebSocket) -> None:
        """
        Handle the event when the websocket connection is opened.

        Args:
            ws (websocket.WebSocketApp): websocket app.

        Returns:
            None
        """
        self.__logger.info(f"websocket connection(id={self.__ws_id}) is opened")
        if self.__api_client is not None and self.__api_client.is_logged_in():
            self.__logger.info(f"websocket connection(id={self.__ws_id}) is logging in...")
            self.__ws_login()

    def on_message(self, ws: websocket._core.WebSocket, message: str) -> None:
        """
        Handle the event when a message is received on the websocket.

        Args:
            ws (websocket.WebSocketApp): websocket app
            message (str): The message received from the websocket.
        Returns:
            None
        """
        self.__logger.debug(f"Received message on ws(id={self.__ws_id}): {message=}.")
        if message == 'pong' or message == 'ping':
            return
        self.__logger.info(f"Received message on ws(id={self.__ws_id}): {message=}.")
        message_obj = json.loads(message)
        if message_obj.get("event") == "login":
            self.__logger.info(f"websocket connection(id={self.__ws_id}) is logged in.")
            return
        if message_obj.get("event") == "subscribe":
            self.__subscribed_channels.append(message_obj.get("arg"))
        channel = message_obj.get("e", None)
        if channel is not None:
            if channel == ws_constants.Channel.Public.ORDERBOOK:
                self.on_orderbook_data(message=message_obj)
            elif channel == ws_constants.Channel.Public.PRECONF_MARKET_UPDATE:
                self.on_market_update(message=message_obj)
            elif channel == ws_constants.QueryType.CURRENT_SLOT:
                self.on_current_slot(message=message_obj)

    def on_current_slot(self, message: dict) -> None:
        """
        Handle the event when a current slot message is received on the websocket.
        Args:
            message: current slot message

        Returns:
            None
        """
        try:
            self.__logger.debug(f"Received slot data: {message=}.")
            if message.get("E", None) is not None:
                update_time = datetime.datetime.utcfromtimestamp(message.get("E") / 1000)
            current_slot = message.get("s", None)
            current_slot_time = message.get("t", None)
            til_next_slot_time = message.get("r", None)
        except Exception as e:
            self.__logger.error(f"Error occurred while processing current slot: {e}")

    def on_orderbook_data(self, message: dict) -> None:
        """
        Handle the event when a orderbook message is received on the websocket.
        Args:
            message: orderbook message

        Returns:
            None

        """
        try:
            self.__logger.debug(f"Received orderbook: {message=}.")
        except Exception as e:
            self.__logger.error(f"Exception thrown in on_orderbook_data raw={message}, {e=}. {traceback.format_exc()}")

    def process_orderbook_data(self, orderbook: dict) -> None:
        pass

    def on_market_update(self, message: dict) -> None:
        """
        Handle the event when a market update message is received on the websocket.
        Args:
            message: market update message

        Returns:
            None
        """
        try:
            self.__logger.debug(f"Received market update: {message=}.")
            instrument_id = message.get("s", None)
            data = message.get("P", None)
        except Exception as e:
            self.__logger.error(f"Exception thrown in on_market_update raw={message}, {e=}. {traceback.format_exc()}")

    def process_market_update(self, new_markets: dict) -> None:
        pass

    def get_orderbook(self, instrument_id: str) -> dict | None:
        pass

    def on_close(self, ws: websocket._core.WebSocket, close_status_code: int, message: str) -> None:
        """
        Handle the event when the websocket connection is closed.
        Args:
            ws: websocket app
            close_status_code: websocket close status code
            message: on close message

        Returns:
            None
        """
        if (close_status_code is not None and close_status_code != websocket.STATUS_NORMAL
                and not self.__reconnect_lock.locked()):
            if close_status_code == 4000:
                self.__logger.info(f" websocket connection (id={self.__ws_id}) normally closed by EthGas. {message=}.")
            else:
                self.__logger.warning(
                    f"websocket connection (id={self.__ws_id}) unexpected closed [{close_status_code=}]. {message=}.")
                self.__re_connect_on_unexpected()
        else:
            self.__logger.info(f"websocket connection (id={self.__ws_id}) normally closed. {message=}.")

    def on_error(self, ws: websocket._core.WebSocket, error) -> None:
        """
        Handle the event when the websocket connection throws an error.
        Args:
            ws: websocket app
            error: websocket error

        Returns:
            None
        """
        if (not self.__reconnect_lock.locked()
                and isinstance(error, websocket.WebSocketConnectionClosedException)):
            self.__logger.warning(
                f"websocket session (id={self.__ws_id}) connection error: {error=}. Trigger reconnection.")
            self.__re_connect_on_unexpected()

    def on_ping(self, ws: websocket._core.WebSocket, message: str) -> None:
        """
        Handle the event when the websocket connection receives a ping message.
        Args:
            ws: websocket app
            message: ping message

        Returns:
            None

        """
        self.__logger.debug(f"websocket session (id={self.__ws_id}) got ping, reply sent.")

    def on_pong(self, ws: websocket._core.WebSocket, message: str) -> None:
        """
        Handle the event when the websocket connection receives a pong message.
        Args:
            ws: websocket app
            message: pong message

        Returns:
            None

        """
        self.__logger.debug(f"websocket session (id={self.__ws_id}) got pong, no need to reply.")
