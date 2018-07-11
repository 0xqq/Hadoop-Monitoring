import os
import sys

import threading
import json
import time
import datetime
import socket
import re

# pip install
try :
    import pip
except :
    print "installing pip"
    cmd = "yum install epel-release -y"
    os.system(cmd)
    cmd = "yum install python-pip -y"
    os.system(cmd)
    import pip
else :
    print "pip is already installed"

#  package install
try :
    import psutil
except :
    os.system('pip install psutil')
    import psutil
try :
    from pymongo import MongoClient
except :
    os.system('pip install pymongo')
    from pymongo import MongoClient
try :
    import requests
except :
    os.system('pip install requests')
    import requests


db_ip = sys.argv[1]
db_port = sys.argv[2]
db_name = sys.argv[3]
db_user = sys.argv[4]
db_pass = sys.argv[5]
clusterInfo={'clusterId':sys.argv[6], 'clusterName':sys.argv[7]}

host = socket.gethostbyname(socket.gethostname())
tick = 3

def time2seconds(time) :
    return round((time-datetime.datetime(1970,1,1)).total_seconds())

def watcher_conf(path, dic, clusterInfo, mongoColumn) :
    dic_result={}
    while True :
    # for i in range(tc) :
        f = open(path, 'r')
        lines = f.readlines();
        flag = False
        for idx  in range(0, len(lines)) :
            _name = re.sub('<.*?>', '', lines[idx]).strip()
            if _name in dic.keys() :
                _value = re.sub('<.*?>', '', lines[idx+1]).strip()
                if dic[_name] != _value :
                    _rname = _name.replace('.','_')
                    dic_result[_rname] = _value
                    dic[_name] = _value
                    flag = True
        if flag :
            mongoColumn.update({'clusterId':clusterInfo['clusterId'], 'clusterName':clusterInfo['clusterName'],'flag':'true', 'host':host },
                                { '$set': {'flag':'false'}})
            mongoColumn.insert({'clusterId':clusterInfo['clusterId'], 'clusterName':clusterInfo['clusterName'],'flag':'true',
                                'ts':time2seconds(datetime.datetime.utcnow()), 'host':host, 'value' : dic_result})
            print '== [CONF] '+ str(flag)
            flag = False
        time.sleep(tick*600)

def watcher_jmx(dic, service, port, clusterInfo, mongoColumn) :
    url = 'http://'+host+':'+port+'/jmx?qry=Hadoop:service='+service+',name='
    while True :
    # for i in range(tc) :
        dic_result = {}
        for _nkey in dic.keys() :
            url_qry = url + _nkey
            res = requests.get(url_qry)

            if res.status_code != 200 :
                f=open('./logs/http.log', 'a')
                f.write(datetime.now()+'\t[http]\tREQUEST_FAIL\t'+res.status_code+"\t"+url_qry)
                f.close()
                return;
            else :
                resJson = res.json()['beans'][0]

                for _key in dic[_nkey].keys() :
                    _rkey = _key.replace('.', '_')
                    # # nodes
                    # if 'Nodes' in _key :
                    #     print resJson[_key].replace('.', '_').replace('\\', '')
                    #     dic_result[_rkey] = json.loads(resJson[_key].replace('.', '_').replace('\\', ''))
                    # else :
                    dic_result[_rkey]=resJson[_key]
        mongoColumn.insert({'clusterId':clusterInfo['clusterId'], 'clusterName':clusterInfo['clusterName'],
                            'ts':time2seconds(datetime.datetime.utcnow()), 'host':host, 'value' : dic_result})
        print '== [JMX] '+ service
        time.sleep(tick)

def watcher_api(dic, service, port, clusterInfo, mongoColumn) :
    url = 'http://'+host+':'+port+'/ws/v1/'
    while True :
    # for i in range(tc) :
        dic_result = {}
        for _nkey in dic.keys() :
            url_qry = url + _nkey
            res = requests.get(url_qry)

            if res.status_code != 200 :
                f=open('./logs/http.log', 'a')
                f.write(datetime.now()+'\t[http]\tREQUEST_FAIL\t'+res.status_code+"\t"+url_qry)
                f.close()
                return;
            else :
                if 'cluster/info' == _nkey :
                    resJson = res.json()['clusterInfo']
                elif 'cluster/metrics' == _nkey :
                    resJson = res.json()['clusterMetrics']
                for _key in dic[_nkey].keys() :
                    dic_result[_key]=resJson[_key]

        mongoColumn.insert({'clusterId':clusterInfo['clusterId'], 'clusterName':clusterInfo['clusterName'],
                            'ts':time2seconds(datetime.datetime.utcnow()), 'host':host,  'value' : dic_result})
        print '== [REST API] '+ service
        time.sleep(tick)

