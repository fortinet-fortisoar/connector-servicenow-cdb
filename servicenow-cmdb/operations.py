""" Copyright start
  Copyright (C) 2008 - 2023 Fortinet Inc.
  All rights reserved.
  FORTINET CONFIDENTIAL & FORTINET PROPRIETARY SOURCE CODE
  Copyright end """

import requests, json
from connectors.core.connector import ConnectorError, get_logger

logger = get_logger('servicenow-cmdb')


class Servicenow(object):
    def __init__(self, config, *args, **kwargs):
        self.username = config.get('username')
        self.password = config.get('password')
        url = config.get('server_url').strip('/')
        if not url.startswith('https://') and not url.startswith('http://'):
            self.url = 'https://{0}/api/now'.format(url)
        else:
            self.url = url + '/api/now'
        self.verify_ssl = config.get('verify_ssl')

    def make_rest_call(self, url, method, data=None, params=None):
        try:
            url = self.url + url
            headers = {
                'Accept': 'application/json'
            }
            logger.debug("Endpoint {0}".format(url))
            response = requests.request(method, url, data=data, params=params, auth=(self.username, self.password),
                                        headers=headers,
                                        verify=self.verify_ssl)
            logger.debug("response_content {0}:{1}".format(response.status_code, response.content))
            if response.ok or response.status_code == 204:
                logger.info('Successfully got response for url {0}'.format(url))
                if 'json' in str(response.headers):
                    return response.json()
                else:
                    return response
            elif response.status_code == 404:
                return response
            else:
                logger.error("{0}".format(response.status_code))
                raise ConnectorError("{0}:{1}".format(response.status_code, response.content))
        except requests.exceptions.SSLError:
            raise ConnectorError('SSL certificate validation failed')
        except requests.exceptions.ConnectTimeout:
            raise ConnectorError('The request timed out while trying to connect to the server')
        except requests.exceptions.ReadTimeout:
            raise ConnectorError(
                'The server did not send any data in the allotted amount of time')
        except requests.exceptions.ConnectionError:
            raise ConnectorError('Invalid Credentials')
        except Exception as err:
            raise ConnectorError(str(err))


def check_payload(payload):
    updated_payload = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            nested = check_payload(value)
            if len(nested.keys()) > 0:
                updated_payload[key] = nested
        elif value != '' and value is not None:
            updated_payload[key] = value
    return updated_payload


def create_configuration_item(config, params):
    sn = Servicenow(config)
    endpoint = '/cmdb/instance/{0}'.format(params.pop('class_name'))
    payload = check_payload(params)
    response = sn.make_rest_call(endpoint, 'POST', data=json.dumps(payload))
    return response


def get_configuration_items(config, params):
    sn = Servicenow(config)
    endpoint = '/cmdb/instance/{0}'.format(params.pop('class_name'))
    payload = check_payload(params)
    response = sn.make_rest_call(endpoint, 'GET', params=payload)
    return response


def get_configuration_item_details(config, params):
    sn = Servicenow(config)
    endpoint = '/cmdb/instance/{0}/{1}'.format(params.get('class_name'), params.get('sys_id'))
    response = sn.make_rest_call(endpoint, 'GET')
    return response


def update_configuration_item(config, params):
    sn = Servicenow(config)
    endpoint = '/cmdb/instance/{0}/{1}'.format(params.pop('class_name'), params.pop('sys_id'))
    payload = check_payload(params)
    response = sn.make_rest_call(endpoint, 'PUT', data=json.dumps(payload))
    return response


def add_relation_to_configuration_item(config, params):
    sn = Servicenow(config)
    endpoint = '/cmdb/instance/{0}/{1}/relation'.format(params.pop('class_name'), params.pop('sys_id'))
    payload = check_payload(params)
    response = sn.make_rest_call(endpoint, 'POST', data=json.dumps(payload))
    return response


def delete_relation_for_configuration_item(config, params):
    sn = Servicenow(config)
    endpoint = '/cmdb/instance/{0}/{1}/relation/{2}'.format(params.pop('class_name'), params.pop('sys_id'),
                                                            params.pop('rel_sys_id'))
    response = sn.make_rest_call(endpoint, 'DELETE')
    return response


def login(config, params):
    sn = Servicenow(config)
    endpoint = sn.url + "/attachment"
    headers = {
        'Accept': 'application/json'
    }
    response = requests.request(method='GET', url=endpoint, params=params,
                                auth=(config.get('username'), config.get('password')), headers=headers,
                                verify=config.get('verify_ssl'))
    return response


def _check_health(config):
    try:
        response = login(config, params={'sysparm_limit': 1})
        if response.ok:
            return True
        else:
            raise ConnectorError('Invalid Credentials!')
    except Exception as err:
        raise ConnectorError('Invalid Credentials!')


operations = {
    'create_configuration_item': create_configuration_item,
    'get_configuration_items': get_configuration_items,
    'get_configuration_item_details': get_configuration_item_details,
    'update_configuration_item': update_configuration_item,
    'add_relation_to_configuration_item': add_relation_to_configuration_item,
    'delete_relation_for_configuration_item': delete_relation_for_configuration_item
}
