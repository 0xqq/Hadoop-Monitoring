var express = require('express');
var path = require('path');
var fs = require('fs')
var app = express();

var clusterPath = './clusterList/'
app.locals.pretty = true

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: false }));
app.use(express.json());

app.locals.pretty = true;
app.set('views', './public/views');
app.set('view engine', 'jade');
var Client = require('mongodb').MongoClient;

var clusters = []
var idx = 0
var url = ""
var db_name = ""
app.get('/', function(req, res){
  clusters = []
  var dir = fs.readdirSync(clusterPath)
  for(var i=0; i<dir.length; i++) {
    var lines = fs.readFileSync(clusterPath+dir[i], 'utf8').split('\n')
    var clusterId = lines[0].split('=')[1].trim()
    var clusterName = lines[1].split('=')[1].trim()
    var db_ip = lines[2].split('=')[1].trim()
    var db_port = lines[3].split('=')[1].trim()
    db_name = lines[4].split('=')[1].trim()
    url = 'mongodb://hm_was:was123@'+db_ip+':'+db_port+'/'+db_name

    clusters.push({'clusterId':clusterId, 'clusterName':clusterName, 'url':url})
  }

  res.render('home', {clusters:clusters})
  // Client.connect('mongodb://localhost:27017/hadoopmon', function(error, database){
  //   if(error) {
  //       console.log(error);
  //   } else {
  //     var db = database.db('hadoopmon')
  //     var cursor =  db.collection('cluster').find();
  //     cursor.each(function(err,doc){
  //       if(err){
  //         console.log(err);
  //       }else{
  //         if(doc != null){
  //           clusters.push({'clusterId':doc.clusterId, 'clusterName':doc.clusterName, 'db_ip':doc.db_ip, 'db_port':doc.db_port, 'db_name':doc.db_name, 'db_user':doc.db_user, 'db_pass':doc.db_pass})
  //         }else{
  //           database.close();
  //           console.log(clusters);
  //           res.render('home', {clusters:clusters})
  //         }
  //       }
  //     });
  //   }
  // });
})

app.post('/cluster/hdfs', function(req, res){
  console.log('/cluster/hdfs');
  idx = req.body.idx;
  console.log(clusters[idx]);
  var cluster = clusters[idx];
  var nnhost = [];
  var lines = fs.readFileSync(clusterPath+'cluster_'+cluster.clusterId, 'utf8').split('\n')
  var nnhost = lines[7].split('=')[1].split(',')
  for(var i=0; i<nnhost.length; i++){
    nnhost[i]=nnhost[i].trim()
  }
  // console.log(nnhost);
  res.send({nnhost:nnhost})

})

app.post('/cluster/hdfs/nnButton/heapUsage', function(req, res){
  // console.log('/cluster/hdfs/nnButton/heapUsage');
  var host = req.body.host;
  var stime = parseInt(req.body.stime);
  var etime = parseInt(req.body.etime);
  var tick = req.body.tick;
  var colName = req.body.colName;

  var cluster = clusters[idx];
  var data = [];
  var label = [];
  // console.log(host);
  // console.log(db_name);
  Client.connect(cluster.url, function(error, database){
    if(error) {
        console.log(error);
    } else {
      var db = database.db(db_name)

      var map = function() {
        var dist = parseInt((this.ts - stime)/tick)
        emit(stime+(dist*tick), this.value.MemHeapUsedM/this.value.MemHeapMaxM);
      };

      var reduce = function(time, used) {
        var total = 0;
        for(var i =0; i<used.length; i++) {
          total += used[i];
        }
        return {
          avgUsed : total/used.length
        }
      };

      db.collection(colName).mapReduce(
        map,
        reduce,
        {
          query : {
            clusterId : cluster.clusterId,
            clusterName : cluster.clusterName,
            host : host,
            ts : {"$gte":stime, "$lt":etime}
          },
          out: {inline:1},
          scope:{
            stime : stime,
            tick : tick
          }
        },
        function(err, collection) {
          if(err){ console.log(err); }
          // console.log("COLLETIONS");
          // console.log(collection);
          for(var i=0; i<collection.length; i++) {
            label.push(collection[i]._id);
            data.push(collection[i].value.avgUsed*100);
          }
          res.send({data:data, label:label})
        }
      );
    }
  })
})

