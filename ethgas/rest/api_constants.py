# region User Login & Account
# POST METHODS
LOGIN_ENDPOINT = "/api/user/login"
VERIFY_LOGIN_ENDPOINT = "/api/user/login/verify"
REFRESH_ENDPOINT = "/api/user/login/refresh"
LOGOUT_ENDPOINT = "/api/user/logout"
POST_INCLUSION_PRECONF_SEND_BUNDLE = "/api/inclusion_preconf/send"

# GET METHODS
GET_USER_INFO_ENDPOINT = "/api/user/info"
GET_ACCOUNT_INFO_ENDPOINT = "/api/user/account"
CREATE_USER_ACCOUNT_ENDPOINT = "/api/user/account"

GET_USER_IP_TRXS_ENDPOINT = "/api/user/account/{}/trxs"
# endregion

# region Market
# GET METHODS
GET_ALL_IP_MARKETS_ENDPOINT = "/api/p/inclusion_preconf/markets"
GET_ALL_WB_MARKETS_ENDPOINT = "/api/p/wholeblock/markets"
GET_IP_PUBLIC_TXS_ENDPOINT = "/api/p/inclusion_preconf/trxs"
GET_WB_PUBLIC_TXS_ENDPOINT = "/api/p/wholeblock/trxs"
# endregion

# region Trading
# GET METHODS
GET_USER_IP_ORDERS_ENDPOINT = "/api/user/inclusion_preconf/orders"
GET_USER_IP_POSITIONS_ENDPOINT = "/api/user/inclusion_preconf/positions"
GET_USER_WB_ORDERS_ENDPOINT = "/api/user/wholeblock/orders"
GET_USER_WB_POSITIONS_ENDPOINT = "/api/user/wholeblock/positions"

# POST METHODS
CREATE_IP_ORDER_ENDPOINT = "/api/inclusion_preconf/order"
CANCEL_IP_ORDER_ENDPOINT = "/api/inclusion_preconf/cancel-order"
CANCEL_ALL_IP_ORDERS_ENDPOINT = "/api/inclusion_preconf/cancel-all-orders"
BATCH_CANCEL_IP_ORDERS_ENDPOINT = "/api/inclusion_preconf/cancel-batch-orders"

CREATE_WB_ORDER_ENDPOINT = "/api/wholeblock/order"
CANCEL_WB_ORDER_ENDPOINT = "/api/wholeblock/cancel-order"
BATCH_CANCEL_WB_ORDERS_ENDPOINT = "/api/wholeblock/cancel-batch-orders"
# endregion

# region Others
SERVER_STATUS_ENDPOINT = "/api/server/status"
# endregion
