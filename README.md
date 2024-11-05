# python-ethgas

This is a Python3 connector for EthGas's RESTful APIs and WebSocket.

Please note that the python-ethgas package is an <b>unofficial</b> project and should be used at your own risk.
It is <b>NOT</b> affiliated with the EthGas and does <b>NOT</b> provide financial or investment advice.

## Table of Contents

- <b>[Overview](#overview)</b>
- <b>[Features](#features)</b>
- <b>[Documentation](#documentation)</b>
- <b>[Quick Start](#quick-start)</b>
- <b>[Example Usage](#example-usage)</b>
- <b>[Disclaimer](#disclaimer)</b>
- <b>[Contact](#contact)</b>

## Overview

The <code>python-ethgas</code> package is a Python3 connector that allows you to interact with the EthGas.
The package utilizes threads to handle concurrent execution of REST API requests and WebSocket subscriptions.
This allows for efficient handling of multiple requests and real-time data streams without blocking the main execution
thread.

The connector provides a <b>REST client</b> that allows you to make requests to all the available REST API endpoints of
the EthGas.
You can perform actions such as retrieving user information, and more.
It also includes a <b>WebSocket client</b> that enables you to subscribe to real-time data streams from EthGas.
You can subscribe to channels like preconf market data, transaction data etc.

To access private endpoints and perform actions on behalf of a user,
both API and Websocket client classes handle the login process and manage the authentication using the <b>JWT access
token</b>.
After you sign in to `APIClient`, the access token is saved and used for private requests. This access token can also be
employed to log in to `WsClient`.
Within this package, you have the option to pass the authenticated APIClient instance to the WsClient class, allowing
for a private WebSocket connection.

This project is undergoing active development, ensuring that new changes to the EthGas APIs or Websocket will be
promptly integrated.

For feedback or suggestions, please reach out via one of the contact methods specified in <b>[Contact](#contact)</b>.

## Features

<ol style="line-height:180%" type="1">
<li>REST API Handling</li>
<li>WebSocket Handling</li>
<li>Thread-based Execution</li>
<li>Exception Handling and Reconnection</li></ol>

| Release Version | Changelog           |
|-----------------|---------------------|
| `0.2.0`         | Development release |

## Documentation

For more detailed information, please refer to the [EthGas Developer Docs](https://developers.ethgas.com/#change-log).

## Quick Start

### Prerequisites

<code>python-ethgas</code> is tested on python version: `3.11`.
Earlier or Later versions of Python might work, but they have not been thoroughly tested and could potentially conflict
with the external web3 library.

<code>python-ethgas</code> utilizes web3, threading, websocket-client and requests for its methods, alongside other
built-in modules.
As the package utilizes the web3 library, we suggest to use version `>=7.4.0` here.

### Installation

To get started with the <code>python-ethgas</code> package, you can install it manually or via <b>PyPI</b> with <code>
pip</code>:

```commandline
pip install python-ethgas
```

## Example Usage

To be able to interact with private endpoints, an ethereum EOA account (wallet address) and the corresponding private
key is <b>required</b>.
We suggest to not include those information in your source code directly but alternatively store them in environment
variables.
Again, please note that the <code>python-ethgas</code> package is an <b>unofficial</b> project and should be used at
your own risk.

<b>JWT access token</b> handling is managed in this package for authentication. For interacting with private endpoints
or private websocket, a login is
required on the EthGas side.
If you intend to establish a private WebSocket connection, please create an instance of the `APIClient` class, log into
your account, and pass it to `WsClient`.
If you want to only interact with public endpoints or public websocket, there is no need to supply an account address or
private key. (Refer to sections 2.1a and 2.2a for more details.)

### 1. Import the required modules

```python
# EthGas REST API Client
from ethgas.rest.api_client import APIClient
# EthGas Websocket Client
from ethgas.websocket.ws_client import WsClient
```

### 2. EthGas REST / WEBSOCKET client

#### 2.1 REST client

```python
# EthGas REST API Client
from ethgas.rest.api_client import APIClient
```

##### 2.1a Public REST client

```python
import logging
from ethgas.utils import helper
# EthGas REST API Client
from ethgas.rest.api_client import APIClient

# create logger
logger = helper.create_logger(logger_level=logging.INFO, logger_name="public_api_client")
rest_url = "<EthGas REST API URL>"
chain_id = "<Chain ID>"
# create public api client
rest = APIClient(rest_url=rest_url, chain_id=chain_id,
                 logger=logger)
```

##### 2.1b Private REST client

```python
import logging
from ethgas.utils import helper
# EthGas REST API Client
from ethgas.rest.api_client import APIClient

# create logger
logger = helper.create_logger(logger_level=logging.INFO, logger_name="private_api_client")
rest_url = "<EthGas REST API URL>"
chain_id = "<Chain ID>"
# set account address and private key
address = "<Account Address>"
private_key = "<Account Private Key>"
# create private api client
rest = APIClient(rest_url=rest_url, chain_id=chain_id,
                 account_address=address, private_key=private_key,
                 logger=logger)
```

#### 2.2 WEBSOCKET client

```python
# EthGas Websocket Client
from ethgas.websocket.ws_client import WsClient
```

##### 2.2a Public WEBSOCKET client

```python
import logging
from ethgas.utils import helper
# EthGas Websocket Client
from ethgas.websocket.ws_client import WsClient

# create logger
logger = helper.create_logger(logger_level=logging.INFO, logger_name="public_ws_client")
ws_url = "<EthGas Websocket URL>"
# create public websocket client
ws = WsClient(ws_url=ws_url, auto_reconnect_retries=5, logger=logger)
```

##### 2.2b Private WEBSOCKET client

```python
import logging
from ethgas.utils import helper
# EthGas REST API Client
from ethgas.rest.api_client import APIClient
# EthGas Websocket Client
from ethgas.websocket.ws_client import WsClient

# create logger
logger = helper.create_logger(logger_level=logging.INFO, logger_name="private_ws_client")
rest_url = "<EthGas REST API URL>"
chain_id = "<Chain ID>"
# set account address and private key
address = "<Account Address>"
private_key = "<Account Private Key>"
# create private api client
rest = APIClient(rest_url=rest_url, chain_id=chain_id,
                 account_address=address, private_key=private_key,
                 logger=logger)
ws_url = "<EthGas Websocket URL>"
# create private websocket client
ws = WsClient(ws_url=ws_url, api_client=rest, auto_reconnect_retries=5, logger=logger)
```

## Disclaimer

This is an unofficial Python project (the "Package") and made available for informational purpose only and does not
constitute financial, investment or trading advice.
You acknowledge and agree to comply with the Terms of service at https://www.ethgas.com/terms-of-service. If you
do not agree, please do not use this package.
Any unauthorised use of the Package is strictly prohibited.

## Contact

For support, suggestions or feedback please reach out to us via the following email address <code>
gaspy503@gmail.com</code>.
