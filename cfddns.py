#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (C) 2013 Tiago Dias

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import requests
import os
import logging

''' Make a request to the CloudFlare API '''
def api_request(action, **kwargs):
	data = {
		'tkn': config['apikey'],
		'email': config['email'],
		'a': action
	}
	data = dict(data.items() + kwargs.items())
	
	r = requests.post('https://www.cloudflare.com/api_json.html', data=data)
	
	# Some requests versions use r.json and some use r.json()
	json = r.json
	try:
		json.__getitem__
	except AttributeError:
		json = r.json()
	
	if json['result'] != 'success':
		raise Exception(json['msg'])
	else:
		return json['response']

''' Get the machine's external IP '''
def external_ip():
	r = requests.get('http://my-ip.heroku.com/')
	
	if r.status_code != 200:
		raise Exception(r.text)
	else:
		return r.text.replace('\n', '')

def main():
	# Get the configurations from the config file
	globals()['config'] = {}
	execfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.py'), config)

	# Set up logging
	logging.basicConfig(
		format='%(asctime)s [%(levelname)s] %(message)s',
		datefmt='%Y/%m/%d %H:%M:%S',
		level=getattr(logging, config['loglevel']))

	# Disable requests INFO messages
	logging.getLogger('requests').setLevel(logging.WARNING)
	
	# Get the machine's external IP
	config['ext_ip'] = external_ip()

	logging.info('Requesting list of records...')
	# Get the list of records
	records = api_request('rec_load_all', z = config['zone'])['recs']['objs']
	
	# Iterate over every records, and change the specified ones
	for record in records:
		if (record['type'] == 'A') and (record['display_name'] in config['domains']):
			if  (record['content'] == config['ext_ip']) and (record['ttl'] == str(config['ttl'])):
				# Change is not necessary - The IP and config['ttl'] are good.
				logging.info('%s doesn\'t need any change.' % record['name'])
			else:
				# Change is necessary
				logging.info('Changing record %s...' % record['name'])
				api_request('rec_edit',
					z = config['zone'],
					id = record['rec_id'],
					type = record['type'],
					name = record['name'],
					ttl = config['ttl'],
					content = config['ext_ip'])

if __name__ == '__main__':
	main()
