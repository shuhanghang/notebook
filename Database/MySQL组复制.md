# MySQL组复制

## 1.什么是MGR

MGR(MySQL Group Replication)是MySQL官方在MySQL  5.7.17版本中以插件形式推出的主从复制高可用技术，它基于原生的主从复制，将各节点归入到一个组中，通过组内节点的通信协商(组通信协议基于Paxos算法)，实现数据的强一致性，具有弹性复制、高可用、主从替换、自动加组等等功能。    

### 1.1MySQL组复制协议



<img src="https://dev.mysql.com/doc/refman/8.0/en/images/gr-replication-diagram.png" alt="Replication Protocol" style="zoom: 33%;" />

这3个节点互相通信，每当有读写事件发生，都会向其他节点传播该事件，经过冲突检测后写入到binglog日志然后提交。

这些节点可以是单主模型的(single-primary)，也可以是多主模型的(multi-primary)。**单主模型只有一个主节点可以接受写操作，主节点故障时可以自动选举主节点**。**多主模型下所有节点都可以接受写操作**，所以没有master-slave的概念。



## 2.组复制模式

MySQL的组复制可以配置为**单主模型**和**多主模型**两种工作模式，它们都能保证MySQL的高可用。以下是两种工作模式的特性简介：

- 单主模型：从复制组中众多个MySQL节点中自动选举一个master节点，只有master节点可以写，其他节点自动设置为read only。当master节点故障时，会自动选举一个新的master节点，选举成功后，它将设置为可写，其他slave将指向这个新的master。
- 多主模型：复制组中的任何一个节点都可以写，因此没有master和slave的概念，只要突然故障的节点数量不太多，这个多主模型就能继续可用。

虽然多主模型的特性很诱人，但缺点是要配置和维护这种模式，必须要深入理解组复制的理论，更重要的是，多主模型限制较多，其一致性、安全性还需要多做测试。





## 3.配置单主模式的组复制

### 3.1 实验环境

实验前请在hosts文件中设置好解析，或则局域网内搭建Dns复制器（推荐docker搭建Dnsmasq）。当然也可以不设置解析，直接在my.cnf文件中使用IP地址即可。

|   系统   |   主机名   |      IP      |  MySQL版本   |
| :------: | :--------: | :----------: | :----------: |
| CentOS 7 | d1.mgr.com | 172.16.10.59 | mysql 8.0.19 |
| CentOS 7 | d2.mgr.com | 172.16.10.58 | mysql 8.0.19 |
| CentOS 7 | d3.mgr.com | 172.16.10.57 | mysql 8.0.19 |



### 3.2  配置第一个节点d1.mgr.com

#### 3.2.1 创建复制用户

连接donor（加组连接对象，由种子节点提供）的通道凭据（**channel credentials**）

```mysql
mysql> create user repl@'%' identified by 'P@ssword1!';
mysql> grant replication slave on *.* to repl@'%';
```

#### 3.2.2修改配置文件

` vim /etc/my.cnf`

```shell
server-id=10                       # 必须
gtid_mode=on                       # 必须，开启GTID模式
enforce_gtid_consistency=on        # 必须，不允许事务违背GTID的一致性
binlog_format=row                  # 必须，以行方式记录
binlog_checksum=none               # 必须，关闭事件校验
master_info_repository=TABLE       # 必须，记录加入master服务器信息到mysql.slave_master_info
relay_log_info_repository=TABLE    # 必须，记录节点中继日志的位置到mysql.slave_relay_log_info
log_slave_updates=on               # 必须，更新节点中继日志
sync-binlog=1                      # 建议，事务同步达到binlog
group_replication_recovery_get_public_key=1

transaction_write_set_extraction=XXHASH64         # 必须，事务写入算法
loose-group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" #必须，或使用uuidgen命令生成
loose-group_replication_start_on_boot=off         # 建议，关闭启动自开启复制
loose-group_replication_local_address="d1.mgr.com:20001"   # 必须，组复制本机地址及端口
loose-group_replication_group_seeds="d1.mgr.com:20001,d2.mgr.com:20002,d3.mgr.com:20003" # 必须，组复制种子地址及端口
loose-group_replication_ip_whitelist="172.16.10.0/24"	#建议，加组白名单
```

重启服务

`systemctl restart mysqld`

#### 3.2.3 配置加组通道

```mysql
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';

```

生成通道的relay log文件，`group_replication_recovery`通道的relay log用于新节点加入组时，**当新节点联系上donor后，会从donor处以异步复制的方式将其binlog复制到这个通道的relay log中，新节点将从这个recovery通道的relay log中恢复数据。**

#### 3.2.4安装插件并启用组复制

