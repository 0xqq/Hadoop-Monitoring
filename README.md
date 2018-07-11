# Hadoop-Monitoring  
  
## 시스템 개요
1. [데이터 수집 및 저장(hm-data_collect)](https://github.com/jwkim-smu/Hadoop-Monitoring/blob/master/README.md#1-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EC%88%98%EC%A7%91-%EB%B0%8F-%EC%A0%80%EC%9E%A5)
2. [웹 UI(hm-web)](https://github.com/jwkim-smu/Hadoop-Monitoring/blob/master/README.md#2-웹-ui)
	
	
## 1. 데이터 수집 및 저장
### 1. 데이터 수집
* python 스크립트를 이용하여 수집
* 3가지 방법으로 수집함
	1. HTTP GET 방식으로 Hadoop의 상태 수집 (jmx & REST api)
	2. Hadoop config file을 주기적으로 체크하여 변동사항 수집
	3. 머신의 상태(CPU, Network, Memory usage) 수집
* Hadoop 역할에 따라 수집 스크립트가 다름
	1. NN, RM : Namenode & Resource Manager
	2. DN, NM : Datanode & Node Manager
	
### 2. 데이터 저장
* Mongodb에 데이터 저장
* pymongo package 사용
	
	
## 2. 웹 UI
### 1. 데이터 쿼리
* Mongodb MapReduce 사용
	1. timestamp를 기준으로 일정 시간 간격에 따라 mapping
	2. mapping된 시간 간격사이의 평균값, 최소값, 최대값 사용
