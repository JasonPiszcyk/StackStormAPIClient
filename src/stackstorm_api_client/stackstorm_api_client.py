#!/usr/bin/env python3
'''
Simple Client to StackStorm API

Copyright (C) 2025 Jason Piszcyk
Email: Jason.Piszcyk@gmail.com

All rights reserved.

This software is private and may NOT be copied, distributed, reverse engineered,
decompiled, or modified without the express written permission of the copyright
holder.

The copyright holder makes no warranties, express or implied, about its 
suitability for any particular purpose.
'''
###########################################################################
#
# Imports
#
###########################################################################
# Shared variables, constants, etc

# System Modules
import requests
import urllib3
import json
import time
from threading import Lock

# Local app modules

# Imports for python variable type hints


###########################################################################
#
# Module Specific Items
#
###########################################################################
#
# Types
#
type ST2_Response = dict | list | tuple | bool | int | float | str | None

#
# Constants
#

#
# Global Variables
#

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
    '''
    Class to describe a simple API Client to StackStorm

    Attributes:
        authenticated (bool): Indicate if API authetication was successful
    '''
    ERROR_INVALID_PATH = "404 Client Error: Not Found for url:"

    # Private Class Attributes
    __lock = Lock()


    #
    # __init__
    #
    def __init__(
            self,
            uri: str = "",
            api_key: str = "",
            auth_token: str = "",
            username: str = "",
            password: str = "",
            verify: bool = True,
            use_path_prefix: bool = True,
            validate_api_key: bool = True
    ):
        '''
        Initialises the instance.

        Args:
            uri (str): The URI for the request (eg https://api.st2.internal)
            api_key (str): The API Key to connect to ST2
            auth_token (str): Token obtained via previous login
            username (str): Username to use to login
            password (str): Password to use to login
            verify (bool): If True, allow urllib3 to verify certificates. If
                False, turn of certificate verification
            use_path_prefix (bool): If True, prepend '/api' to request URI
            validate_api_key (bool): If True, validate the API key via a call
                to ST2.  If False, the key will be sent as part of a request
                and the request will fail if the key is invalid
                
        Returns:
            None

        Raises:
            None
        '''

        # Private Attributes
        self.__verify = verify
        self.__authenticated = False

        # If requested, turn off the warnings about cert verification
        if not self.__verify: urllib3.disable_warnings()

        # Create the path prefeix based on whether to include 'API' or not
        if use_path_prefix:
            self.path_prefix = "/api/v1"
        else:
            self.path_prefix = "/v1"

        if api_key and not validate_api_key:
            # We can skip the check on the API Key and just try to use it...
            # Used for once off requests, saves doing 2 calls to API for one
            # response
            # We will fail on API request if API key is invalid
            # Set the defaults and just store api key
            self.__api_uri = uri if uri else "https://localhost"
            self.__api_key = api_key
            self.__auth_token = None
            self.__authenticated = True
        elif auth_token:
            # If we are provided with an Auth Token, assume it is correct
            # We will fail on API request if Auth Token is invalid
            # Login process done elsewhere (eg we are called from a stackstorm
            # action)
            self.__api_uri = uri if uri else "https://localhost"
            self.__api_key = None
            self.__auth_token = auth_token
            self.__authenticated = True
        else:
            # Set the defaults and validate the auth info before storing it
            self.__api_uri = "https://localhost"
            self.__api_key = None
            self.__auth_token = None
            self.__authenticated = False

            # Set the host to default or the value provided in arguments
            # Will override instance variable if succesful connection
            _conn_uri = uri if uri else self.__api_uri

            if api_key:
                self.__api_uri = _conn_uri
                self.auth(uri=_conn_uri, api_key=api_key)
            elif username or password:
                # Try to login
                self.login(uri=_conn_uri, username=username, password=password)


    ###########################################################################
    #
    # Properties
    #
    ###########################################################################
    #
    # authenticated
    #
    @property
    def authenticated(self) -> bool:
        ''' Indicate if the API authentication was successful '''
        return self.__authenticated


    ###########################################################################
    #
    # Auth Methods
    #
    ###########################################################################
    #
    # login
    #
    def login(
            self,
            uri: str = "",
            username: str = "",
            password: str = ""
    ):
        '''
        Login to the StackStorm API

        Args:
            uri (str): The URI of the StackStorm API
            username (str): Name of user to authenticate to StackStorm
            password (str): Password for user to authenticate to StackStorm

        Returns:
            None

        Raises:
            ValueError
                when username is empty
                when password is empty
        '''
        if not username:
            raise ValueError("'username' argument must be supplied")

        if not password:
            raise ValueError("'password' argument must be supplied")

        _api_uri = uri or self.__api_uri
        _full_path = f"{_api_uri}/auth/v1/tokens"

        try:
            _resp_dict = self._api_post(
                uri=_full_path,
                username=username,
                password=password
            )

        except requests.exceptions.HTTPError:
            return

        if not isinstance(_resp_dict, dict):
            # Response is invalid
            return

        if "token" in _resp_dict:
            # Store the host/login info
            StackStormAPIClient.__lock.acquire()
            self.__api_uri = _api_uri
            self.__auth_token = _resp_dict["token"]
            self.__authenticated = True
            StackStormAPIClient.__lock.release()


    #
    # auth
    #
    def auth(
            self,
            uri: str = "",
            api_key: str = ""
    ):
        '''
        Authenticate to the StackStorm API via api_key

        Args:
            uri (str): The URI of the StackStorm API
            api_key (str): API Key to use

        Returns:
            None

        Raises:
            ValueError
                when api_key is empty
        '''
        if not api_key:
            raise ValueError("'api_key' argument must be supplied")

        _api_uri = uri or self.__api_uri
        _full_path = f"{_api_uri}{self.path_prefix}"

        StackStormAPIClient.__lock.acquire()
        self.__api_key = api_key
        StackStormAPIClient.__lock.release()

        try:
            _ = self._api_get(uri=_full_path)
        except requests.exceptions.HTTPError:
            self.__api_key = None
            return

        StackStormAPIClient.__lock.acquire()
        self.__api_uri = _api_uri
        self.__authenticated = True
        StackStormAPIClient.__lock.release()


    ###########################################################################
    #
    # Access Methods
    #
    ###########################################################################
    #
    # _make_uri
    #
    def _make_uri(
            self,
            path: str = ""
    ) -> str:
        '''
        Generate a URI from info

        Args:
            path (str): The API path to query

        Returns:
            None

        Raises:
            None
        '''
        if not path: path = "/"
        
        return f"{self.__api_uri}{path}"


    #
    # get
    #
    def get(
            self,
            path: str = "",
            params: dict = {}
    ) ->  ST2_Response:
        '''
        A simple GET request

        Args:
            path (str): The API path to query
            params (dict): Query parameters for the request

        Returns:
            ST2_Response: Response from the ST2 API

        Raises:
            None
        '''
        uri = self._make_uri(path=path)

        return self._api_get(uri=uri, params=params)


    #
    # put
    #
    def put(
            self,
            path: str = "",
            params: dict = {},
            body: dict = {}
    ) -> bool:
        '''
        A simple PUT request

        Args:
            path (str): The API path to query
            params (dict): Query parameters for the request
            body (dict): The request body

        Returns:
            boolean: True if successful, False otherwise

        Raises:
            None
        '''
        _uri = self._make_uri(path=path)

        return self._api_put(uri=_uri, params=params, body=body)


    #
    # post
    #
    def post(
            self,
            path: str = "",
            params: dict = {},
            body: dict = {}
    ) -> ST2_Response:
        '''
        A simple POST request

        Args:
            path (str): The API path to query
            params (dict): Query parameters for the request
            body (dict): The request body

        Returns:
            ST2_Response: Response from the ST2 API

        Raises:
            None
        '''
        _uri = self._make_uri(path=path)

        return self._api_post(uri=_uri, params=params, body=body)


    #
    # delete
    #
    def delete(
            self,
            path: str = "",
            params: dict = {},
    ) -> bool:
        '''
        A simple DELETE request

                Args:
            path (str): The API path to query
            params (dict): Query parameters for the request

        Returns:
            boolean: True if successful, False otherwise

        Raises:
            None
        '''
        _uri = self._make_uri(path=path)

        return self._api_delete(uri=_uri, params=params)


    ###########################################################################
    #
    # API Helper Methods
    #
    ###########################################################################
    #
    # get_execution_status
    #
    def get_execution_status(
            self,
            id: str = ""
    ) -> str:
        '''
        Get the status of an execution

        Args:
            id (str): The Execution ID to query

        Returns:
            str: The status of the execution

        Raises:
            ValueError
                when id is empty            
        '''
        if not id:
            raise ValueError(f"'id' argument must be specified")

        _exec_status = "missing"
        _resp = None
        try:
            _resp = self.get(f"{self.path_prefix}/executions/{id}")
        except requests.exceptions.HTTPError as err:
            if str(err).find(self.ERROR_INVALID_PATH) == -1:
                raise err

        if isinstance(_resp, dict) and "status" in _resp:
            _exec_status = _resp["status"]

        return _exec_status


    #
    # wait_for_execution
    #
    def wait_for_execution(
            self,
            id: str = "",
            timeout:int = 0,
            interval: int = 10
    ) -> bool:
        '''
        Wait for an execution to complete

        Args:
            id (str): The Execution ID to query
            timeout (int): Time in secs to wait before giving up (0 = infinite)
            interval (int): Polling interval in seconds

        Returns:
            boolean: True if successful, False if failed or timed out

        Raises:
            ValueError
                when id is empty            
        '''
        if not id:
            raise ValueError(f"'id' argument must be specified")

        # Ensur the interval is 'sane'
        if interval < 1: interval = 1
        if interval > 300: interval = 300

        _elapsed_time = 0
        while (timeout == 0) or (_elapsed_time < timeout):
            _status = self.get_execution_status(id)

            if _status in ("missing", "failed"): return False
            if _status == "succeeded": return True

            time.sleep(interval)
            _elapsed_time += interval

        # Timed out before receiving a response
        return False


    #
    # get_execution_result
    #
    def get_execution_result(
            self,
            id: str = ""
    ) -> ST2_Response:
        '''
        Get the result of an execution

        Args:
            id (str): The Execution ID to query

        Return Value:
            string: The result of the execution

        Raises:
            ValueError
                when id is empt or invalid
        '''
        if not id:
            raise ValueError(f"'id' argument must be specified")

        _resp = None
        try:
            _resp = self.get(f"{self.path_prefix}/executions/{id}")
        except requests.exceptions.HTTPError as err:
            if str(err).find(self.ERROR_INVALID_PATH) == -1:
                raise ValueError(f"execution cannot be found (ID={id})")

        # Query should return a dict
        if not isinstance(_resp, dict):
            return None

        if "result" in _resp:
            return _resp["result"]

        return None


    ###########################################################################
    #
    # API Access Functions
    #
    ###########################################################################
    #
    # _check_response
    #
    def _check_response(
            self,
            response
    ) -> ST2_Response:
        '''
        Check the response value and make sure it is of type ST2_Response

        Args:
            response (any): The response from a request

        Returns:
            ST2_Response: The response or None if it was not a valid type

        Raises:
            None
        '''
        if isinstance(response, (dict, list, tuple, bool, int, float, str)):
            return response

        # Unknown type (or possibly None)
        return None
        

    #
    # _set_headers
    #
    def _set_headers(
            self,
            headers: dict = {}
    ) -> dict:
        '''
        Set the request header based on 

        Args:
            header (dict): An existing header to update

        Returns:
            dict: The headers after modification

        Raises:
            None
        '''
        headers.update({
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
        })

        if self.__api_key:
            headers.update({"St2-Api-Key": self.__api_key})
        elif self.__auth_token:
            headers.update({"X-Auth-Token": self.__auth_token})
        
        return headers


    #
    # _api_get
    #
    def _api_get(
            self,
            uri: str = "",
            params:dict = {}
    ) -> ST2_Response:
        '''
        A GET request

        Args:
            uri (str): The URI for the API request
            params (dict): Query parameters for the request

        Returns:
            ST2_Response: Response from the ST2 API

        Raises:
            ValueError
                when uri is empty
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        # Perform the request
        _req = requests.get(
            uri,
            headers=self._set_headers(),
            params=params,
            verify=self.__verify
        )

        # Raise an exception if the request failed
        _req.raise_for_status()

        # Process the info from the request
        return self._check_response(_req.json())


    #
    # _api_put
    #
    def _api_put(
            self,
            uri: str = "",
            params: dict = {},
            body: dict = {}
    ) -> bool:
        '''
        A PUT request

        Args:
            uri (str): The URI for the API request
            params (dict): Query parameters for the request
            body (dict): The request body

        Returns:
            boolean: True if successful, False or exception otherwise

        Raises:
            ValueError
                when uri is empty            
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        # Perform the request
        _headers = self._set_headers({
            "content-type": "application/json"
        })

        _req = requests.put(
            uri,
            headers=_headers,
            params=params,
            data=json.dumps(body),
            verify=self.__verify
        )

        # Raise an exception if the request failed
        _req.raise_for_status()

        # The request went through OK
        return True


    #
    # _api_post
    #
    def _api_post(
            self,
            uri: str = "",
            params: dict = {},
            body: dict = {},
            username: str = "",
            password: str = ""
    ) -> ST2_Response:
        '''
        A POST request 

        Args:
            uri (str): The URI for the API request
            params (dict): Query parameters for the request
            body (dict): The request body
            username (str): Name of user to authenticate to StackStorm
            password (str): Password for user to authenticate to StackStorm

        Returns:
            ST2_Response: Response from the ST2 API

        Raises:
            ValueError
                when uri is empty
                when body cannot be serialised
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        _headers = {
            "content-type": "application/json"
        }

        try:
            _body_json = json.dumps(body)
        except:
            raise ValueError("invalid body data")

        if username or password:
            # We might be trying to login
            _req = requests.post(
                uri,
                auth=(username, password),
                headers=_headers,
                params=params,
                data=_body_json,
                verify=self.__verify
            )
        else:
            # Perform the request
            _req = requests.post(
                uri,
                headers=self._set_headers(_headers),
                params=params,
                data=_body_json,
                verify=self.__verify
            )

        # Raise an exception if the request failed
        _req.raise_for_status()

        # The request went through OK
        return self._check_response(_req.json())


    #
    # _api_delete
    #
    def _api_delete(
            self,
            uri: str = "",
            params:dict = {}
    ) -> bool:
        '''
        A DELETE request

        Args:
            uri (str): The URI for the API request
            params (dict): Query parameters for the request

        Returns:
            boolean: True if successful, False or exception otherwise

        Raises:
            ValueError
                when uri is empty
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        # Perform the request
        _req = requests.delete(
            uri,
            headers=self._set_headers(),
            params=params,
            verify=self.__verify
        )

        # Raise an exception if the request failed
        _req.raise_for_status()

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

