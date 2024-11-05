from enum import Enum


# *** Public Channels ***
class Channel:
    class Public:
        PRECONF_MARKET_UPDATE = "preConfMarketUpdate"
        MARKET_PRICE_HISTORY = "marketPriceHistory"
        RECENT_TRADES = "recentTrades"
        ORDERBOOK = "orderBook"
        MARKET_INFO = "marketInfo"

    class Private:
        USER_ORDER = "userOrder"
        USER_TRADE = "userTrade"


class MarketType(Enum):
    def __str__(self):
        return str(self.value)

    INCLUSION_PRECONF = "inclusionPreconf"
    WHOLE_BLOCK = "wholeBlock"


class QueryType(Enum):
    def __str__(self):
        return str(self.value)

    CURRENT_SLOT = "currentSlot"
    OPEN_ORDERS = "openOrders"
    CURRENT_POSITIONS = "currentPositions"
    BLOCK_SPACE_SALE = "blockSpaceSale"

# *** Private Channels ***
