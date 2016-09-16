#!/usr/bin/env python
# -*- coding: utf-8 -*-

#@Author: Carl Dubois
#@Email: c.dubois@f5.com
#@Description: BIGIQ / BIGIP Trust and Discover LTM
#@Product: BIGIQ
#@VersionIntroduced: 5.0.0

import sys
import simplejson as json
import base64
import string
import os.path
import httplib
import time

def device_trust(config):
    print "\n"
    print '####Begin a trust task between BIGIQ and BIGIP####'

    ## Connection to localhost:8100
    connection = httplib.HTTPConnection('localhost:8100')
    connection.set_debuglevel(0) # user can set debug level
    
    ## Request DATA
    data = {'address':config['bigip'],'userName':'admin', 'password':'admin', 'clusterName':'', 'useBigiqSync':'false'}

    ## Request POST
    connection.request('POST', '/cm/global/tasks/device-trust', json.dumps(data), config['headers'])

    ## Parse Response
    response = connection.getresponse()
    print response.status, response.reason
    print response.read()

    time.sleep(1)
    if response.status in [200, 202]:
        print "Trust task successfully started."
    else:
        return False

    ## get status of task

    t=1
    while True:
        connection.connect()
        connection.request('GET', '/cm/global/tasks/device-trust', None, config['headers'])
        response = connection.getresponse()
        j_out = json.loads(response.read())

        # Test current step to verify trust is complete.
        for item in j_out['items']:
            if item['address'] == config['bigip']:
                if item['currentStep'] == 'DONE':
                    return True, item['machineId']
                else:
                    print str(t) + " sec"
                    time.sleep(1)
                    t+=1
                    continue
        # If not DONE is 30 sec fail.
        if t>=30:
            return False

def device_discover(config, devid, adc=None, afm=None, asm=None):
    print "\n"
    print '####Discover modules selected LTM, AFM, ASM via resource BIGIP####'

    ## Connection to localhost:8100
    connection = httplib.HTTPConnection('localhost:8100')
    connection.set_debuglevel(0) # user can set debug level

    ## Reference link to BIGIP
    link = 'cm/system/machineid-resolver/' + devid

    ## Request DATA
    adc_data = {'deviceReference': {"link": link}, 'moduleList': [{'module': 'adc_core'}], 'userName': config['username'], 'password': config['password'], 'rootUser': config['root_username'], 'rootPassword' : config['root_password'], 'automaticallyUpdateFramework' : 'true'}
    adc_afm_data = {'deviceReference': {"link": link}, 'moduleList': [{'module': 'adc_core'}, {'module': 'firewall'},{'module': 'security_shared'}], 'userName': config['username'], 'password': config['password'], 'rootUser': config['root_username'], 'rootPassword' : config['root_password'], 'automaticallyUpdateFramework' : 'true'}
    adc_asm_data = {'deviceReference': {"link": link}, 'moduleList': [{'module': 'adc_core'}, {'module': 'asm'},{'module': 'security_shared'}], 'userName': config['username'], 'password': config['password'], 'rootUser': config['root_username'], 'rootPassword' : config['root_password'], 'automaticallyUpdateFramework' : 'true'}
    all_data = {'deviceReference': {"link": link}, 'moduleList': [{'module': 'adc_core'}, {'module': 'firewall'}, {'module': 'asm'},{'module': 'security_shared'}], 'userName': config['username'], 'password': config['password'], 'rootUser': config['root_username'], 'rootPassword' : config['root_password'], 'automaticallyUpdateFramework' : 'true'}

    ## Request POST
    if config['module'] == 'adc':
        connection.request('POST', '/cm/global/tasks/device-discovery', json.dumps(adc_data), config['headers'])
    elif config['module'] == 'afm':
        connection.request('POST', '/cm/global/tasks/device-discovery', json.dumps(adc_afm_data), config['headers'])
    elif config['module'] == 'asm':
        connection.request('POST', '/cm/global/tasks/device-discovery', json.dumps(adc_asm_data), config['headers'])
    elif config['module'] == 'all':
        connection.request('POST', '/cm/global/tasks/device-discovery', json.dumps(all_data), config['headers'])
    else:
        print "Module {0} is not avalible.".format(config['module'])
        return False

    ## Parse Response
    response = connection.getresponse()
    print response.status, response.reason
    print response.read()

    time.sleep(1)
    if response.status in [200, 202]:
        print "Device discover task successfully started."
    else:
        return False

    ## Get status of task
    t=1
    while True:
        connection.connect()
        connection.request('GET', '/cm/global/tasks/device-discovery', None, config['headers'])
        response = connection.getresponse()
        j_out = json.loads(response.read())

        # Test current step to verify trust is complete.
        for item in j_out['items']:
            if item['deviceReference']['link'] == link and item['status'] == 'STARTED':
                time.sleep(1)

        if t>=40:
            return True
        else:
            t+=1
            print str(t) + " sec"

