#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Store all the classes using for this project

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2022/6/20 08:48
- Copyright: Copyright © 2022 Rex Zhou. All rights reserved.
"""

__version__ = "0.0.2"

__author__ = "Rex Zhou"
__copyright__ = "Copyright © 2022 Rex Zhou. All rights reserved."
__credits__ = [__author__]
__license__ = "None"
__maintainer__ = __author__
__email__ = "879582094@qq.com"

import abc
import json
import os
import re
import socket
from urllib import parse

import requests
from fastapi import HTTPException
from fastapi.logger import logger
from requests.exceptions import ConnectTimeout


class APIBasic(abc.ABC):
    """Overall abstract class for API"""

    # The official docs URL
    DOCS_URL = ''
    # The official end point
    END_POINT = ''
    # The seconds for requests timeout
    TIME_OUT = int(os.environ.get("TIME_OUT", 20))

    def help(self) -> dict:
        """
        Print the official docs URL for help

        :return: Help message
        :rtype: dict
        """
        print(f'For more information, please visit: {self.DOCS_URL}')
        return {
            "message": f'For more information, please visit: {self.DOCS_URL}'
        }

    @staticmethod
    def check_fqdn(record: str) -> str:
        """
        Check if the record is match with FQDN
        Refer:
        https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch08s15.html

        :param record: The request record
        :type record: str
        :return: If not matched, return `notfqdn` key string else return ''
        :rtype: str
        """
        regex = r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$'
        if re.findall(regex, record):
            return ''
        return 'notfqdn'

    def check_end_point(self) -> str:
        """
        Check if the provider's end point hostname can be resolved

        :return: If can't resolved, return `badresolv` key string else return ''
        :rtype: str
        """
        hostname = parse.urlparse(self.END_POINT).hostname
        try:
            socket.gethostbyname_ex(hostname)
            return ''
        except socket.gaierror:
            return 'badresolv'

    def update_record(  # pylint: disable=no-self-use
        self,  # pylint: disable=too-many-arguments
        record: str,  # pylint: disable=unused-argument
        value: str,  # pylint: disable=unused-argument
        username: str,  # pylint: disable=unused-argument
        password: str) -> str:  # pylint: disable=unused-argument
        """
        The DSM 7.1 abstract method for DDNS service
        for more detail, visit:
        https://kb.synology.cn/zh-cn/DSM/help/DSM/AdminCenter/connection_ddns?version=7

        :param record: The record name of your CloudFlare DNS
        :type record: str
        :param value: The record value of your CloudFlare DNS
        :type value: str
        :param username: Username for authentication [Optional]
        :type username: str
        :param password: Password for authentication [Optional]
        :type password: str
        :return: Result string
        :rtype: str
        :author: Zhou Ruixi A.K.A Rex Chow
        :created: 2022-06-20 8:59 CST
        classes.APIAbstract.update_record
        """
        ...


class CloudFlare(APIBasic):
    """CloudFlare DDNS class"""

    DOCS_URL = 'https://api.cloudflare.com/'
    END_POINT = 'https://api.cloudflare.com/client/v4/'
    ENV_ZONE = 'CF_ZONE'
    ZONES_LINK = 'zones'
    RECORD_LINK = 'zones/{}/dns_records'
    UPDATE_LINK = 'zones/{}/dns_records/{}'

    def __init__(self):
        super().__init__()
        self.zone = os.environ.get(self.ENV_ZONE)
        self._zone_id = ''
        self._record_id = ''
        self.headers = {
            'Authorization': 'Bearer abcdefghijklmnopqrstuvwxyz',
            'Content-Type': 'application/json'
        }

    @property
    def zone_id(self) -> str:
        """
        Return the zone's id

        :return: Zone id
        :rtype: str
        """
        if self._zone_id:
            logger.info('Using cached zone id.')
            return self._zone_id
        url = parse.urljoin(self.END_POINT, self.ZONES_LINK)
        kwargs = {
            'url': url,
            'headers': self.headers,
            'params': {
                'name': self.zone
            },
            'timeout': self.TIME_OUT
        }
        try:
            response = requests.get(**kwargs)
        except ConnectTimeout:
            logger.error('Request time out!')
            raise HTTPException(
                408, detail=f"Can't get response from {self.END_POINT}"
            ) from ConnectTimeout
        if response.status_code == 403:
            msg = 'Token is invalid!'
            logger.critical(msg)
            raise HTTPException(403, detail=msg)
        self._zone_id = self._parse_response(response, self.zone)
        logger.info('Zone id has been cached.')
        if not self._zone_id:
            logger.critical("Can't get zone id!")
            raise EnvironmentError(
                f'Wrong zone environment variable: {self.zone}!')
        return self._zone_id

    @staticmethod
    def _parse_response(response, key: str) -> str:
        json_ = json.loads(response.content.decode('utf8'))
        logger.debug(json_)
        result = [_.get('id') for _ in json_.get('result', [{}])]
        if len(result) == 1:
            return result.pop()
        msg = f"Can't find ID of {key}!"
        logger.error(msg)
        return ''

    def _put_request(self, url: str, record: str, value: str):
        data = {
            "type": 'A',
            "name": record,
            "content": value,
            "ttl": 1,
            "proxied": False
        }
        logger.debug(data)
        kwargs = {
            'url': url,
            'data': json.dumps(data),
            'headers': self.headers,
            'timeout': self.TIME_OUT
        }
        try:
            response = requests.put(**kwargs)
        except ConnectTimeout:
            raise HTTPException(
                408,
                detail=f"Can't get response from {url}") from ConnectTimeout
        # Refer: https://api.cloudflare.com/#responses
        mapper = {
            200: 'good',
            400: 'badagent',
            401: 'badauth',
            403: 'badauth',
            405: 'badagent',
            415: 'badagent',
            429: 'abuse',
        }
        if result := mapper.get(response.status_code):
            return result
        return '911'

    def _pre_check(self, record: str):
        if result := self.check_end_point():
            return result
        if result := self.check_fqdn(record):
            return result
        return ''

    def get_record_id(self, record: str) -> str:
        """
        Get the record's id

        :param record: Record name
        :type record: str
        :return: Record ID
        :rtype: str
        """
        if self._record_id:
            logger.info('Using cached record id')
            return self._record_id
        url = parse.urljoin(self.END_POINT,
                            self.RECORD_LINK.format(self.zone_id))
        kwargs = {
            'url': url,
            'headers': self.headers,
            'params': {
                'name': record
            },
            'timeout': self.TIME_OUT
        }
        try:
            response = requests.get(**kwargs)
        except ConnectTimeout:
            return 'badconn'
        logger.info('Record id has been cached.')
        return self._parse_response(response, record)

    def update_record(self, record: str, value: str, username: str,
                      password: str) -> str:
        if result := self._pre_check(record):
            logger.warning('Pre check error: %s', result)
            return result
        logger.info('Arguments check passed.')
        self.zone = self.zone if self.zone and not username else username
        self.headers.update({'Authorization': f'Bearer {password}'})
        try:
            record_id = self.get_record_id(record)
        except HTTPException as error:
            mapper = {
                403: 'badauth',  # Authenticate error
                408: 'badconn'  # Time out error
            }
            return mapper.get(error.status_code, '911')
        except EnvironmentError:
            # Wrong domain error
            return 'nohost'
        link = self.UPDATE_LINK.format(self.zone_id, record_id)
        url = parse.urljoin(self.END_POINT, link)
        result = self._put_request(url, record, value)
        logger.info('Update successful.')
        return result
