# Hadoop-Monitoring  
  
## 시스템 개요
1. 데이터 수집 및 저장(hm-data_collect)
2. 웹 UI(hm-web)
	
	
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
