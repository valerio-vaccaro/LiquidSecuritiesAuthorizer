#  _      _             _     _  _____                      _ _   _
# | |    (_)           (_)   | |/ ____|                    (_) | (_)
# | |     _  __ _ _   _ _  __| | (___   ___  ___ _   _ _ __ _| |_ _  ___  ___
# | |    | |/ _` | | | | |/ _` |\___ \ / _ \/ __| | | | '__| | __| |/ _ \/ __|
# | |____| | (_| | |_| | | (_| |____) |  __/ (__| |_| | |  | | |_| |  __/\__ \
# |______|_|\__, |\__,_|_|\__,_|_____/ \___|\___|\__,_|_|  |_|\__|_|\___||___/
#              | |
#              |_|    Demo external authorizer
#
# This is an examples of external authorizer for liquid securities.
#             DON'T USE THIS CODE IN PRODUCTION
#
# - http.server is not ready for a production service
# - we don't show how to add a tls certificate
# - configurations are saved in the same file in plain text
# - we don't have any api for gaids management
# - we can not update rules during authorizer is running
# - we allow skip signature check (only for debugging)
# - we use error messages in json without specific codes

import http.server
import socketserver
import json
import time
import requests
import re

# Liquid node configuration (used for signature check)
RPC_HOST = ''
RPC_PORT = ''
RPC_USER = ''
RPC_PASSWORD = ''
RPC_PASSPHRASE = ''

# Liquid securities platform signature
CHECK_SIGNATURE = False
SIGNATURE_ADDRESS = ''

# Asset ID whitelist
CHECK_ASSET_ID = False
ASSET_ID = [
    '',
    '',
]

# Amount check
CHECK_AMOUNT = False
MIN_AMOUNT = 0
MAX_AMOUNT = 1000000

# Whitelist and rules for inputs
CHECK_GAID_IN = True
GAIDS_IN_WHITELIST = [
    '',
    '',
    '',
    '',
    '',
    '',
]

# Whitelist and rules for outputs
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

class RPCHost(object):
    def __init__(self, url):
        self._session = requests.Session()
        if re.match(r'.*\.onion/*.*', url):
            self._session.proxies = {}
            self._session.proxies['http'] = 'socks5h://localhost:9050'
            self._session.proxies['https'] = 'socks5h://localhost:9050'
        self._url = url
        self._headers = {'content-type': 'application/json'}

    def call(self, rpcMethod, *params):
        payload = json.dumps({"method": rpcMethod, "params": list(params), "jsonrpc": "2.0"})
        tries = 5
        hadConnectionFailures = False
        while True:
            try:
                response = self._session.post(self._url, headers=self._headers, data=payload)
            except requests.exceptions.ConnectionError:
                tries -= 1
                if tries == 0:
                    raise Exception('Failed to connect for remote procedure call.')
                hadFailedConnections = True
                print("Couldn't connect for remote procedure call, will sleep for five seconds and then try again ({} more tries)".format(tries))
                time.sleep(10)
            else:
                if hadConnectionFailures:
                    print('Connected for remote procedure call after retry.')
                break
        if not response.status_code in (200, 500):
            raise Exception('RPC connection failure: ' + str(response.status_code) + ' ' + response.reason)
        responseJSON = response.json()
        if 'error' in responseJSON and responseJSON['error'] != None:
            raise Exception('Error in RPC call: ' + str(responseJSON['error']))
        return responseJSON['result']


