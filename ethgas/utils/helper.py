import datetime
import logging
import math
import random
import sys
import uuid
from logging.handlers import RotatingFileHandler
from threading import Thread, Timer
from urllib.parse import urlencode

# to ignore connection pool warning
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)


def generate_uuid() -> str:
    return str(uuid.uuid1())[0:8]
    # return str(uuid.uuid1()).replace('-', '')


def get_current_utc_timestamp() -> float:
    """
    Get current time in UTC timestamp format

    Returns:
        float: current time in UTC timestamp format
    """
    dt = datetime.datetime.now(datetime.timezone.utc)
    utc_time = dt.replace(tzinfo=datetime.timezone.utc)
    return utc_time.timestamp()


def generate_query_url(url: str, dict_query_params: dict):
    """
    Generate a query string for use with a REST API endpoint.
    This function generates the necessary query string from the provided dictionary for use with a REST API endpoint.

    Args:
        url (str): The REST API domain + endpoint.
        dict_query_params (dict): A dictionary containing all parameter names and values to be included in the query string.

    Returns:
        str: The original URL with a query string appended to it derived from the dictionary provided.
    """
    url += "?"

    params = []
    for key, val in dict_query_params.items():
        if isinstance(val, list):
            list_query_str = urlencode([(key, element) for element in val])
            params.append(list_query_str)
            continue

        params.append(str(key) + "=" + str(val))

    url += "&".join(params)
    return url


def create_thread(func: object | None, args: tuple) -> Thread:
    """
    Create and start a daemon thread for the specified function and arguments.

    Args:
        func (object | None): The function name. Do not invoke it; leave out the "()".
        args (tuple): The tuple of the function's arguments.

    Returns:
        Thread: The Thread object.
    """
    t = Thread(target=func, args=args)
    t.daemon = True
    return t


def create_thread_with_kwargs(func: object | None, kwargs: dict) -> Thread:
    """
    Create and start a daemon thread for the specified function and arguments.

    Args:
        func (object | None): The function name. Do not invoke it; leave out the "()".
        kwargs (dict): The dictionary of the function's arguments.

    Returns:
        Thread: The Thread object.
    """

    t = Thread(target=func, kwargs=kwargs)
    t.daemon = True
    return t


def get_default_logger():
    """
    Create a default logger

    Returns:
        default logger
    """
    default_logger = logging
    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(module)s - %(name)s - %(message)s")
    # Create a stream handler and set the formatter
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    default_logger.basicConfig(level=logging.INFO, handlers=[stream_handler])
    return default_logger


def create_logger(logger_level: int = logging.INFO, logger_name: str = "ethgas",
                  filename: str = None) -> logging.Logger:
    """
    Create a logger
    :param logger_level: logger level (default: logging.INFO)
    :param logger_name: logger name (default: "ethgas")
    :param filename: log filename (default: None)
    :return: logger
    """
    logging.basicConfig(level=logger_level)
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        logger.handlers.clear()
    # Create a formatter with the desired format
    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(module)s - %(name)s - %(message)s")
    if filename is not None:
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ts_filename = f"{filename}_{now}.log"
        max_file_size = 524288000  # in bytes
        backup_count = 20
        file_handler = RotatingFileHandler(ts_filename, maxBytes=max_file_size, backupCount=backup_count)
        file_handler.setLevel(logger_level)
        file_handler.setFormatter(formatter)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.setLevel(logger_level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_random_float(min_limit: float, max_limit: float, step: float) -> float:
    """
    Get a random float between the specified limits.
    :param step:
    :param min_limit:
    :param max_limit:
    :return:
    """
    total = int((max_limit - min_limit) / step)
    rand = random.randint(0, total)
    return round(min_limit + rand * step, 11)


def get_ip_price(slot: int, gas_price=20, start=1.25, noisiness=50, scalar=3):
    basic_noise = gas_price * start * (1 + (random.random() - 0.5) / noisiness)
    time_decay_price = (basic_noise-gas_price)/(1 + (slot+1)/scalar)
    return round(time_decay_price, 2)


def get_wb_price(slot: int, gas_price=20, start=1.45, finish=1.63, noisiness=100, scalar1=10, scalar2=50):
    price = gas_price * (start + (finish - start) * (1 + slot) / 64) * (1 + (random.random() - 0.5) / noisiness) - gas_price
    random_number = random.uniform(5.25, 6.00)
    return round(max(price, random_number), 2)


class RepeatTimer(Timer):
    def run(self):
        """
        Override the run method of Timer class.

        This method is called when the timer is started and it repeatedly calls the specified function with the provided arguments.
        """
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
