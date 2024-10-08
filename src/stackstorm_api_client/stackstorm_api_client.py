#!/usr/bin/env python3
'''
* stackstorm_api_client.py
*
* Copyright (c) 2023 Jason Piszcyk
*
* @author: Jason Piszcyk
* 
* Simple Client to StackStorm API
*
'''
import requests
import urllib3
import json
import time

from threading import Lock

#
# Constants
#


###########################################################################
#
# StackStormAPIClient Class
#
###########################################################################
#
# StackStormAPIClient
#
class StackStormAPIClient():
    ''' Simple API Client to StackStorm '''
    ERROR_INVALID_PATH = "404 Client Error: Not Found for url:"

    # Private Class Attributes
    __lock = Lock()


    #
    # __init__
    #
    def __init__(self, *args, uri=None, api_key=None, auth_token=None,
                username=None, password=None, verify=True, use_path_prefix=True,
                validate_api_key=True, **kwargs):
        ''' Init method for class '''
        super().__init__(*args, **kwargs)

        # If we don't want to verify the certs, turn off the warnings
        self._verify = verify
        if not self._verify: urllib3.disable_warnings()

        # Creat the path prefeix based on whether to include 'API' or not
        if use_path_prefix:
            self.path_prefix = "/api/v1"
        else:
            self.path_prefix = "/v1"

        if api_key and not validate_api_key:
            # We can skip the check on the API Key and just try to use it...
            # Used for once off requests, saves doing 2 calls to API for one response
            # We will fail on API request if API key is invalid
            # Set the defaults and just store api key
            self._api_uri = uri if uri else "https://localhost"
            self._api_key = api_key
            self._auth_token = None
            self._authenticated = True
        elif auth_token:
            # If we are provided with an Auth Token, assume it is correct
            # We will fail on API request if Auth Token is invalid
            # Login process done elsewhere (eg we are called from a stackstorm action)
            self._api_uri = uri if uri else "https://localhost"
            self._api_key = None
            self._auth_token = auth_token
            self._authenticated = True
        else:
            # Set the defaults and validate the auth info before storing it
            self._api_uri = "https://localhost"
            self._api_key = None
            self._auth_token = None
            self._authenticated = False

            # Set the host to default or the value provided in arguments
            # Will override instance variable if succesful connection
            _conn_uri = uri if uri else self._api_uri

            if api_key:
                self._api_uri = _conn_uri
                self.auth(uri=_conn_uri, api_key=api_key)
            elif username or password:
                # Try to login
                self.login(uri=_conn_uri, username=username, password=password,)



    ###########################################################################
    #
    # Auth Methods
    #
    ###########################################################################
    #
    # login
    #
    def login(self, uri=None, username=None, password=None):
        '''
        Login to the StackStorm API

        Parameters:
            uri: The URI of the StackStorm API
            username: Name of user to authenticate to StackStorm
            password: Password for user to authenticate to StackStorm

        Return Value:
            None
        '''
        if not username:
            raise ValueError("'username' argument must be supplied")

        if not password:
            raise ValueError("'password' argument must be supplied")

        _api_uri = uri if uri else self._api_uri
        _full_path = f"{_api_uri}/auth/v1/tokens"

        try:
            resp_dict = self._api_post(uri=_full_path, username=username, password=password)
        except requests.exceptions.HTTPError:
            return

        if "token" in resp_dict:
            # Store the host/login info
            StackStormAPIClient.__lock.acquire()
            self._api_uri = _api_uri
            self._auth_token = resp_dict["token"]
            self._authenticated = True
            StackStormAPIClient.__lock.release()


    #
    # auth
    #
    def auth(self, uri=None, api_key=None):
        '''
        Authenticate to the StackStorm API via api_key

        Parameters:
            uri: The URI of the StackStorm API
            api_key: API Key to use

        Return Value:
            None
        '''
        if not api_key:
            raise ValueError("'api_key' argument must be supplied")

        _api_uri = uri if uri else self._api_uri
        _full_path = f"{_api_uri}{self.path_prefix}"

        StackStormAPIClient.__lock.acquire()
        self._api_key = api_key
        StackStormAPIClient.__lock.release()

        try:
            resp_dict = self._api_get(uri=_full_path)
        except requests.exceptions.HTTPError:
            self._api_key = None
            return

        StackStormAPIClient.__lock.acquire()
        self._api_uri = _api_uri
        self._authenticated = True
        StackStormAPIClient.__lock.release()


    #
    # authenticated
    #
    def authenticated(self):
        '''
        report if we have authenticated successfully

        Parameters:
            None

        Return Value:
            bool: True if successful, False otherwise
        '''
        return self._authenticated


    ###########################################################################
    #
    # Access Methods
    #
    ###########################################################################
    #
    # _make_uri
    #
    def _make_uri(self, path=None):
        '''
        Generate a URI from info

        Parameters:
            path: The API path to query

        Return Value:
            string: The URI
        '''
        if not path:
            path = "/"
        
        uri = f"{self._api_uri}{path}"
        
        return uri


    #
    # get
    #
    def get(self, path=None, params={}):
        '''
        A simple GET request

        Parameters:
            path: The API path to query
            params: Query parameters for the request

        Return Value:
            dict: Response from the request
        '''
        uri = self._make_uri(path=path)

        return self._api_get(uri=uri, params=params)


    #
    # put
    #
    def put(self, path=None, params={}, body={}):
        '''
        A simple POST request

        Parameters:
            path: The API path to query
            params: Query parameters for the request
            body: The request body

        Return Value:
            boolean: True if successful, False or exception otherwise
        '''
        uri = self._make_uri(path=path)

        return self._api_put(uri=uri, params=params, body=body)


    #
    # post
    #
    def post(self, path=None, params={}, body={}):
        '''
        A simple POST request

        Parameters:
            path: The API path to query
            params: Query parameters for the request
            body: The request body

        Return Value:
            dict: Response from the query
        '''
        uri = self._make_uri(path=path)

        return self._api_post(uri=uri, params=params, body=body)


    #
    # delete
    #
    def delete(self, path=None, params={}):
        '''
        A simple DELETE request

        Parameters:
            path: The API path to query
            params: Query parameters for the request

        Return Value:
            boolean: True if successful, False or exception otherwise
        '''
        uri = self._make_uri(path=path)

        return self._api_delete(uri=uri, params=params)


    ###########################################################################
    #
    # API Helper Methods
    #
    ###########################################################################
    #
    # get_execution_status
    #
    def get_execution_status(self, id=None):
        '''
        Get the status of an execution

        Parameters:
            id: The Execution ID to query

        Return Value:
            string: The status of the execution
        '''
        if not id:
            raise ValueError(f"'id' argument must be specified")

        exec_status = "missing"
        resp = None
        try:
            resp = self.get(f"{self.path_prefix}/executions/{id}")
        except requests.exceptions.HTTPError as err:
            if str(err).find(self.ERROR_INVALID_PATH) == -1:
                raise err

        if resp and "status" in resp:
            exec_status = resp["status"]

        return exec_status


    #
    # wait_for_execution
    #
    def wait_for_execution(self, id=None, timeout=0, interval=10):
        '''
        Wait for an execution to complete

        Parameters:
            id: The Execution ID to wait for
            timeout: Time in secs to wait before giving up (0 = infinite)
            interval: Polling interval in seconds

        Return Value:
            boolean: True if successful, False if failed or timed out
        '''
        if not id:
            raise ValueError(f"'id' argument must be specified")
        
        if interval < 1: interval = 1
        if interval > 300: interval = 300

        elapsed_time = 0
        while (timeout == 0) or (elapsed_time < timeout):
            status = self.get_execution_status(id)

            if status == "missing": return False
            if status == "failed": return False
            if status == "succeeded": return True

            time.sleep(interval)
            elapsed_time += interval
        
        return False


    #
    # get_execution_result
    #
    def get_execution_result(self, id=None):
        '''
        Get the result of an execution

        Parameters:
            id: The Execution ID to query

        Return Value:
            string: The result of the execution
        '''
        if not id:
            raise ValueError(f"'id' argument must be specified")

        exec_status = "missing"
        try:
            resp = self.get(f"{self.path_prefix}/executions/{id}")
        except requests.exceptions.HTTPError as err:
            if str(err).find(self.ERROR_INVALID_PATH) == -1:
                raise err

        if "result" in resp:
            result = resp["result"]

        return result


    ###########################################################################
    #
    # API Access Functions
    #
    ###########################################################################
    #
    # _set_headers
    #
    def _set_headers(self, headers={}):
        '''
        Set the request header based on 

        Parameters:
            header: An existing header to update

        Return Value:
            dict: The header after modification
        '''
        headers.update({
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
        })

        if self._api_key:
            headers.update({"St2-Api-Key": self._api_key})
        elif self._auth_token:
            headers.update({"X-Auth-Token": self._auth_token})
        
        return headers


    #
    # _api_get
    #
    def _api_get(self, uri=None, params={}):
        '''
        A GET request

        Parameters:
            uri: The URI for the API request
            params: Query parameters for the request

        Return Value:
            object: Response converted to the response data type
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        # Perform the request
        headers = self._set_headers()
        req = requests.get(
            uri,
            headers=headers,
            params=params,
            verify=self._verify
        )

        # Raise an exception if the request failed
        req.raise_for_status()

        # Return the info from the request
        req_data = json.loads(req.text)
        return req_data


    #
    # _api_put
    #
    def _api_put(self, uri=None, params={}, body={}):
        '''
        A PUT request

        Parameters:
            uri: The URI for the API request
            params: Query parameters for the request
            body: The request body


        Return Value:
            boolean: True if successful, False or exception otherwise
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        # Perform the request
        headers = {
            "content-type": "application/json"
        }
        headers = self._set_headers(headers)
        req = requests.put(
            uri,
            headers=headers,
            params=params,
            data=json.dumps(body),
            verify=self._verify
        )

        # Raise an exception if the request failed
        req.raise_for_status()

        # The request went through OK
        return True


    #
    # _api_post
    #
    def _api_post(self, uri=None, params={}, body={},
                   username=None, password=None):
        '''
        A POST request 

        Parameters:
            uri: The URI for the API request
            params: Query parameters for the request
            body: The request body
            username: Name of user to authenticate to StackStorm
            password: Password for user to authenticate to StackStorm

        Return Value:
            object: Response converted to the response data type
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        headers = {
            "content-type": "application/json"
        }
        if username or password:
            # We might be trying to login
            req = requests.post(
                uri,
                auth=(username, password),
                headers=headers,
                params=params,
                data=json.dumps(body),
                verify=self._verify
            )
        else:
            # Perform the request
            headers = self._set_headers(headers)
            req = requests.post(
                uri,
                headers=headers,
                params=params,
                data=json.dumps(body),
                verify=self._verify
            )

        # Raise an exception if the request failed
        req.raise_for_status()

        # The request went through OK
        req_data = json.loads(req.text)
        return req_data


    #
    # _api_delete
    #
    def _api_delete(self, uri=None, params={}):
        '''
        A DELETE request

        Parameters:
            uri: The URI for the API request
            params: Query parameters for the request

        Return Value:
            boolean: True if successful, False or exception otherwise
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        # Perform the request
        headers = self._set_headers()
        req = requests.delete(
            uri,
            headers=headers,
            params=params,
            verify=self._verify
        )

        # Raise an exception if the request failed
        req.raise_for_status()

        # The request went through OK
        return True


###########################################################################
#
# In case this is run directly rather than imported...
#
###########################################################################
'''
Handle case of being run directly rather than imported
'''
if __name__ == "__main__":
    pass

