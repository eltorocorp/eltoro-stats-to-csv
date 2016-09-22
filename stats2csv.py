#/usr/bin/python

import requests, sys, ast
from datetime import date,timedelta

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
baseUrl = 'https://api-prod.eltoro.com'

#dev gateway
#baseUrl = 'https://api-dev.eltoro.com'

login_resp = requests.post(baseUrl + '/users/login', login)

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
    user_resp = requests.get(baseUrl + '/users/' + user_id, headers=headers)
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
orgs = [org_id]

orgs_resp = requests.get(baseUrl + '/orgs', headers=headers)
for org in orgs_resp.json():
    if org_id in org['parents']:
        orgs.push(org['_id'])

#Print column headings
fields = ['_id',
        'campaignId',
        'orgId',
        'targetType',
        'creativeType',
        'name',
        'campaignName',
        'refId',
        'start',
        'stop'
        ]
row1 = ''
for f in fields:
    row1 += f + ','
row1 = row1[:-1]
for i in range(0, 24):
    row1 += ',clicks' + str(i) + ',imps' + str(i)
print row1

#Write a row for each orderline belonging to each org
for org in orgs:
    ol_query = '/orderlines?orgId=' + org_id
    ols = requests.get(baseUrl + ol_query, headers=headers).json()
    for ol in ols:
        if 'campaign' in ol.keys() and 'name' in ol['campaign'].keys():
            ol['campaignName'] = ol['campaign']['name']
        stats_query = (
            '/stats?start=' +
            start +
            '&stop=' +
            stop +
            '&granularity=' +
            granularity+
            '&orgId=' +
            org_id +
            '&campaignId=' +
            '&orderLineId=' +
            ol['_id']
        )
        stats = requests.get(baseUrl + stats_query).json()
        data = ""
        for hour in stats:
            data += str(hour['clicks']) + ',' + str(hour['imps']) + ','
        field_list = ''
        for f in fields:
            if f in ol.keys():
                if type(ol[f]) == 'str':
                    field_list += ol[f] + ','
                else:
                    field_list += str(ol[f]) + ','
            else:
                field_list += ','
        print field_list + data


sys.exit()
print baseUrl + stats_query
print headers

try:
    raw = ast.literal_eval(stats_resp.text)
    print granularity + ',clicks,imps'
    for result in raw:
        print result['start_date'] + ',' + str(result['clicks']) + ',' + str(result['imps'])
except KeyError:
    print "There was an error, please check your arguments and try again."
    print stats_resp.text
except TypeError:
    print "Your query returned no results. please check your arguments and try again."