app.post('/cluster/hdfs/nnButton/diskUsage', function(req, res){
  console.log('/cluster/hdfs/nnButton/diskUsage');
  var host = req.body.host;
  var stime = parseInt(req.body.stime);
  var etime = parseInt(req.body.etime);
  var tick = req.body.tick;
  var colName = req.body.colName;

  var cluster = clusters[idx];
  var data = [];
  var label = [];

  Client.connect(cluster.url, function(error, database){
    if(error) {
        console.log(error);
    } else {
      var db = database.db(db_name)

      var map = function() {
        var dist = parseInt((this.ts - stime)/tick)
        emit(stime+(dist*tick), this.value.CapacityUsed/this.value.CapacityTotal);
      };
      var reduce = function(time, used) {
        var total = 0;
        for(var i =0; i<used.length; i++) {
          total += used[i];
        }
        return {
          avgUsed : total/used.length
        }
      };

      db.collection(colName).mapReduce(
        map,
        reduce,
        {
          query : {
            clusterId : cluster.clusterId,
            clusterName : cluster.clusterName,
            host : host,
            ts : {"$gte":stime, "$lt":etime}
          },
          out: {inline:1},
          scope:{
            stime : stime,
            tick : tick
          }
        },
        function(err, collection) {
          if(err){ console.log(err); }
          // console.log(collection);
          for(var i=0; i<collection.length; i++) {
            label.push(collection[i]._id);
            data.push(collection[i].value.avgUsed*100);
          }
          res.send({data:data, label:label})
        }
      );
    }
  })
})

app.post('/cluster/hdfs/nnButton/blockInfo', function(req, res){
  console.log('/cluster/hdfs/nnButton/blockInfo');
  var host = req.body.host;
  var cluster = clusters[idx];
  // console.log(cluster);
  var data = [];
  var label = [];
  (async function() {
    let client;
    try {
      client = await Client.connect(cluster.url);
      console.log("Connected correctly to server");
      const db = client.db(db_name);

      var curtime = (new Date().getTime() / 1000)-4;

      col = db.collection('conf_change');
      // Get the cursor
      var cursor = col.find({'clusterId':cluster.clusterId, 'clusterName':cluster.clusterName, 'host':host, 'flag':'true'});
      while(await cursor.hasNext()) {
        var doc = await cursor.next();
        var blockSize=doc.value.dfs_blocksize;
        var replifactor=doc.value.dfs_replication;
      }
      col = db.collection('NameNode_jmx');
      // Get the cursor
      cursor = col.find({'clusterId':cluster.clusterId, 'clusterName':cluster.clusterName, 'host':host, 'ts':{"$gte":curtime}});
      // Iterate over the cursor
      while(await cursor.hasNext()) {
        var doc = await cursor.next();
        var totalFile=doc.value.FilesTotal;
        var totalBlock=doc.value.BlocksTotal;
        var missingBlock=doc.value.MissingBlocks;
        var corruptBlock=doc.value.CorruptBlocks;
      }
    } catch (err) {
      console.log(err.stack);
    }
      res.send({blockInfo:{'blockSize':blockSize, 'replifactor':replifactor,
              'totalFile':totalFile, 'totalBlock':totalBlock}})
  })();
})

app.post('/cluster/hdfs/nnButton/headline', function(req, res){
  console.log('/cluster/hdfs/nnButton/headline');

  var host = req.body.host;

  var cluster = clusters[idx];
  // console.log(cluster);

  var data = [];
  var label = [];
  (async function() {
    let client;
    try {
      client = await Client.connect(cluster.url);
      console.log("Connected correctly to server");
      const db = client.db(db_name);
      var col = db.collection('NameNode_jmx');
      var curtime = (new Date().getTime() / 1000)-4;
      // console.log(curtime);
      // console.log(cluster);
      // Get the cursor
      var cursor = col.find({'clusterId':cluster.clusterId, 'clusterName':cluster.clusterName, 'host':host, 'ts':{"$gte":curtime}});
      // Iterate over the cursor
      while(await cursor.hasNext()) {
        var doc = await cursor.next();
        // console.log("=="+doc);
        var NNStarted=doc.value.NNStarted;
        var HAState=doc.value.tag_HAState;
        var CapacityUsed=doc.value.CapacityUsed;
        var CapacityTotal=doc.value.CapacityTotal;
        var MemHeapUsedM=doc.value.MemHeapUsedM;
        var MemHeapMaxM=doc.value.MemHeapMaxM;
        var MissingBlocks=doc.value.MissingBlocks;
        var CorruptBlocks=doc.value.CorruptBlocks;

        var LiveNodes=doc.value.LiveNodes;
        var DeadNodes=doc.value.DeadNodes;
        var DecomNodes=doc.value.DecomNodes;

        var LiveNodes_JSON = JSON.parse(LiveNodes.replace("\\",''));
        var DecomNodes_JSON = JSON.parse(DecomNodes.replace("\\",''));
        var DeadNodes_JSON = JSON.parse(DeadNodes.replace("\\",''));

        var live = Object.keys(LiveNodes_JSON).length
        var total = Object.keys(LiveNodes_JSON).length+ Object.keys(DecomNodes_JSON).length+ Object.keys(DeadNodes_JSON).length
      }


      res.send({headline:{'NNStarted':NNStarted, 'HAState':HAState,
              'CapacityUsed':(CapacityUsed/CapacityTotal*100).toFixed(2),
              'live':live, 'total':total,
              'MemHeapUsedM':(MemHeapUsedM/MemHeapMaxM*100).toFixed(2),
              'MissingBlocks':MissingBlocks, 'CorruptBlocks':CorruptBlocks}})
    } catch (err) {
      console.log(err.stack);
    }
  })();
})

