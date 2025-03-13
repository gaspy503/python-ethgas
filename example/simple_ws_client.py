import logging
import os
import time

from ethgas.rest.api_client import APIClient
from ethgas.utils import helper
from ethgas.websocket import ws_constants
from ethgas.websocket.ws_client import WsClient

if __name__ == "__main__":
    logger = helper.create_logger(logger_level=logging.INFO, logger_name="simple_ws_client")
    logger.info("initialize simple websocket client...")
    # remember to set config in .env file or set env variable (see .env.example)
    rest_url = os.getenv("REST_URL")
    chain_id = os.getenv("CHAIN_ID")
    ws_url = os.getenv("WS_URL")
    # set account address and private key
    address = os.getenv("EXAMPLE_ACCOUNT_ADDRESS")
    private_key = os.getenv("EXAMPLE_PRIVATE_KEY")
    # create api client
    # if account_address and private_key are None, then the api client will use public REST APIs only
    rest = APIClient(rest_url=rest_url, chain_id=chain_id,
                     account_address=address, private_key=private_key,
                     verify_tls=True, user_agent=None, refresh_interval=3600, re_login_interval=604800,
                     logger=logger)
    # create websocket client
    # if api_client is None or not logged in, then the websocket client will use public session only
    ws = WsClient(ws_url=ws_url, api_client=rest, auto_reconnect_retries=5, logger=logger)
    # get market info from api client
    market_info_response = rest.get_all_ip_markets()
    logger.info("inclusion preconf market info: %s", market_info_response)
    ip_markets = market_info_response.get("data.markets", [])
    # subscribe public channels
    # public: inclusion preconf market info channel
    ws.subscribe_market_update(market_type=ws_constants.MarketType.INCLUSION_PRECONF)
    # ws.subscribe_market_update(market_type=ws_constants.MarketType.INCLUSION_PRECONF, is_subscribe=False)
    # ws.subscribe_candlestick_update(market_type=ws_constants.MarketType.INCLUSION_PRECONF)
    # ws.subscribe_recent_trades_update(market_type=ws_constants.MarketType.INCLUSION_PRECONF)
    # ws.subscribe_orderbook(market_type=ws_constants.MarketType.INCLUSION_PRECONF)
    # ws.subscribe_block_builder_update(market_type=ws_constants.MarketType.INCLUSION_PRECONF)
    while True:
        time.sleep(1)
