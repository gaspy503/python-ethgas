class BadRequestError(Exception):
    """
    Exception raised for returned EthGas errors.
    Status Code: 400

    Attributes:
        response -- The response object.
        message -- Explanation of the error.
        status_code -- The code number returned.
    """

    def __init__(self, response, message):
        self.response = response
        self.status_code = response.status_code
        self.response_content = response.content

        super().__init__(message)


class UnauthorizedError(Exception):
    """
    Exception raised for returned EthGas errors.
    Status Code: 401

    Attributes:
        response -- The response object.
        message -- Explanation of the error.
        status_code -- The code number returned.
    """

    def __init__(self, response, message):
        self.response = response
        self.status_code = response.status_code
        self.response_content = response.content

        super().__init__(message)


class ForbiddenError(Exception):
    """
    Exception raised for returned EthGas errors.
    Status Code: 403

    Attributes:
        response -- The response object.
        message -- Explanation of the error.
        status_code -- The code number returned.
    """

    def __init__(self, response, message):
        self.response = response
        self.status_code = response.status_code
        self.response_content = response.content

        super().__init__(message)


class InternalServerError(Exception):
    """
    Exception raised for returned EthGas errors.
    Status Code: 500

    Attributes:
        response -- The response object.
        message -- Explanation of the error.
        status_code -- The code number returned.
    """

    def __init__(self, response, message):
        self.response = response
        self.status_code = response.status_code
        self.response_content = response.content

        super().__init__(message)


class ServiceUnavailableError(Exception):
    """
    Exception raised for returned EthGas errors.
    Status Code: 503

    Attributes:
        response -- The response object.
        message -- Explanation of the error.
        status_code -- The code number returned.
    """

    def __init__(self, response, message):
        self.response = response
        self.status_code = response.status_code
        self.response_content = response.content

        super().__init__(message)


class UnspecifiedError(Exception):
    """
    Exception raised for returned EthGas errors.
    """

    def __init__(self, message):
        super().__init__(message)


class InvalidOrderTypeError(Exception):
    """
    Exception raised for invalid EthGas order type error.

    Attributes:
        message -- Explanation of the error.
    """

    def __init__(self, assigned_order_type, message):
        self.assigned_order_type = assigned_order_type

        super().__init__(message)


class InvalidOrderQtyError(Exception):
    """
    Exception raised for invalid EthGas order quantity error.

    Attributes:
        message -- Explanation of the error.
    """

    def __init__(self, assigned_order_quantity, message):
        self.assigned_order_quantity = assigned_order_quantity

        super().__init__(message)


class RequestErrorCodeError(Exception):
    def __init__(self, response, error_code, error_msg_key, message):
        self.response = response
        self.error_code = error_code
        self.error_msg_key = error_msg_key
        super().__init__(message)


class UnknownError(Exception):
    """
    Exception raised for EthGas for unknown error

    Attributes:
        response -- The response object.
        message -- Explanation of the error.
        status_code -- The code number returned.
    """

    def __init__(self, response, message):
        self.response = response
        self.status_code = response.status_code
        self.response_content = response.content

        super().__init__(message)
