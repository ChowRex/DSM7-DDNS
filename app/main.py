#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point to using CloudFlare

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2022/6/20 08:48
- Copyright: Copyright © 2022 Rex Zhou. All rights reserved.
"""

__version__ = "0.0.1"

__author__ = "Rex Zhou"
__copyright__ = "Copyright © 2022 Rex Zhou. All rights reserved."
__credits__ = [__author__]
__license__ = "None"
__maintainer__ = __author__
__email__ = "879582094@qq.com"

import logging
import os

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.logger import logger

from utils import classes

level = getattr(logging, str(os.environ.get('LOG_LEVEL', 'INFO')).upper())
logging.basicConfig(level=level)
logger.info('Log level: %s', level)
app = FastAPI()
supports = {'cloudflare': classes.CloudFlare()}


# Why use GET method?
# Synology using it for update record.
# Refer:
# https://www.pubyun.com/wiki/%E5%B8%AE%E5%8A%A9:api
# https://www.noip.com/integrate/request
@app.get("/update")
@app.post("/update")
async def update(record: str = None,
                 value: str = None,
                 username: str = None,
                 password: str = None,
                 provider: str = 'cloudflare') -> PlainTextResponse:
    """
    Refer: https://github.com/joshuaavalon/SynologyCloudflareDDNS
    # source /etc.defaults/ddns_provider.conf
        good -  Update successfully.
        nochg - Update successfully but the IP address have not changed.
        nohost - The hostname specified does not exist in this user account.
        abuse - The hostname specified is blocked for update abuse.
        notfqdn - The hostname specified is not a fully-qualified domain name.
        badauth - Authenticate failed.
        911 - There is a problem or scheduled maintenance on provider side
        badagent - The user agent sent bad request(like HTTP method/parameters is not permitted)
        badresolv - Failed to connect to  because failed to resolve provider address.
        badconn - Failed to connect to provider because connection timeout.

    :param record: The name of dns record
    :type record: str
    :param value: The value of dns record
    :type value: str
    :param username: The username for auth
    :type username: str
    :param password: The password for auth
    :type password: str
    :param provider: The name of domain provider, supports: { cloudflare | ... }
    :type provider: str
    :return: Result string
    :rtype: Response
    """
    kwargs = {
        'record': record,
        'value': value,
        'username': username,
        'password': password,
    }
    if not all(kwargs.values()):
        return PlainTextResponse('nohost')
    cli = supports[provider]
    result = cli.update_record(**kwargs)
    return PlainTextResponse(result)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app='main:app',
                host="127.0.0.1",
                port=8000,
                reload=True,
                debug=True)
