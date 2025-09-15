#!/usr/bin/env python3
'''
Stackstorm ST2 API Tests

Copyright (C) 2025 Jason Piszcyk
Email: Jason.Piszcyk@gmail.com

All rights reserved.

This software is private and may NOT be copied, distributed, reverse engineered,
decompiled, or modified without the express written permission of the copyright
holder.

The copyright holder makes no warranties, express or implied, about its 
suitability for any particular purpose.
'''

# System Imports
import pytest
# import json
import requests

# Our Module Imports
import stackstorm_api_client
import configparser

#
# Globals
#
ST2_CFG_FILE = "/tmp/st2_config"

###########################################################################
#
# Start the tests...
#
###########################################################################
#
# read in auth info
#
api_host = "https://localhost"
api_key = ""
username = ""
password = ""

st2cfg = configparser.ConfigParser()
st2cfg.read(ST2_CFG_FILE)

if "stackstorm" in st2cfg:
    if "api_host" in st2cfg["stackstorm"]:
        api_host = st2cfg["stackstorm"]["api_host"]


if "credentials" in st2cfg:
    if "api_key" in st2cfg["credentials"]:
        api_key = st2cfg["credentials"]["api_key"]

    if "user" in st2cfg["credentials"]:
        username = st2cfg["credentials"]["user"]

    if "password" in st2cfg["credentials"]:
        password = st2cfg["credentials"]["password"]


def test_without_auth_validation():
    # Correct API Key
    st2 = stackstorm_api_client.StackStormAPIClient(
        uri=api_host,
        api_key=api_key,
        verify=False, 
        validate_api_key=False
    )
    assert st2.authenticated

    x = st2.get("/api/v1") 
    assert isinstance(x, dict)
    assert str(x["version"]) == "3.8.0"

    # Wrong API Key
    st2 = stackstorm_api_client.StackStormAPIClient(
        uri=api_host,
        api_key="junk",
        verify=False,
        validate_api_key=False
    )
    assert st2.authenticated

    with pytest.raises(requests.exceptions.HTTPError):
        x =  st2.get("/api/v1") 


def test_user_password():
    # Invalid password
    st2 = stackstorm_api_client.StackStormAPIClient(
        uri=api_host,
        username=username,
        password="invalid",
        verify=False
    )
    assert not st2.authenticated

    # Invalid username
    st2 = stackstorm_api_client.StackStormAPIClient(
        uri=api_host,
        username="some_guy_here23",
        password=password,
        verify=False
    )
    assert not st2.authenticated

    # Correct username and password
    st2 = stackstorm_api_client.StackStormAPIClient(
        uri=api_host,
        username=username,
        password=password,
        verify=False
    )
    assert st2.authenticated


def test_api_key():
    # Invalid key
    st2 = stackstorm_api_client.StackStormAPIClient(
        uri=api_host,
        api_key="junk",
        verify=False
    )
    assert not st2.authenticated

    # Correct API Key
    st2 = stackstorm_api_client.StackStormAPIClient(
        uri=api_host,
        api_key=api_key,
        verify=False
    )
    assert st2.authenticated


def test_method():
    # do a get call 
    st2 = stackstorm_api_client.StackStormAPIClient(
        uri=api_host,
        api_key=api_key,
        verify=False
    )
    assert st2.authenticated

    x =  st2.get("/api/v1") 
    assert isinstance(x, dict)
    assert str(x["version"]) == "3.8.0"
