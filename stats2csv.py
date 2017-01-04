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

## get campaign top level list
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

## This gets all of the orderline data, and preps the data for output - add additional fields here
def get_orderLines(org_list):

    campaigns = get_campaigns(org_list)

    collection = "orderLines"
    ols = []
    creatives=[]
    camplist=[]
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
    for camp in campaigns:
        thecamp = {
                'campaignId':camp["_id"],
                'orgId':camp["orgId"]
                }
        camplist.append(thecamp)

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
                        'orderLineId':c["_id"],
                        'campaignId':c["campaignId"],
                        'targetType':c["targetType"],
                        'creativeType':c["creativeType"],
                        'orderLineName':c["name"],
                        'campaignName':c["campaign"]["name"],
                        'refId':refId,
                        'start':c["start"],
                        'stop':c["stop"]
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
                            'creativeId':cre["_id"],
                            'orderLineId':olid,
                            'creativeName':cre["name"],
                            'size':size,
                            }
                #    print creative
                    creatives.append(creative)
                try:
                    for cre in c["creativesIdsDetached"]:
                        try:
                            size=cre["size"]
                        except:
                            size=0
                            pass
                        creative={
                                'creativeId':cre["_id"],
                                'orderLineId':olid,
                                'creativeName':cre["name"],
                                'size':size,
                                }
                    #    print creative
                        creatives.append(creative)
                except:
                    pass
    return camplist,ols,creatives

# this runs the query for the detail stats for each option
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
    #print query
    return r

# Parse arguments and verify some things, default others
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


## Do all of the login stuff here

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


## Check valid login and org id
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

#Used for making the csvs by names
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

## Get the org from the login that happened
orgs = get_orgs(org_id)
## now go get the data from the functions above
print "Getting data for the report"
campaigns,ols,creatives = get_orderLines(orgs)


# meat an Potato's
for level in indices.keys():
    print level + " running"
    rows = []
    ids={}
    val = ""
    row1 = 'Date,Hour,Clicks,Imps,'

    #Write a row for each collection belonging to each org
    if level == 'orderLines':
        rows = ols
        id = 'orderLineId'

    if level == 'creatives':
        rows = creatives
        id = 'creativeId'

    if level == 'campaigns':
        rows = campaigns
        id = 'campaignId'

    for f,value in rows[0].iteritems():
        row1 += str(f) + ','
    row1 = row1[:-1]
    indices[level]['file'].write(row1 + '\n')

    print "Running Stats for " + level
    for row in rows:
        #ids = build_ids(level, row[id])
        if level == "campaigns":
            ids['campaigns']=row["campaignId"]
            ids['creatives']=""
            ids['orderLines']=""
        if level == "orderLines":
            ids['campaigns']=""
            ids['creatives']=""
            ids['orderLines']=row["orderLineId"]
        if level == "creatives":
            ids['campaigns']=""
            ids['creatives']=row["creativeId"]
            ids['orderLines']=row["orderLineId"]

        stats = stats_query(ids, headers)
        i = 0
        for obs in stats:
            if i > 4 and i < 29:
                indices[level]['file'].write(str(start) + ',')
                indices[level]['file'].write(str(i - 5) + ',')
                indices[level]['file'].write(str(obs['clicks']) + ',')
                indices[level]['file'].write(str(obs['imps']) + ',')
                for f,value in row.iteritems():
                    if isinstance(value,basestring):
                        val = val + '"' + str(value) + '"'+ ","
                    else:
                        val = val + str(value)+ ","
                val = val[:-1]
                indices[level]['file'].write(val + '\n')
                val = ""
            i += 1

sys.exit()
