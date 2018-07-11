##############################
## PIP INSTALL
##############################
print '===================[PACKAGE CHECK]===================='
import os
import time
# pip install
try :
    import pip
except :
    print "-- installing pip"
    cmd = "yum install epel-release -y"
    os.system(cmd)
    cmd = "yum install python-pip"
    os.system(cmd)
    import pip
else :
    print "-- pip is already installed"

#  package install
os.system('pip install paramiko')
import paramiko
os.system('pip install pymongo')
from pymongo import MongoClient
print ''

##############################
## HOSTNAME SET
##############################
print '==================[ CLUSTER HOST CHECK ]==================='
# base directory
BASE_DIR = "/root/hm_workspace/"
os.system("mkdir -p "+BASE_DIR)

# hostnames variable setting for deploying
hadoop_conf_dir="/etc/hadoop/conf/" # This may change depending on your hadoop settings.
hostnames=[]
nnhost=[]
dnhost=[]
cmd_namehost="cat "+hadoop_conf_dir+"/hdfs-site.xml | grep -A 1 'dfs.namenode.http-address.' | grep '<value>'" + \
             "| sed -e 's/<value>//g' | sed -e 's/<\/value>//g' | sed -e 's/:/ /g' |  awk '{print $1}'"
nnhost=os.popen(cmd_namehost).readlines()
cmd_datahost="hdfs dfsadmin -report | grep 'Hostname: ' | awk '{print $2}'"
dnhost=os.popen(cmd_datahost).readlines()

# readlines has appended '\n'
# rstrip '\n'
for idx in range(0,len(nnhost)) :
    nnhost[idx] = nnhost[idx].rstrip('\n') #remove strip
for idx in range(0,len(dnhost)) :
    dnhost[idx] = dnhost[idx].rstrip('\n') #remove strip

# host ip CHECK
for idx in range(0,len(nnhost)) :
    print 'ip check - '+nnhost[idx]
    nnhost[idx] = os.popen("ping -c 1 -W 1 "+nnhost[idx]+" | grep PING | awk '{print $3}'").readline().rstrip('\n').replace('(','').replace(')','')
for idx in range(0,len(dnhost)) :
    print 'ip check - '+dnhost[idx]
    dnhost[idx] =  os.popen("ping -c 1 -W 1 "+dnhost[idx]+" | grep PING | awk '{print $3}'").readline().rstrip('\n').replace('(','').replace(')','')
hostnames+=nnhost
hostnames+=dnhost
print hostnames
print '[Ok]\n'

##############################
## DATABASE CONNECTION CHECK
##############################
print '===================[ DATABASE CHECK ]==================='
# Mongodb server for data collecting
db_ip = ""
db_port = ""
db_name = ""
db_pass = ""
db_user = ""

while 1 :
    print "-- Insert yout mongodb connection info"
    db_ip = raw_input("Database IP : ")
    db_port = raw_input("Database Port : ")
    db_name = raw_input("Database Name : ")
    db_user = raw_input("Database User : ")
    db_pass = raw_input("Database Password : ")

    # It is only Testing Configuration ##############################################################
    if db_ip=="" :
        db_ip = "10.41.4.230"
    if db_port=="" :
        db_port = "27017"
    if db_name=="" :
        db_name = "hadoopmon"
    if db_user=="" :
        db_user = "hmUser"
    if db_pass=="" :
        db_pass = "nbp123"
    try :
        conn = MongoClient("mongodb://"+db_user+":"+db_pass+"@"+db_ip+":"+db_port+"/"+db_name)
         # The ismaster command is cheap and does not require auth.
        conn.admin.command('ismaster')
    except  :
        print "-- This Mongodb Server is not available !\n"
        time.sleep(1)
    else :
        print "-- Mongodb Server is available !"
        ############
        # conn[db_name].command("createUser","hm_was",pwd="was123",roles=["read"])
        conn.close()
        break
print ''


##############################
## META DATA SET
##############################
print '=================[ CLUSTER META SETTING ]================='
# get cluster id into Namenode config
namenode_conf_dir = "/ambari/hadoop/hdfs/namenode/current/VERSION"
cmd_cluster_id = "cat "+namenode_conf_dir+ "| grep 'clusterID' "
cluster_id = os.popen(cmd_cluster_id).readline().rstrip('\n').split('=')[1] # format : clusterID=xxxxxxxx

# get cluster name by user input
cluster_name = raw_input("-- Insert your cluster name : ")

