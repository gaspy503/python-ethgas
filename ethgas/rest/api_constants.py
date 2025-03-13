# region User Login & Account
# POST METHODS
LOGIN_ENDPOINT = "/api/v1/user/login"
VERIFY_LOGIN_ENDPOINT = "/api/v1/user/login/verify"
REFRESH_ENDPOINT = "/api/v1/user/login/refresh"
LOGOUT_ENDPOINT = "/api/v1/user/logout"

# GET METHODS
GET_USER_INFO_ENDPOINT = "/api/v1/user/info"
GET_ACCOUNT_INFO_ENDPOINT = "/api/v1/user/account"
CREATE_USER_ACCOUNT_ENDPOINT = "/api/v1/user/account"

GET_USER_ACCOUNT_ID_TXS_ENDPOINT = "/api/v1/user/account/{}/txs"
GET_USER_ACCOUNT_TXS_ENDPOINT = "/api/v1/user/account/txs"
# endregion

# region Deposit & Withdraws
GET_FUNDING_DEPOSITS = "/api/v1/user/funding/deposits"
GET_FUNDING_WITHDRAWS = "/api/v1/user/funding/withdraws"
GET_FUNDING_WITHDRAW_STATUS = "/api/v1/user/funding/withdraw/status"
POST_FUNDING_DEPOSIT = "/api/v1/user/funding/deposit"
# endregion

# region Market
# GET METHODS
GET_ALL_IP_MARKETS_ENDPOINT = "/api/v1/p/inclusion-preconf/markets"
GET_ALL_WB_MARKETS_ENDPOINT = "/api/v1/p/wholeblock/markets"
GET_IP_PUBLIC_TRADES_ENDPOINT = "/api/v1/p/inclusion-preconf/trades"
GET_WB_PUBLIC_TRADES_ENDPOINT = "/api/v1/p/wholeblock/trades"
# endregion

# region Pricer
GET_PRICER_SETTING = "/api/v1/user/pricer"
GET_PRICER_MARKETS_ACTIVE = "/api/v1/pricer/markets/active"
GET_PRICER_ACCOUNT_TOKENS = "/api/v1/pricer/account-tokens"
GET_PRICER_IP_POSITION = "/api/v1/pricer/inclusion-preconf/positions"
GET_PRICER_WB_POSITION = "/api/v1/pricer/wholeblock/positions"
GET_PRICER_IP_ORDERS = "/api/v1/pricer/inclusion-preconf/orders"
GET_PRICER_WB_ORDERS = "/api/v1/pricer/wholeblock/orders"
POST_ENABLE_PRICER = "/api/v1/user/delegate/pricer"

# region Trading
# GET METHODS
GET_USER_IP_ORDERS_ENDPOINT = "/api/v1/user/inclusion-preconf/orders"
GET_USER_IP_POSITIONS_ENDPOINT = "/api/v1/user/inclusion-preconf/positions"
GET_USER_IP_TRADES = "/api/v1/user/inclusion-preconf/txs"
GET_USER_WB_ORDERS_ENDPOINT = "/api/v1/user/wholeblock/orders"
GET_USER_WB_POSITIONS_ENDPOINT = "/api/v1/user/wholeblock/positions"
GET_USER_WB_TRADES = "/api/v1/user/wholeblock/txs"

# POST METHODS
CREATE_IP_ORDER_ENDPOINT = "/api/v1/inclusion-preconf/order"
CANCEL_IP_ORDER_ENDPOINT = "/api/v1/inclusion-preconf/cancel-order"
CANCEL_ALL_IP_ORDERS_ENDPOINT = "/api/v1/inclusion-preconf/cancel-all-orders"
BATCH_CANCEL_IP_ORDERS_ENDPOINT = "/api/v1/inclusion-preconf/cancel-batch-orders"

CREATE_WB_ORDER_ENDPOINT = "/api/v1/wholeblock/order"
CANCEL_WB_ORDER_ENDPOINT = "/api/v1/wholeblock/cancel-order"
BATCH_CANCEL_WB_ORDERS_ENDPOINT = "/api/v1/wholeblock/cancel-batch-orders"
# endregion

# region Block Build
# GET METHODS
GET_BUNDLES_ENDPOINT = "/api/v1/slot/bundles"
GET_ACCOUNT_BUNDLES_ENDPOINT = "/api/v1/slot/account/bundles"

# POST METHODS
POST_INCLUSION_PRECONF_SEND_BUNDLE = "/api/v1/user/bundle/send"
POST_EMPTY_BLOCK_SPACE = "/api/v1/slot/forceEmptyBlockSpace"
# endregion

# region Others
SERVER_STATUS_ENDPOINT = "/api/v1/server/status"
# endregion

# region Validator
GET_VALIDATORS = "/api/v1/user/validators"
POST_VALIDATOR_REGISTER = "/api/v1/validator/register"
POST_VALIDATOR_VERIFY = "/api/v1/validator/verify"
