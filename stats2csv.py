#/usr/bin/python

import requests, sys, ast
from datetime import date,timedelta

# Functions
def get_orgs(org_id):
    _orgs = [org_id]
    orgs_resp = requests.get(base_url + '/orgs', headers=headers)
    for org in orgs_resp.json():
        if org_id in org['parents']:
            _orgs.push(org['_id'])
    return _orgs

def get_collection(collection, org_list):
    result = []
    for org in org_list:
        query = '/' + collection + '?orgId=' + org
        coll = requests.get(base_url + query, headers=headers).json()
        result += coll
    return result

def stats_query(ids):
    query = (
        '/stats?start=' +
        start +
        '&stop=' +
        stop +
        '&granularity=' +
        granularity+
        '&orgId=' +
        org_id +
        '&campaignId=' + ids['campaigns'] +
        '&orderLineId=' + ids['orderlines'] +
        '&ceativeId=' + ids['creatives']
    )
    r = requests.get(base_url + query).json()
    return r

def build_ids(level, _id):
    ids = {
        'campaigns': '',
        'orderlines': '',
        'creatives': '',
        }
    ids[level] = _id;
    return ids

def buildCSV(level):
    return

def writeCSV(data):
    return

# Parse arguments
try:
    try:
        start = sys.argv[3]
    except:
        start = str(date.today() - timedelta(days=1))#+" 00:00:00"
    try:
        stop = sys.argv[4]
    except:
        stop = str(date.today() - timedelta(days=1))#+" 23:59:59"
    try:
        granularity = sys.argv[5]
    except:
        granularity = "hour"
    user = sys.argv[1]  # Hard Code username here if you do not wish to enter it on the command line
    passw = sys.argv[2] # Hard Code password here if you do not wish to enter it on the command line

except IndexError:
    print 'Usage:\n\n  python stats2csv <username> <password> <start (optional)> <end (optional)> <granularity (optional)> <org id (optional)>'
    print ""
    print "If dates or granularity are left off, it defaults to 'yesterday' (if run right now : "+ start +" thru  " + stop +") with a granularity timeframe of '"+granularity+"'"
    print "username/password are required fields, unless you have hard coded them into this script"
    print "-- This script should be in a cron/scheduled task to run daily at at least 2am PST, or 5am EST to ensure yesterday stats are updated --"
    sys.exit()

try:
    org_id = sys.argv[6]
except IndexError:
    org_id = 'not set'


login = { 'username': user, 'password': passw }

#Prod gateway
base_url = 'https://api-prod.eltoro.com'

#dev gateway
#base_url = 'https://api-dev.eltoro.com'

login_resp = requests.post(base_url + '/users/login', login)

try:
    token = login_resp.json()[unicode('token')]
    user_id = login_resp.json()[unicode('id')]
except KeyError:
    print 'Login error, check your credentials\n'
    print login_resp.text
    sys.exit()

headers = {
    "Authorization": ("Bearer " + str(token))
}

if org_id == 'not set':
    user_resp = requests.get(base_url + '/users/' + user_id, headers=headers)
    try:
        orgs = user_resp.json()[unicode('roles')].keys()
    except:
        print "Please provide an org id as the last argument"
        sys.exit()
    if len(orgs) == 1:
        org_id = str(orgs[0])
    else:
        print "You belong to multiple orgs. Please provide an org id as the last argument"
        sys.exit()

#get list of orderlines

#make a list of orgs and suborgs
orgs = get_orgs(org_id)

#Print column headings
#  [ <key>, <label> ]#
fields = {
    'orderlines': [
        ['_id', '"orderlineId"'],
        ['campaignId','"campaignId"'],
        ['orgId','"orgId"'],
        ['targetType','"targetType"'],
        ['creativeType','"creativeType"'],
        ['name','"OrdName"'],
        ['campaignName','"campaignName"'],
        ['refId','"refId"'],
        ['start','"start"'],
        ['stop','"stop"'],
    ],
    'campaigns': [
        ['_id', 'campaignId']
    ],
    'creatives': [
        ['_id', 'creativeId']
    ],
}

for level in ['orderlines', 'campaigns', 'creatives']:
    row1 = ''
    for f in fields[level]:
        row1 += f[1] + ','
    row1 = row1[:-1]
    for i in range(0, 24):
        row1 += ',"clicks' + str(i) + '","imps' + str(i) + '"'
    print row1
    row1 = ''

    #Write a row for each orderline belonging to each org
    colls = get_collection(level, orgs)
    for coll in colls:
        ids = build_ids(level, coll['_id'])
        stats = stats_query(ids)
        data = ""
        for hour in stats:
            data += str(hour['clicks']) + ',' + str(hour['imps']) + ','
        field_list = ''
        for f in fields[level]:
            if f[0] in coll.keys():
                if type(coll[f[0]]) in [unicode, str]:
                    field_list += '"' + coll[f[0]] + '",'
                else:
                    field_list += str(coll[f[0]]) + ','
            else:
                field_list += ','
        print field_list + data


sys.exit()
