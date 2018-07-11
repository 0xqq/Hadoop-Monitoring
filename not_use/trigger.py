##############################
## DATA COLLECTOR SET
##############################
# Data Collector : logstash and local_collector.py
# [Logstash] collects data for hadoop state
# [local_collector.py] collects data for server's local resource state
import os
import sys
import urllib
import tarfile
import datetime

BASE_DIR = "/root/hm_data_collector/"
logstash_url = "https://artifacts.elastic.co/downloads/logstash/logstash-6.2.4.tar.gz"
ls_conf_url = "https://github.com/RedCheezeCake/Hadoop-Monitoring/raw/master/Logstash/logstash.conf"
lc_py_url = "https://github.com/RedCheezeCake/Hadoop-Monitoring/raw/master/Logstash/local_collector.py"

# LOGSTASH PART
# Download logstash
urllib.urlretrieve(logstash_url, BASE_DIR+"logstash.tar.gz")

# print Extract logstash.tar.gz
print "tar.gz Extract.."
tar = tarfile.open(BASE_DIR+"logstash.tar.gz")
tar.extractall(path=BASE_DIR, members=None)
tar.close()

# dir rename logstashxxx -> logstash
LS_HOME = BASE_DIR+"logstash-6.2.4/"
os.remove(BASE_DIR+"logstash.tar.gz")
# cur_ls_name = os.popen('ls ' + BASE_DIR + ' | grep logstash ').readline().rstrip('\n')
# os.rename(BASE_DIR+cur_ls_name, BASE_DIR+'logstash')

# download logstash-output-mongodb plugin
print 'install mongodb output plug-in'
os.system(LS_HOME+"bin/logstash-plugin install logstash-output-mongodb")

# Download conf and local collector
urllib.urlretrieve(ls_conf_url, LS_HOME+"logstash.conf")
urllib.urlretrieve(lc_py_url, LS_HOME+"local_collector.py")

##############################
## DATA COllECTOR TRIGGER
##############################
# set db and cluster info by argv
db_ip   = sys.argv[1]
db_port = sys.argv[2]
db_name = sys.argv[3]
db_user = sys.argv[4]
db_pass = sys.argv[5]
cluster_id   = sys.argv[6]
cluster_name = sys.argv[7]

# get hostname
hostname = os.popen('uname -n').readline().rstrip('\n')

# Modify logstash.conf
print '[Modify logstash.conf]'
ls_conf_template = open(LS_HOME + "logstash.conf", 'r').readlines()
components = {"$DB_IP":db_ip, "$DB_PORT":db_port, "$DB_NAME":db_name, "$DB_USER":db_user,
            "$DB_PASS":db_pass, "$CLUSTER_ID":cluster_id, "$CLUSTER_NAME":cluster_name, "$HOSTNAME":hostname}
ls_conf = ""

for line in ls_conf_template :
    for comp in components.keys() :
        if comp in line :
            line = line.replace(comp,components[comp])
    # if '\'' in line :
    #     line = line.replace('\'', '\\\'')
    ls_conf += line.rstrip('\n')

# launch logstash
print '[Launch logstash]'
os.system("nohup "+LS_HOME+'bin/logstash -e \"'+ ls_conf+'\"  > /dev/null 2>&1')

# launch local_collector.py
print '[Launch local_collector.py]'
os.system("nohup python "+LS_HOME+'local_collector.py '+db_ip+" "+ db_port+" "+ db_name+" "+ db_user+" "+ db_pass+" "+ cluster_id+" "+ cluster_name+" "+ hostname+' > /dev/null 2>&1')

