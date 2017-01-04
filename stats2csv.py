#/usr/bin/python

import requests, sys, ast
from datetime import date,timedelta,datetime

#Prod gateway
base_url = 'https://api-prod.eltoro.com'

#dev gateway
#base_url = 'https://api-dev.eltoro.com'

# Functions
def get_orgs(org_id):
    _orgs = [org_id]
    orgs_resp = requests.get(base_url + '/orgs', headers=headers)
    for org in orgs_resp.json()['results']:
        if org_id in org['parents']:
            _orgs.append(org['_id'])
    return _orgs

def valid_campaign_list(org_list):
    result = []
    for org in org_list:
        query = '/campaigns?orgId=' + org
        coll = requests.get(base_url + query, headers=headers).json()['results']
        for c in coll:
            if c['status'] == 20 or c['status'] == 99 and c["stop"] :
                result.append(c['_id'])
    return result;


def valid_ol_list(org_list, camp_id_list):
    result = []
    for org in org_list:
        query = '/orderLines?orgId=' + org
        coll = requests.get(base_url + query, headers=headers).json()['results']
        for c in coll:
            if c['campaignId'] in camp_id_list:
                result.append(c['_id'])
    return result;


def get_campaigns(org_list):
    collection = "campaigns"
    result = []
    suffix = '&pagingLimit=10'
    for org in org_list:
        page = 1
        query = '/' + collection + '?orgId=' + org + suffix
        resp = requests.get(base_url + query + '&pagingPage=' + str(page), headers=headers).json()
        coll = resp['results']
        paging = resp['paging']
        while paging['total'] > paging['limit'] * page:
            page += 1
            resp = requests.get(base_url + query + '&pagingPage=' + str(page), headers=headers).json()
            coll += resp['results']

        ## Filter for only active within last 7 days
        recentdate = date.today() - timedelta(days=7)
        for c in coll:
            try:
                if c['status'] == 20 or c['status'] == 99:# and c["stop"] > recentdate :
                    result.append(c)
            except:
                pass
    return result


def get_orderLines(campaigns):
    collection = "orderLines"
    ols = []
    creatives=[]
    suffix = '&pagingLimit=10'
    page = 1
    query = '/' + collection + "?" + suffix
    resp = requests.get(base_url + query + '&pagingPage=' + str(page), headers=headers).json()
    coll = resp['results']
    paging = resp['paging']
    while paging['total'] > paging['limit'] * page:
        page += 1
        resp = requests.get(base_url + query + '&pagingPage=' + str(page), headers=headers).json()
        coll += resp['results']
    allols = coll

    for c in allols:
        for camp in campaigns:
            if c["campaign"]["_id"] == camp["_id"]:
                #print camp["_id"] + " has ol " + c["_id"] + " on it"
                try:
                    refId=c["refId"]
                except:
                    refId=""
                    pass
                oldata = {
                    ##  CSV Field Header: Field to Populate it wit
                        "orderLineId":c["_id"],
                        "campaignId":c["campaignId"],
                        "targetType":c["targetType"],
                        "creativeType":c["creativeType"],
                        "orderLineName":c["name"],
                        "campaignName":c["campaign"]["name"],
                        "refId":refId,
                        "start":c["start"],
                        "stop":c["stop"]
                }
                ols.append(oldata)
                olid=c["_id"]
                for cre in c["creatives"]:
                    try:
                        size=cre["size"]
                    except:
                        size=0
                        pass
                    creative={
                            "creativeId":cre["_id"],
                            "orderLineId":olid,
                            "creativeName":cre["name"],
                            "size":size,
                            }
                #    print creative
                    creatives.append(creative)

    return ols,creatives


def stats_query(ids, headers):
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
        '&orderLineId=' + ids['orderLines'] +
        '&creativeId=' + ids['creatives']
    )
    r = requests.get(base_url + query, headers=headers).json()
    return r

def build_ids(level, _id):
    ids = {
        'campaigns': '',
        'orderLines': '',
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
        start = str(date.today() - timedelta(days=1))# + "%2007:00:00"
    try:
        stop = sys.argv[4]
    except:
        stop = str(date.today() - timedelta(days=0))# + "%2006:59:59"
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

#create output files
creative_csv = open('creative' + str(start) + '.csv', 'w')
orderLine_csv = open('orderLine' + str(start) + '.csv', 'w')
campaign_csv = open('campaign' + str(start) + '.csv', 'w')

login = { 'username': user, 'password': passw }


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

#get list of orderLines

#make a list of orgs and suborgs
#Print column headings
#  [ <key>, <label> ]#
fields = {
    'orderLines': [
        ['_id', '"orderLineId"'],
        ['campaignId','"campaignId"'],
        ['targetType','"targetType"'],
        ['creativeType','"creativeType"'],
        ['name','"orderLineName"'],
        ['campaignName','"campaignName"'],
        ['refId','"refId"'],
        ['start','"start"'],
        ['stop','"stop"'],
    ],
    'campaigns': [
        ['_id', 'campaignId'],
        ['orgId', 'orgId']
    ],
    'creatives': [
        ['_id', 'creativeId'],
        ['orderLineIds', 'orderLineId'],
        ['name', 'creativeName'],
        ['size', 'size']
    ],
}

indices = {
    'orderLines': {
        'name': 'orderLines',
        'file': orderLine_csv,
    },
    'campaigns': {
        'name': 'campaigns',
        'file': campaign_csv,
    },
    'creatives': {
        'name': 'creatives',
        'file': creative_csv,
        'denorm': 'orderLines',
    },
}
orgs = get_orgs(org_id)
print orgs
print str(len(get_campaigns(orgs)))+ " campaigns"
ols,creatives=get_orderLines(get_campaigns(orgs))
print str(len(ols)) + " order lines"
print str(len(creatives)) + " creatives"
sys.exit()



valid_camps = valid_campaign_list(orgs)
valid_ols = valid_ol_list(orgs, valid_camps)

def check_row(row, good_list, collection):
    if 'campaignId' in row.keys() and row['campaignId'] in good_list:
        return True
    if collection == 'campaigns' and row['_id'] in good_list:
        return True
    if collection == 'creatives' and set(row['orderLineIds']) & set(valid_ols):
        return True
    return False



for level in indices.keys():
    rows = []
    row1 = 'Date,Hour,Clicks,Imps,'
    for f in fields[level]:
        row1 += f[1] + ','
    row1 = row1[:-1]
    indices[level]['file'].write(row1 + '\n')
    row1 = ''

    #Write a row for each orderLine belonging to each org
    rows = get_collection(level, orgs)
    for row in rows:
        if check_row(row, valid_camps, level):
            field_list = ''
            for f in fields[level]:
                if f[0] in row.keys():
                    if type(row[f[0]]) in [unicode, str]:
                        field_list += '"' + row[f[0]] + '",'
                    elif f[0] == 'orderLineIds':
                        field_list += '"' + row[f[0]][0] + '",'
                    else:
                        field_list += str(row[f[0]]) + ','
                else:
                    field_list += ','
            field_list = field_list[:-1]
            ids = build_ids(level, row['_id'])
            stats = stats_query(ids, headers)
            i = 0
            for obs in stats:
                if i > 6 and i < 31:
                    indices[level]['file'].write(str(start) + ',')
                    indices[level]['file'].write(str(i - 7) + ',')
                    indices[level]['file'].write(str(obs['clicks']) + ',')
                    indices[level]['file'].write(str(obs['imps']) + ',')
                    indices[level]['file'].write(field_list + '\n')
                i += 1

sys.exit()
