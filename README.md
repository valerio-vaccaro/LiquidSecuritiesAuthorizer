```
  _      _             _     _  _____                      _ _   _
 | |    (_)           (_)   | |/ ____|                    (_) | (_)
 | |     _  __ _ _   _ _  __| | (___   ___  ___ _   _ _ __ _| |_ _  ___  ___
 | |    | |/ _` | | | | |/ _` |\___ \ / _ \/ __| | | | '__| | __| |/ _ \/ __|
 | |____| | (_| | |_| | | (_| |____) |  __/ (__| |_| | |  | | |_| |  __/\__ \
 |______|_|\__, |\__,_|_|\__,_|_____/ \___|\___|\__,_|_|  |_|\__|_|\___||___/
              | |
              |_|    Demo external authorizer
```
# LiquidSecuritiesAuthorizer
This is an examples of external authorizer for liquid securities.
___DON'T USE THIS CODE IN PRODUCTION___

- http.server is not ready for a production service
- we don't show how to add a tls certificate
- configurations are saved in the same file in plain text
- we don't have any api for gaids management
- we can not update rules during authorizer is running
- we allow skip signature check (only for debugging)
- we use error messages in json without specific codes

# How to use
Just clone this repository and call authorizer.py with python3.

```
python3 authorizer.py
```

The server will wait for connection and allow only POST with path `/issuerauthorizer`, other call will generate an error message

You can also specify a TCP port waiting for incoming messages (default: 5005).

```
python3 authorizer.py 80
```

# Configuration

## Liquid node configuration
Connect the authorizer to a Liquid Node in order to verify signature in received messages.

```
RPC_HOST = ''
RPC_PORT = ''
RPC_USER = ''
RPC_PASSWORD = ''
RPC_PASSPHRASE = ''
```

## Liquid securities platform signature
If you want check signature of received messages put `CHECK_SIGNATURE` to `True` and configure the `SIGNATURE_ADDRESS`.

```
CHECK_SIGNATURE = True
SIGNATURE_ADDRESS = ''
```

## Asset ID whitelist
This configuration allows to check the asset id for each transaction received, if you want enable it set `CHECK_ASSET_ID` to `True` and add asset id in hex to the `ASSET_ID` array.

```
CHECK_ASSET_ID = True
ASSET_ID = [
    '',
    '',
]
```

## Amount check
This settings allow filter transaction with little or big amount of token moved, if you want use set `CHECK_AMOUNT` to `True` and configure the min and max thresholds, transaction that move an amount outside this range will not be authorized.

```
CHECK_AMOUNT = True
MIN_AMOUNT = 0
MAX_AMOUNT = 1000000
```

## Whitelist and rules for inputs
This configuration allow you to set a list of account able to spend tokens, if you want use set `CHECK_GAID_IN` to `True` and insert in the `GAIDS_IN_WHITELIST` the authorized GAIDs.

```
CHECK_GAID_IN = True
GAIDS_IN_WHITELIST = [
    '',
    '',
    '',
    '',
    '',
    '',
]
```

## Whitelist and rules for outputs
This configuration allow you to set a list of account able to receive tokens, if you want use set `CHECK_GAID_OUT` to `True` and insert in the `GAIDS_OUT_WHITELIST` the authorized GAIDs.

If `ALLOWS_CHANGES` is set to `True` the GAIDs present in the transaction inputs will be temporary allowed to receive tokens, this is useful if we want allow a GAID to spend partially UTXO and receive back a change.

```
CHECK_GAID_OUT = True
GAIDS_OUT_WHITELIST = [
    '',
    '',
    '',
    '',
    '',
    '',
]
ALLOWS_CHANGES = True
```