def convert_to_mbit(value):
    return value/1024./1024.*8

def watcher_resource(clusterInfo, mongoColumn) :
    old_value = 0
    while True :
    # for i in range(tc) :
        new_value = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

        if old_value:
            cpu_percent = psutil.cpu_percent()
            memory_total = psutil.virtual_memory().total
            memory_used = psutil.virtual_memory().used
            memory_percent = psutil.virtual_memory().percent
            network_bandwidth = float(format(convert_to_mbit(new_value - old_value), '.2f'))

            # db insert
            mongoColumn.insert({'clusterId':clusterInfo['clusterId'], 'clusterName':clusterInfo['clusterName'], "cpu":cpu_percent, "memory":{"total":memory_total, "used":memory_used, "percent":memory_percent},
                        "network":network_bandwidth, "host":host, "ts":time2seconds(datetime.datetime.utcnow())})
            print '== [RESOURCE] '
        time.sleep(tick)
        old_value = new_value


# MongoClientW
client = MongoClient("mongodb://"+db_user+":"+db_pass+"@"+db_ip+":"+db_port+"/"+db_name)
db = client[db_name]

# Conf
conf_dir = '/etc/hadoop/conf/'
detect_keyword = {'dfs.replication':'', 'dfs.blocksize':''}
t_conf = threading.Thread(target=watcher_conf, args=(conf_dir+'hdfs-site.xml', detect_keyword, clusterInfo, db['conf_change'],))
t_conf.deamon = True
t_conf.start()


# HTTP
dic_service={'NameNode':'50070', 'ResourceManager':'8088'}

# JMX
dic_NN_jmx={'FSNamesystem':{'tag.HAState':'', 'CapacityTotal':'', 'CapacityUsed':'', 'BlocksTotal':'', 'FilesTotal':'', 'MissingBlocks':'', 'CorruptBlocks':''},
         'JvmMetrics':{'MemHeapMaxM':'', 'MemHeapUsedM':''},
         'NameNodeInfo':{'NNStarted':'', "LiveNodes":'', "DeadNodes":'', "DecomNodes":'', 'Safemode':''}
         }
dic_RM_jmx={'JvmMetrics':{'MemHeapMaxM':'', 'MemHeapUsedM':''}}
for _skey in dic_service.keys() :
    if _skey == 'NameNode' :
        dic_jmx = dic_NN_jmx
    else :
        dic_jmx = dic_RM_jmx
    if bool(dic_jmx) :
        t_jmx = threading.Thread(target=watcher_jmx, args=(dic_jmx, _skey, dic_service[_skey], clusterInfo, db[_skey+'_jmx'],))
        t_jmx.deamon = True
        t_jmx.start()

# Rest API
dic_NN_api={}
dic_RM_api={'cluster/info':{'state':'', 'haState':'', 'startedOn':''},
            'cluster/metrics':{'appsSubmitted':'', 'appsCompleted':'', 'appsPending':'', 'appsFailed':'', 'appsKilled':'',
                                'reservedMB':'', 'availableMB':'', 'allocatedMB':'', 'totalMB':'',
                                'reservedVirtualCores':'', 'availableVirtualCores':'', 'allocatedVirtualCores':'', 'totalVirtualCores':'',
                                'containersAllocated':'', 'containersReserved':'', 'containersPending':'',
                                'totalNodes':'', 'activeNodes':'', 'lostNodes':'', 'unhealthyNodes':'', 'decommissionedNodes':'', 'rebootedNodes':''}
            }
for _skey in dic_service.keys() :
    if _skey == 'NameNode' :
        dic_api = dic_NN_api
    else :
        dic_api = dic_RM_api
    if bool(dic_api) :
        t_api = threading.Thread(target=watcher_api, args=(dic_api, _skey, dic_service[_skey], clusterInfo, db[_skey+'_api'],))
        t_api.deamon = True
        t_api.start()

# machine resource
t_resource = threading.Thread(target=watcher_resource, args=(clusterInfo, db['server_rsrc'],))
t_resource.deamon = True
t_resource.start()
