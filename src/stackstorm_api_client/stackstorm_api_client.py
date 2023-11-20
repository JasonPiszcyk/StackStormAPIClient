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
    # Attributes

    # Private Attributes
    __api_host = "localhost"
    __auth_token = None
    __api_key = None
    __verify = True
    __authenticated = False


    #
    # __init__
    #
    def __init__(self, *args, host=None, api_key=None, username=None,
                 password=None, verify=True, **kwargs):
        ''' Init method for class '''
        super().__init__(*args, **kwargs)

        if host: self.__api_host = host
        self.__verify = verify
        if not self.__verify: urllib3.disable_warnings()

        if api_key:
            self.__api_host = api_key
        elif username or password:
            # Try to login
            self.login(
                host=self.__api_host,
                username=username,
                password=password,
            )


    ###########################################################################
    #
    # Auth Methods
    #
    ###########################################################################
    #
    # login
    #
    def login(self, host=None, username=None, password=None):
        '''
        Login to the StackStorm API

        Parameters:
            host: The host of the StackStorm API
            username: Name of user to authenticate to StackStorm
            password: Password for user to authenticate to StackStorm

        Return Value:
            bool: True if successful, False otherwise
        '''
        if not username:
            raise ValueError("'username' argument must be supplied")

        if not password:
            raise ValueError("'password' argument must be supplied")

        api_host = host if host else self.__api_host
        uri = f"https://{api_host}/auth/v1/tokens"

        try:
            resp_dict = self.__api_post(uri=uri, username=username, password=password)
        except requests.exceptions.HTTPError:
            return

        if "token" in resp_dict:
            # Store the host/login info
            self.__api_host = api_host
            self.__auth_token = resp_dict["token"]
            self.__authenticated = True


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
        return self.__authenticated


    ###########################################################################
    #
    # Access Methods
    #
    ###########################################################################
    #
    # __make_uri
    #
    def __make_uri(self, path=None):
        '''
        Generate a URI from info

        Parameters:
            path: The API path to query

        Return Value:
            string: The URI
        '''
        if not path:
            path = "/"
        
        uri = f"https://{self.__api_host}{path}"
        
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
        uri = self.__make_uri(path=path)

        return self.__api_get(uri=uri, params=params)


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
        uri = self.__make_uri(path=path)

        return self.__api_post(uri=uri, params=params, body=body)


    #
    # post
    #
    def post(self, path=None, params={}):
        '''
        A simple POST request

        Parameters:
            path: The API path to query
            params: Query parameters for the request

        Return Value:
            dict: Response from the query
        '''
        uri = self.__make_uri(path=path)

        return self.__api_post(uri=uri, params=params)


    #
    # get
    #
    def get(self, path=None, params={}):
        '''
        A simple DELETE request

        Parameters:
            path: The API path to query
            params: Query parameters for the request

        Return Value:
            boolean: True if successful, False or exception otherwise
        '''
        uri = self.__make_uri(path=path)

        return self.__api_get(uri=uri, params=params)


    ###########################################################################
    #
    # API Access Functions
    #
    ###########################################################################
    #
    # __set_header
    #
    def __set_header(self, headers=None):
        '''
        Set the request header based on 

        Parameters:
            header: An existing header to update

        Return Value:
            dict: The header after modification
        '''
        if not headers:
            headers = {}
        
        if self.__api_key:
            headers.update({"St2-Api-Key": self.__api_key})
        elif self.__auth_token:
            headers.update({"X-Auth-Token": self.__auth_token})
        
        return headers


    #
    # __api_get
    #
    def __api_get(self, uri=None, params={}):
        '''
        A GET request

        Parameters:
            uri: The URI for the API request
            params: Query parameters for the request

        Return Value:
            dict: Response converted to a dictionary
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        # Perform the request
        headers = self.__set_header()
        req = requests.get(
            uri,
            headers=headers,
            params=params,
            verify=self.__verify
        )

        # Raise an exception if the request failed
        req.raise_for_status()

        # Return the info from the request
        req_dict = json.loads(req.text)
        return req_dict


    #
    # __api_put
    #
    def __api_put(self, uri=None, params={}, body={}):
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
        headers = self.__set_header()
        req = requests.put(
            uri,
            headers=headers,
            params=params,
            data=json.dumps(body),
            verify=self.__verify
        )

        # Raise an exception if the request failed
        req.raise_for_status()

        # The request went through OK
        return True


    #
    # __api_post
    #
    def __api_post(self, uri=None, params={}, username=None, password=None):
        '''
        A POST request 

        Parameters:
            uri: The URI for the API request
            params: Query parameters for the request
            username: Name of user to authenticate to StackStorm
            password: Password for user to authenticate to StackStorm

        Return Value:
            dict: The response as a dictionary
        '''
        if not uri:
            raise ValueError("'uri' argument must be supplied")

        if username or password:
            # We might be trying to login
            req = requests.post(
                uri,
                auth=(username, password),
                params=params,
                verify=self.__verify
            )
        else:
            # Perform the request
            headers = self.__set_header()
            req = requests.post(
                uri,
                headers=headers,
                params=params,
                verify=self.__verify
            )

        # Raise an exception if the request failed
        req.raise_for_status()

        # The request went through OK
        req_dict = json.loads(req.text)
        return req_dict


    #
    # __api_delete
    #
    def __api_delete(self, uri=None, params={}):
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
        headers = self.__set_header()
        req = requests.delete(
            uri,
            headers=headers,
            params=params,
            verify=self.__verify
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

