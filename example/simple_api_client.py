import logging
import os
import random

from ethgas.rest.api_client import APIClient
from ethgas.utils import helper
from ethgas.utils.constants import Order

if __name__ == "__main__":
    logger = helper.create_logger(logger_level=logging.INFO, logger_name="simple_api_client")
    logger.info("initialize simple api client...")
    # remember to set config in .env file or set env variable (see .env.example)
    rest_url = os.getenv("REST_URL")
    # set account address and private key
    address = os.getenv("EXAMPLE_ACCOUNT_ADDRESS")
    private_key = os.getenv("EXAMPLE_PRIVATE_KEY")
    # create api client
    # if account_address and private_key are None, then the api client will use public REST APIs only
    rest = APIClient(rest_url=rest_url,
                     account_address=address, private_key=private_key,
                     verify_tls=True, refresh_interval=3600, re_login_interval=604800,
                     logger=logger)
    # get current inclusion preconf market info from api client
    # public market info endpoint
    market_info_response = rest.get_all_ip_markets()
    logger.info("inclusion preconf market info: %s", market_info_response)
    ip_markets = market_info_response.get("data", {}).get("markets", [])
    # randomly select an inclusion preconf market
    chosen_market = ip_markets[random.randint(0, len(ip_markets) - 1)]


    # send a limit buy order to the inclusion preconf market with minimum quantity (private endpoint)
    # generate a random client order id as replacement uuid
    ip_order_id = helper.generate_uuid()
    # get the minimum quantity from the inclusion preconf market
    quantity = float(chosen_market.get("minQuantity"))
    # get the maximum price (in ETH) from the inclusion preconf market
    price_eth = float(chosen_market.get("maxPrice"))
    created_order_res = rest.create_ip_order(instrument_id=chosen_market.get("instrumentId"),
                                         side=Order.Side.BUY.value, order_type=Order.Type.LIMIT.value,
                                         quantity=quantity, price=price_eth,
                                         client_order_id=ip_order_id)
    logger.info(f"created inclusion preconf order: {created_order_res}")


    # send a limit buy order to the whole block market (private endpoint)
    # generate a random client order id as replacement uuid
    market_info_response = rest.get_all_wb_markets()
    logger.info("whole block market info: %s", market_info_response)
    wb_markets = market_info_response.get("data", {}).get("markets", [])
    # randomly select an inclusion preconf market
    chosen_market = wb_markets[random.randint(0, len(wb_markets) - 1)]
    wb_order_id = helper.generate_uuid()
    # get the maximum price (in ETH) from the whole block market
    price_eth = float(chosen_market.get("maxPrice"))
    # create an inclusion preconf buy limit order
    created_order_res = rest.create_wb_order(instrument_id=chosen_market.get("instrumentId"),
                                         side=Order.Side.BUY.value, order_type=Order.Type.LIMIT.value,
                                         price=price_eth,
                                         client_order_id=wb_order_id)
    logger.info(f"created whole block order: {created_order_res}")