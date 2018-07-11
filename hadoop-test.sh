#! /bin/bash
hadoop fs -rm -r /output
hadoop jar $HADOOP_TEST_HOME/hadoop-mapreduce-examples-2.7.3.jar wordcount /input /output
