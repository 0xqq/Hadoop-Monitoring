import os
import sys
import datetime

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
os.system('pip install psutil')
import psutil
os.system('pip install pymongo')
from pymongo import MongoClient

# read argv
db_ip   = sys.argv[1]
db_port = sys.argv[2]
db_name = sys.argv[3]
db_user = sys.argv[4]
db_pass = sys.argv[5]

cluster_id   = sys.argv[6]
cluster_name = sys.argv[7]
hostname = sys.argv[8]

# mongodb connection
client = MongoClient("mongodb://"+db_user+":"+db_pass+"@"+db_ip+":"+db_port+"/"+db_name)
db = client[db_name]
col = db['ServerResource']
# col='??'
#db[col].query

# data collect and insert
old_value = 0
def convert_to_mbit(value):
    return value/1024./1024.*8
#
# def send_stat(value):
#     return "%0.3f" % convert_to_mbit(value)

while True:
    new_value = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

    if old_value:
        cpu_percent = psutil.cpu_percent(interval=3)
        memory_total = psutil.virtual_memory().total
        memory_used = psutil.virtual_memory().used
        memory_percent = psutil.virtual_memory().percent
        network_bandwidth = float(format(convert_to_mbit(new_value - old_value), '.2f'))

        # db insert
        col.insert({"clusterId":cluster_id, "clusterName":cluster_name, "cpu":cpu_percent, "memory":{"total":memory_total, "used":memory_used, "percent":memory_percent}, 
                    "network":network_bandwidth, "hostname":hostname, "timastamp":datetime.datetime.utcnow()})
        print "insert!"
    old_value = new_value