def device_import(config, devid):
    print "\n"
    print '####Import module configuration selected LTM, AFM, ASM via resource BIGIP####'
    uri = []

    ## Connection to localhost:8100
    connection = httplib.HTTPConnection('localhost:8100')
    connection.set_debuglevel(0) # user can set debug level

    ## Reference link to BIGIP
    link = 'cm/system/machineid-resolver/' + devid
    data = {'deviceReference': {'link': link}, 'uuid': devid, 'deviceUri': 'http://' + config['bigip'] + ':443', 'machineId': devid}

    if config['module'] == 'afm':
        print "ADC and AFM import"
        uri_adc = '/cm/adc-core/tasks/declare-mgmt-authority'
        uri.append(uri_adc)
        uri_afm = '/cm/firewall/tasks/declare-mgmt-authority'
        uri.append(uri_afm)
    elif config['module'] == 'asm':
        print "ADC and ASM import"
        uri_adc = '/cm/adc-core/tasks/declare-mgmt-authority'
        uri.append(uri_adc)
        uri_asm = '/cm/asm/tasks/declare-mgmt-authority'
        uri.append(uri_asm)
    else:
        print "ADC, AFM and ASM import"
        uri_adc = '/cm/adc-core/tasks/declare-mgmt-authority'
        uri.append(uri_adc)
        uri_afm = '/cm/firewall/tasks/declare-mgmt-authority'
        uri.append(uri_afm)
        uri_asm = '/cm/asm/tasks/declare-mgmt-authority'
        uri.append(uri_asm)

    ## POST
    for i in range(len(uri)):
        connection.request('POST', uri[i], json.dumps(data), config['headers'])

        ## Parse Response
        response = connection.getresponse()
        print response.status, response.reason
        print response.read()
        
        time.sleep(1)
        if response.status in [200, 202]:
            print "Device import task successfully started."
        else:
            return False

        ## Get status of task
        t=1
        flag=0
        while True:
            connection.connect()
            connection.request('GET', uri[i], None, config['headers'])
            response = connection.getresponse()
            j_out = json.loads(response.read())
            
            # Test current step to verify trust is complete.
            for item in j_out['items']:
                if item['deviceIp'] == config['bigip']:
                    if item['currentStep'] == 'DONE':
                        flag=1
                    else:
                        print str(t) + " sec"
                        time.sleep(1)
                        t+=1
                        continue
            # If not DONE is 60 sec fail.
            if flag==1:
                break
            elif t==60:
                return False
    return True


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
        print "Please specify the BIGIP address in which you want to form trust. ex. ./discover.py x.x.x.x"
        sys.exit(1)

    try:
        config['module'] = sys.argv[2]
    except:
        print "Please tell me via command line which BIGIP module you wish to discover. Thank you"
        sys.exit(1)
    #==========================
    # Header used for httplib
    #==========================
    ## Header used in the connection request
    config['headers'] = {"Authorization"  : "Basic %s" % base64.b64encode(config['username'] + ':' + config['password']), "Content-Type"   : "application/json"}

    #==========================
    # device_trust
    #==========================
    result_trust = device_trust(config)
    
    #==========================
    # device_discovery
    #==========================
    result_discovery = device_discover(config, result_trust[1])

    #==========================
    # ltm_import
    #==========================
    result_import = device_import(config, result_trust[1])

    if result_trust[0] == True and result_discovery == True and result_import == True:
        print "Trust,  Discovery and Import successfully established."
    else:
        print "Trust and Discovery failed to establish"
        
