from enum import Enum


class SessionType:
    PUBLIC = "public"
    PRIVATE = "private"
    Login = "login"


class RequestMethod:
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"


class Order:
    class Side(Enum):
        def __bool__(self):
            return bool(self.value)

        SELL = False
        BUY = True

    class Type(Enum):
        def __int__(self):
            return int(self.value)

        MARKET = 1
        LIMIT = 2


# region fields
ADDRESS = "addr"
CHAIN_ID = "chainId"
REFRESH_TOKEN = "refreshToken"
NONCE_HASH = "nonceHash"
SIGNATURE = "signature"
TRADE_ID = "trade_id"
ACCOUNT_ID = "account_id"
ORDER_ID = "order_id"
INSTRUMENT_ID = "instrument_id"
SYMBOL = "symbol"
RATE = "rate"
PRICE = "price"
QUANTITY = "quantity"
ACC_FILL_SIZE = "acc_fill_size"
SIDE = "side"
UPDATE_TIME = "update_time"
MARKET_ORDER = "market_order"
LIMIT_ORDER = "limit_order"
BIDS = "bids"
ASKS = "asks"
# endregion