class ExternalAuthorizerHandler(http.server.SimpleHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    # GET sends back an error message
    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps({'Error': 'Use a POST call'}).encode())

    # POST parse content and reply
    def do_POST(self):
        if (self.path == '/issuerauthorizer'):
            payload_size = int(self.headers['Content-Length'])
            payload = self.rfile.read(payload_size)
            payload_json = json.loads(payload.decode())

            if not isinstance(payload_json, dict) or \
                    set(payload_json.keys()) != {'message', 'signature'} or \
                    not isinstance(payload_json['message'], dict) or \
                    not isinstance(payload_json['signature'], str):
                json_result = {'result': False, 'error': 'Unexpected formatting',}
                self._set_headers()
                self.wfile.write(json.dumps(json_result).encode())
                return

            signature = payload_json['signature']
            message_dict = payload_json['message']
            message_str = json.dumps(message_dict, separators=(',', ':'), sort_keys=True).encode('ascii').decode()

            if CHECK_SIGNATURE:
                serverURL = 'http://{}:{}@{}:{}'.format(RPC_USER, RPC_PASSWORD, RPC_HOST, RPC_PORT)
                host = RPCHost(serverURL)
                if (len(RPC_PASSPHRASE) > 0):
                    result = host.call('walletpassphrase', RPC_PASSPHRASE, 60)

                response = host.call('verifymessage', SIGNATURE_ADDRESS, signature, message_str)
                if not response:
                    json_result = {'result': False, 'error': 'Invalid signature',}
                    print(json_result)
                    self._set_headers()
                    self.wfile.write(json.dumps(json_result).encode())
                    return

            json_result = {'result': True, 'error': '',}
            if message_dict is None:
                json_result = {'result': False, 'error': error,}
            else:
                # Check asset id
                if CHECK_ASSET_ID:
                    if message_dict['request']['asset_id'] not in ASSET_ID:
                        json_result = {'result': False, 'error': 'Unknown asset id',}
                        print(json_result)
                        self._set_headers()
                        self.wfile.write(json.dumps(json_result).encode())
                        return
                # Check inputs
                i = 0
                total_in = 0
                for row in message_dict['request']['inputs']:
                    total_in = total_in + row['amount']
                    if CHECK_AMOUNT:
                        if row['amount'] < MIN_AMOUNT or row['amount'] > MAX_AMOUNT:
                            json_result = {'result': False, 'error': 'Amount invalid (#{} input)'.format(i),}
                            print(json_result)
                            self._set_headers()
                            self.wfile.write(json.dumps(json_result).encode())
                            return
                    if ALLOWS_CHANGES:
                        GAIDS_OUT_WHITELIST.append(row['gaid'])
                    if CHECK_GAID_IN:
                        if row['gaid'] not in GAIDS_IN_WHITELIST:
                            json_result = {'result': False, 'error': 'Unauthorized GAID (#{} input)'.format(i),}
                            print(json_result)
                            self._set_headers()
                            self.wfile.write(json.dumps(json_result).encode())
                            return
                    i = i + 1
                # Check outputs
                i = 0
                total_out = 0
                for row in message_dict['request']['outputs']:
                    total_out = total_out + row['amount']
                    if CHECK_AMOUNT:
                        if row['amount'] < MIN_AMOUNT or row['amount'] > MAX_AMOUNT:
                            json_result = {'result': False, 'error': 'Amount invalid (#{} output)'.format(i),}
                            print(json_result)
                            self._set_headers()
                            self.wfile.write(json.dumps(json_result).encode())
                            return
                    if CHECK_GAID_OUT:
                        if row['gaid'] not in GAIDS_OUT_WHITELIST:
                            json_result = {'result': False, 'error': 'Unauthorized GAID (#{} output)'.format(i),}
                            print(json_result)
                            self._set_headers()
                            self.wfile.write(json.dumps(json_result).encode())
                            return
                    i = i + 1
                # Check amounts are the same
                if not total_in == total_out:
                    json_result = {'result': False, 'error': 'Different amounts',}
                    print(json_result)
                    self._set_headers()
                    self.wfile.write(json.dumps(json_result).encode())
                    return

            # Send back the result
            self._set_headers()
            print(json_result)
            self.wfile.write(json.dumps(json_result).encode())
        else:
            self._set_headers()
            json_result = {'result': False, 'error': 'Use the path /issuerauthorizer'}
            print(json_result)
            self.wfile.write(json.dumps(json_result).encode())


def run(server_class=socketserver.TCPServer, handler_class=ExternalAuthorizerHandler, port=8008):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    print ('Starting authorizer on port {} ...'.format(port))
    httpd.serve_forever()


if __name__ == "__main__":
    print(
        '  _      _             _     _  _____                      _ _   _\n' +
        ' | |    (_)           (_)   | |/ ____|                    (_) | (_)\n' +
        ' | |     _  __ _ _   _ _  __| | (___   ___  ___ _   _ _ __ _| |_ _  ___  ___\n' +
        ' | |    | |/ _` | | | | |/ _` |\\___ \\ / _ \\/ __| | | | \'__| | __| |/ _ \\/ __|\n' +
        ' | |____| | (_| | |_| | | (_| |____) |  __/ (__| |_| | |  | | |_| |  __/\\__ \\\n' +
        ' |______|_|\\__, |\\__,_|_|\\__,_|_____/ \\___|\\___|\\__,_|_|  |_|\\__|_|\\___||___/\n' +
        '              | |\n'
        '              |_|    Demo external authorizer\n\n' +
        ' This is an examples of external authorizer for liquid securities.\n' +
        '            DON\'T USE THIS CODE IN PRODUCTION\n'
    )
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
