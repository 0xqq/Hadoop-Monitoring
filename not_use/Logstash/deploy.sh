#! /bin/bash
##############################
## INSERT HOST and CLUSTER_ID TO DB
##############################
## set hosts ip
hosts=()
hosts_slaves=()
counter=0
while read ip host;
do
  hosts+=("$host")
  if [ "$counter" -ne 0 ];
  then
    hosts_slaves+=("$ip")
  fi
  (( counter ++ ))
done < /etc/hdhosts
echo ${hosts[@]}
echo ${hosts_slaves[@]}

## get cluster id
### 1. using curl method 
var=`curl -X GET http://localhost:8088/ws/v1/cluster/info`
clusterId=`echo $var | cut -d',' -f1 | cut -d':' -f3`

### 2. using namenode config
#clusterIdLine=`sed -n '/clusterID/p' /ambari/hadoop/hdfs/namenode/current/VERSION`
#clusterId=`echo $clusterIdLine | cut -d'=' -f2`

### password error catch가 필요
echo -e "Database Password : \c "
read dbpassword

## insert master hostname to DB 
for _HOST in "${hosts[@]}";
do
  insertclstr="INSERT INTO cluster(hostname, clusterId)  VALUES (\"$_HOST\",\"$clusterId\")"
  `mysql -hdb-ou7l.pub-cdb.ntruss.com -uroot -p$dbpassword hadoopmon -e "$insertclstr"`
done 

##############################
## LOGSTASH
##############################

## download & decompress Logstash 
#wget -P /opt https://artifacts.elastic.co/downloads/logstash/logstash-6.2.4.tar.gz
#tar -xzf /opt/logstash-6.2.4.tar.gz -C /opt/
#rm /opt/logstash-6.2.4.tar.gz

## download logstash.conf
#wget -O /opt/logstash-6.2.4/logstash.conf https://github.com/RedCheezeCake/Hadoop-Monitoring/blob/master/Logstash/logstash.conf?raw=true

## Set Logstash env
export LS_HOME="/opt/logstash-6.2.4"
export LS_BIN=$LS_HOME/bin
export LS_JDBC=$LS_HOME/vendor/jar/jdbc
echo $LS_HOME
echo $LS_BIN
echo $LS_JDBC

## install output plugin : JDBC
$LS_BIN/logstash-plugin install logstash-output-jdbc
mkdir -p $LS_JDBC
wget -P $LS_JDBC https://downloads.mysql.com/archives/get/file/mysql-connector-java-8.0.9-rc.tar.gz
tar xzf mysql-connector-java-8.0.9-rc.tar.gz
mv $LS_JDBC/mysql-connector-java-8.0.9-rc/mysql-connector-java-8.0.9-rc-bin.jar $LS_JDBC/mysql-connector-java-8.0.9-rc-bin.jar
#rm -rf $LS_JDBC/mysql-connector-java-8.0.9-rc

## deploy LS to slaves
echo LS DEPLOYING...
for _IP in "${hosts_slaves[@]}"
do
  `scp -r $LS_HOME $_IP:/opt/`
done

## run LS on slaves
echo LS RUNNING...
for _IP in "${hosts_slaves[@]}"
do 
  ssh ${_IP} "/opt/logstash-6.2.4/bin/logstash -f /opt/logstash-6.2.4/logstash.conf"
done
