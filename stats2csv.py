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
                    if c['_id'] in ['58641f64a6ba51bb4290c755','586420cca6ba51bb4290c819','58642262a6ba51bb4290cb36','5864269fa6ba51bb4290d355','586426f0a6ba51bb4290d3d0']:
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
                            'creativeName':cre["name"]
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
                                'creativeName':cre["name"]
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

def stats_query_tmp(ids, headers):
    query = (
        '/narollup-results?start_date=' +
        start +
        '&end_date=' +
        stop +
        '&time_frame=' +
        granularity
    )
    if str(ids['orderLines']) <> "" and ids['creatives'] == "":
        query = query + '&order_line_id=' + ids['orderLines']
    if str(ids['campaigns']) <> "":
        query = query + '&campaign_id=' + ids['campaigns']
    if str(ids['creatives']) <> "":
        query = query + '&order_line_id=' + ids['orderLines'] + '&creative_id=' + ids['creatives']
# '&org_id=' + org_id +
    base_url="http://172.30.1.151:9002"
    r = requests.get(base_url + query).json()
    #print query
    return r["results"]
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
        row1 += 'orderLineId' + ','
        row1 += 'campaignId' + ','
        row1 += 'targetType' + ','
        row1 += 'creativeType' + ','
        row1 += 'orderLineName' + ','
        row1 += 'campaignName' + ','
        row1 += 'refId' + ','
        row1 += 'start' + ','
        row1 += 'stop'

    if level == 'creatives':
        rows = creatives
        id = 'creativeId'
        for row in rows:
            row1 += 'creativeId' + ','
            row1 += 'orderLineId' + ','
            row1 += 'creativeName'
            break

    if level == 'campaigns':
        rows = campaigns
        id = 'campaignId'
        for row in rows:
            row1 += "orgId" + ','
            row1 += 'campaignId'
            break

    print level + " Column headers: " + row1
    indices[level]['file'].write(row1 + '\r\n')

    print "Running Stats for " + level
    totalclicks=0
    totalimps=0
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

#        stats = stats_query(ids, headers)
#        print stats
        stats = stats_query_tmp(ids, headers)
#        print stats
        i = 0
        for obs in stats:
            #print obs
            #
            ## This is accounting for GMT->EST by getting two days worth and running on the proper window...
            ## Raw Log data is in GMT
            if i > 4 and i < 29:
                indices[level]['file'].write(str(start) + ',')
                indices[level]['file'].write(str(i - 5) + ',')
                indices[level]['file'].write(str(obs['clicks']) + ',')
                totalclicks = totalclicks + obs['clicks']
                indices[level]['file'].write(str(obs['imps']) + ',')
                totalimps = totalimps + obs['imps']
                if level == "campaigns":
                    indices[level]['file'].write(str(row['orgId']) + ',')
                    indices[level]['file'].write(str(row['campaignId']))
                if level == "orderLines":
                    indices[level]['file'].write(str(row['orderLineId']) + ',')
                    indices[level]['file'].write(str(row['campaignId']) + ',')
                    indices[level]['file'].write(str(row['targetType']) + ',')
                    indices[level]['file'].write(str(row['creativeType']) + ',')
                    indices[level]['file'].write(str(row['orderLineName']) + ',')
                    indices[level]['file'].write(str(row['campaignName']) + ',')
                    indices[level]['file'].write(str(row['refId']) + ',')
                    indices[level]['file'].write(str(row['start']) + ',')
                    indices[level]['file'].write(str(row['stop']))
                if level == "creatives":
                    indices[level]['file'].write(str(row['creativeId']) + ',')
                    indices[level]['file'].write(str(row['orderLineId']) + ',')
                    indices[level]['file'].write(str(row['creativeName']))
                indices[level]['file'].write('\r\n')
                val = ""
            i += 1
    print "Total Clicks for "+ level +" : " + str(totalclicks)
    print "Total Imps for "+ level +" : " + str(totalimps)
sys.exit()