```mysql
mysql> install plugin group_replication soname 'group_replication.so';
mysql> reset master;
mysql> reset slave;
mysql> set @@global.group_replication_bootstrap_group=on;
mysql> start group_replication;
mysql> set @@global.group_replication_bootstrap_group=off;
```

`reset master`清空`binlog.index`索引日志并新建`binlog.000001`

`reset slave` 清空`relay-bin-group_replication_applier.index`索引日志并新建`relay-bin-group_replication_applier.000001`

`reset master` 和`reset slave` 通常用于**第一次创建或加入数据库集群时使用**。

是为了避免下次重启组复制插件功能时再次引导创建一个组，`group_replication_bootstrap_group`变量临时启用。当启动组复制功能后，将生成另一个通道`group_replication_applier`的相关文件（类似中继日志），并由applier线程（类似sql线程）重放到数据库。

#### 3.2.5查看组复制成员情况

```mysql
mysql> select * from performance_schema.replication_group_members;
```



###  3.3配置第二个节点d2.mgr.com

#### 3.3.1 创建复制用户

连接donor（加组连接对象，由种子节点提供）的通道凭据（**channel credentials**）

```shell
mysql> create user repl@'%' identified by 'P@ssword1!';
mysql> grant replication slave on *.* to repl@'%';
```

#### 3.3.2修改配置文件

` vim /etc/my.cnf`

```shell
#### Group Replication d2.mgr.com ####
server-id=20                     
gtid_mode=on                       
enforce_gtid_consistency=on       
binlog_format=row                  
binlog_checksum=none               
master_info_repository=TABLE       
relay_log_info_repository=TABLE    
log_slave_updates=on               
sync-binlog=1                      
group_replication_recovery_get_public_key=1

transaction_write_set_extraction=XXHASH64         
loose-group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" 
loose-group_replication_start_on_boot=off        
loose-group_replication_local_address="d2.mgr.com:20002"   
loose-group_replication_group_seeds="d1.mgr.com:20001,d2.mgr.com:20002,d3.mgr.com:20003"
loose-group_replication_ip_whitelist="172.16.10.0/24"	
```

重启服务

`systemctl restart mysqld`

#### 3.3.3 配置加组通道

```shell
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';

```

#### 3.3.4安装插件并加入到复制组

```mysql
mysql> install plugin group_replication soname 'group_replication.so';
mysql> reset master;
mysql> reset slave;
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';
mysql> start group_replication;
```

#### 3.3.5查看组复制成员情况

```mysql
mysql> select * from performance_schema.replication_group_members;
```



### 3.4添加第三个节点d3.mgr.com

#### 3.4.1 创建复制用户

连接donor（加组连接对象，由种子节点提供）的通道凭据（**channel credentials**）

```shell
mysql> create user repl@'%' identified by 'P@ssword1!';
mysql> grant replication slave on *.* to repl@'%';
```

#### 3.4.2修改配置文件

```shell
#### Group Replication d3.mgr.com ####
server-id=30                     
gtid_mode=on                       
enforce_gtid_consistency=on        
binlog_format=row                 
binlog_checksum=none               
master_info_repository=TABLE       
relay_log_info_repository=TABLE    
log_slave_updates=on               
sync-binlog=1                      
group_replication_recovery_get_public_key=1

transaction_write_set_extraction=XXHASH64        
loose-group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" 
loose-group_replication_start_on_boot=off       
loose-group_replication_local_address="d3.mgr.com:20003"   
loose-group_replication_group_seeds="d1.mgr.com:20001,d2.mgr.com:20002,d3.mgr.com:20003"
loose-group_replication_ip_whitelist="172.16.10.0/24"	
```

重启服务

`systemctl restart mysqld`

#### 3.4.3 配置加组通道

```shell
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';

```

重启服务

`systemctl restart mysqld`

#### 3.4.4安装插件并加入到复制组

```mysql
mysql> install plugin group_replication soname 'group_replication.so';
mysql> reset master;
mysql> reset slave;
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';
mysql> start group_replication;
```

#### 3.4.5查看组复制成员情况

```mysql
mysql> select * from performance_schema.replication_group_members;
```





## 4.参考

【1】[MySQL高可用之组复制技术(2)：配置单主模型的组复制](https://www.cnblogs.com/f-ck-need-u/p/9203154.html)  

【2】[Chapter 18 Group Replication](https://dev.mysql.com/doc/refman/8.0/en/group-replication.html)

【3】[MySQL 8.0.13 Group Replication Recovery Error MY-002061](https://stackoverflow.com/questions/53672176/mysql-8-0-13-group-replication-recovery-error-my-002061)