app.post('/cluster/hdfs/nnButton/datanode', function(req, res){
  console.log('/cluster/hdfs/nnButton/datanode');
  console.log(url);
  var host = req.body.host;
  var stime = parseInt(req.body.stime);
  var etime = parseInt(req.body.etime);
  var tick = req.body.tick;
  var colName = req.body.colName;

  var cluster = clusters[idx];

  var data = [];
  var label = [];

  (async function() {
    let client;
    try {
      client = await Client.connect(cluster.url);
      console.log("Connected correctly to server");
      const db = client.db(db_name);
      // Get the collection
      var col = db.collection("NameNode_jmx");
      var curtime = (new Date().getTime() / 1000)-4;
      // Get the cursor
      var cursor = col.find({'clusterId':cluster.clusterId, 'clusterName':cluster.clusterName, 'host':host, 'ts':{"$gte":curtime}});
      // Iterate over the cursor

      while(await cursor.hasNext()) {
        var ip = []
        var live = [];
        var decom = [];
        var dead = [];
        var doc = await cursor.next();

        var LiveNodes=doc.value.LiveNodes;
        var DeadNodes=doc.value.DeadNodes;
        var DecomNodes=doc.value.DecomNodes;

        var LiveNodes_JSON = JSON.parse(LiveNodes.replace("\\",''));
        var DecomNodes_JSON = JSON.parse(DecomNodes.replace("\\",''));
        var DeadNodes_JSON = JSON.parse(DeadNodes.replace("\\",''));

        for(var k in LiveNodes_JSON) {
          var _live = {}
          _live['name'] = k.split(":")[0];
          _live['disk'] = ((LiveNodes_JSON[k]['used']/LiveNodes_JSON[k]['capacity'])*100).toFixed(2)
          live.push(_live)
          ip.push(LiveNodes_JSON[k]['infoAddr'].split(":")[0])
          console.log(ip);
        }
        for(var k in DecomNodes_JSON) {
          var _decom = {}
          _decom['name'] = k.split(":")[0];
          _decom['disk'] = 0;
          _decom['heap'] = 0;
          decom.push(_decom)
        }
        for(var k in DeadNodes_JSON) {
          var _dead = {}
          _dead['name'] = k.split(":")[0];
          _dead['disk'] = 0;
          _dead['heap'] = 0;
          dead.push(_dead)
        }
      }

      var col = db.collection("DataNode_jmx");

      for( var i=0; i<ip.length; i++){
        var cursor = col.find({'clusterId':cluster.clusterId, 'clusterName':cluster.clusterName,
                                  'host': ip[i], 'ts':{"$gte":curtime}});
        while(await cursor.hasNext()) {
          var doc = await cursor.next();
          console.log(doc);
          var heapMax = doc.value.MemHeapMaxM
          var heapUsed = doc.value.MemHeapUsedM
          live[i]['heap'] = ((doc.value.MemHeapUsedM/ doc.value.MemHeapMaxM)*100).toFixed(2)

        }
      }



      var map = function() {
        var dist = parseInt((this.ts - stime)/tick)
        var LiveNodes=this.value.LiveNodes;
        LiveNodes_JSON = JSON.parse(LiveNodes.replace("\\",''));
        var keys = [];
        for(var k in LiveNodes_JSON) keys.push(k);
        emit(stime+(dist*tick), keys.length);
      };
      var reduce = function(time, used) {
        var min = 0;
        for(var i =0; i<used.length; i++) {
          if(i==0){ min = used[0] }
          if(min>used[i]) { min = used[i] }
        }
        return {
          min : min
        }
      };
      var col = db.collection("NameNode_jmx");

      col.mapReduce(
        map,
        reduce,
        {
          query : {
            clusterId : cluster.clusterId,
            clusterName : cluster.clusterName,
            host : host,
            ts : {"$gte":stime, "$lt":etime}
          },
          out: {inline:1},
          scope:{
            stime : stime,
            tick : tick
          }
        },
        function(err, collection) {
          if(err){ console.log(err); }
          for(var i=0; i<collection.length; i++) {
            label.push(collection[i]._id);
            data.push(collection[i].value.min);
          }
          res.send({data:data, label:label,
                    doughnut_count:[Object.keys(LiveNodes_JSON).length, Object.keys(DecomNodes_JSON).length, Object.keys(DeadNodes_JSON).length],
                    doughnut_label:['Live', 'Decommission', 'Lost'],
                    nodelist:{live,decom,dead}})
        }
      );

    } catch (err) {
      console.log(err.stack);
    }
  })();
})

app.listen(3000, function(req, res){
  console.log('PORT 3000 Connected');
})
