from enum import Enum


# *** Public Channels ***
class Channel:
    class Public:
        PRECONF_MARKET_UPDATE = "preconfMarketUpdate"
        CANDLESTICK_UPDATE = "candlestickUpdate"
        RECENT_TRADES_UPDATE = "recentTradeUpdate"
        ORDERBOOK_UPDATE = "orderBookUpdate"
        TICKER_UPDATE = "tickerUpdate"
        BLOCK_BUILDER_UPDATE = "blockBuilderUpdate"

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

    CANDLESTICKS = "candlesticks"
    CURRENT_SLOT = "currentSlot"
    OPEN_ORDERS = "openOrders"
    CURRENT_POSITIONS = "currentPositions"
    BLOCK_SPACE_SALE = "blockSpaceSale"

# *** Private Channels ***
