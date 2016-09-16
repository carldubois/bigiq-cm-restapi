#!/usr/bin/env python
# -*- coding: utf-8 -*-

#@Author: Carl Dubois
#@Email: c.dubois@f5.com
#@Description: BIGIQ / BIGIP add to BIGIQ License Pool LTM
#@Product: BIGIQ
#@VersionIntroduced: 5.0.0

import sys
import simplejson as json
import base64
import string
import os.path
import httplib
import time

def base_license(config):
    print "\n"
    print '####Add a BIGIP to a BIGIQ license pool####'

    ## Connection to localhost:8100
    connection = httplib.HTTPConnection('localhost:8100')
    connection.set_debuglevel(0) # user can set debug level
    
    connection.connect()
    connection.request('GET', '/cm/shared/licensing/pools', None, config['headers'])
    response = connection.getresponse()
    j_out = json.loads(response.read())

    # Test current step to verify trust is complete.
    for item in j_out['items']:
        if item['baseRegKey'] == config['baseregkey']:
            member_uuid = item['uuid']
            break
    else:
        print "Unable to find base reg key provisioned on BIGIQ license management."
        sys.exit(1)
        
    lic_json = {"deviceAddress": config['bigip'],"username": config['username'],"password": config['password']}
        
    ## Request GET license pool
    connection.connect()
    connection.request('POST', '/cm/shared/licensing/pools/' + member_uuid + '/members', json.dumps(lic_json), config['headers'])
    
    ## Parse Response
    response = connection.getresponse()
    print response.status, response.reason
    j_pool = json.loads(response.read())

    time.sleep(1)
    if response.status in [200, 202]:
        print "POST to add device managed/unmanaged to licence pool with base reg key: " + config['baseregkey'] + " - SUCCESS"
    
    else:
        return False

    i=0
    while True:
        connection.connect()
        response = connection.request('GET', '/cm/shared/licensing/pools/' + member_uuid + '/members/' + j_pool['uuid'], None, config['headers'])
        response = connection.getresponse()
        j_str = json.loads(response.read())

        if j_str['deviceAddress'] == config['bigip']:
            if j_str['state'] == 'LICENSED':
                return True
                break
            elif j_str['state'] == 'FAILED':
                return False
                break    
            else:
                time.sleep(1)
                i+=1
                print "BIGIP Licence State = " + j_str['state'] + " expecting LICENSED: " + str(i)

if __name__ == '__main__':
    result = {}
    config = {}
    config['username'] = 'admin'
    config['password'] = 'admin'
    config['root_username'] = 'root'
    config['root_password'] = 'default'
    
    try:
        config['bigip'] = sys.argv[1]
    except:
        print "Please specify the BIGIP address in which you want to add to license pool provisioned on BIGIQ."
        sys.exit(1)
        
    try:
        config['baseregkey'] = sys.argv[2]
    except:
        print "Please tell me via command line the base reg key you wish to add the device too. Thank you"
        sys.exit(1)
    #==========================
    # Header used for httplib
    #==========================
    ## Header used in the connection request
    config['headers'] = {"Authorization"  : "Basic %s" % base64.b64encode(config['username'] + ':' + config['password']), "Content-Type"   : "application/json"}

    #==========================
    # device_trust
    #==========================
    result = base_license(config)
    
    if result == True:
        print "Add device to license reg pool - SUCCESS"
    else:
        print "Add device to license ref pool - FAIL"
        