# write file
cluster_meta_file_path = BASE_DIR+"cluster_"+cluster_id
cluster_meta_file = open(cluster_meta_file_path, 'w')
cluster_meta_file.write("cluster ID   = "+cluster_id)
cluster_meta_file.write("\ncluster Name = "+cluster_name)
cluster_meta_file.write("\nmongodb ip   = "+db_ip)
cluster_meta_file.write("\nmongodb port = "+db_port)
cluster_meta_file.write("\nmongodb name = "+db_name)
cluster_meta_file.write("\nmongodb user = hm_was")
cluster_meta_file.write("\nmongodb pwd  = was123")
cluster_meta_file.write("\nnn hosts = ")
for idx in range(0,len(nnhost)) :
    cluster_meta_file.write(nnhost[idx]+", ")
cluster_meta_file.write("\ndn hosts = ")
for idx in range(0,len(dnhost)) :
    cluster_meta_file.write(dnhost[idx]+", ")
cluster_meta_file.close()

# show info
print "[CLUSTER INFO]"
print "cluster id   : " + cluster_id
print "cluster name : " + cluster_name
print "hostnames    : "
for idx in range(0, len(hostnames)) :
    print "["+str(idx)+"] : " + hostnames[idx]
print ''

# send meta data file to WAS by ssh
while 1 :
    print "-- Send cluster meta file to Web Server"
    was_ip = raw_input("Web Server IP : ")
    was_user = raw_input("Web Server User : ")
    was_pass = raw_input("Web Server Password : ")

    # It is only Testing Configuration ##############################################################
    if was_ip=="" :
        was_ip = "10.41.0.208"
    if was_user=="" :
        was_user = "root"
    if was_pass=="" :
        was_pass = "kdh1200#@!"

    msg = os.system("scp " +cluster_meta_file_path+" "+was_user+"@"+was_ip+":/root/hmweb2/clusterList")
    # 0 is good
    if msg != 0 :
        print "This Web Server is not available !\n"
        sleep(1)
    else :
        # conn = MongoClient("mongodb://"+was_ip+":27017")
        # db = conn.hadoopmon
        # db.cluster.insert({"clusterId":cluster_id, "clusterName":cluster_name, "host":{"nn":nnhost, "dn":dnhost}})
        print "Cluster Meta Data Send [ok]"
        break
print ''

##############################
## DEPLOY TRIGGER
##############################
print '===================[ DEPLOY AND RUN ]===================='

# download trigger.py
import urllib

print "-- Download py"
hddc_nn_rm_url = "https://github.com/RedCheezeCake/Hadoop-Monitoring/raw/master/hddc_nn_rm.py"
hddc_dn_nm_url = "https://github.com/RedCheezeCake/Hadoop-Monitoring/raw/master/hddc_dn_nm.py"
urllib.urlretrieve(hddc_nn_rm_url, BASE_DIR+"hddc_nn_rm.py")
urllib.urlretrieve(hddc_dn_nm_url, BASE_DIR+"hddc_dn_nm.py")
target_dir='/root/hm_data_collector/'

# deploy and launch
print "-- Start deploying..."
for target_host in hostnames :
    print target_host
    _flag=False
    if target_host in nnhost :
        _flag = True
    print _flag
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print "["+target_host+"]"
    try :
        ssh.connect(target_host, username = 'root', password = '')
    except :
        while 1 :
            target_pwd =  raw_input("plz " + target_host + "'s Password : ")
            try :
                ssh.connect(target_host, username = 'root', password = target_pwd)
            except :
                print "Password is not correct!\n[TRY AGAIN]"
                sleep(1)
            else :
                break

    ssh.exec_command('mkdir -p '+target_dir+'/log')

    # deploy trigger
    sftp = ssh.open_sftp()
    if _flag :
        sftp.put(BASE_DIR+"hddc_nn_rm.py", target_dir+"hddc_nn_rm.py")
    else :
        sftp.put(BASE_DIR+"hddc_dn_nm.py", target_dir+"hddc_dn_nm.py")

    # excute trigger
    # argv[db_ip, db_port, db_name, db_user, db_pass, cluster_id, cluster_name]
    if _flag :
        stdin, stdout, stderr = ssh.exec_command('nohup python '+target_dir+'hddc_nn_rm.py '+db_ip+' '+db_port+' '+db_name+' '+db_user+' '+db_pass+' '+cluster_id+' '+cluster_name+' >/dev/null 2>&1 &')
    else :
        stdin, stdout, stderr = ssh.exec_command('nohup python '+target_dir+'hddc_dn_nm.py '+db_ip+' '+db_port+' '+db_name+' '+db_user+' '+db_pass+' '+cluster_id+' '+cluster_name+' >/dev/null 2>&1 &')

    # log_out = open(target_dir+'/log/log_out.log', 'w')
    # log_out.write(stdout.read())
    # log_out.close()
    # log_err = open(target_dir+'/log/log_err.log', 'w')
    # log_err.write(stderr.read())
    # log_err.close()

    ssh.close()
