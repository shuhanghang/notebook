# MySQL组复制

## 一. 什么是MGR

MGR(MySQL Group Replication)是MySQL官方在MySQL  5.7.17版本中以插件形式推出的主从复制高可用技术，它基于原生的主从复制，将各节点归入到一个组中，通过组内节点的通信协商(组通信协议基于Paxos算法)，实现数据的强一致性，具有弹性复制、高可用、主从替换、自动加组等等功能。

### 1.1 MySQL组复制协议

<img src="https://s1.ax1x.com/2020/04/08/GRNulj.png" alt="Replication Protocol" style="zoom: 33%;" />

这3个节点互相通信，每当有读写事件发生，都会向其他节点广播该事件，经过冲突检测后写入到binglog日志然后提交。

- receiver的作用类似于io线程，用于接收组内个节点之间传播的消息和事务。也用于接收外界新发起的事务。
- applier的作用类似于sql线程，用于应用relay log中的记录。不过，组复制的relay log不再是relay log，而是这里的组复制relay log：`relay-log-group_replication_applier.00000N`。
- certifier的作用在receiver接收到消息后，验证是否有并发事务存在冲突问题。冲突检测通过后，这条消息就会写入到组复制的relay log中，等待applier去应用。

这些节点可以是单主模型的(single-primary)，也可以是多主模型的(multi-primary)。**单主模型只有一个主节点可以接受写操作，主节点故障时可以自动选举主节点**。**多主模型下所有节点都可以接受写操作**，所以没有master-slave的概念。



### 1.2 组复制模式

MySQL的组复制可以配置为**单主模型**和**多主模型**两种工作模式，它们都能保证MySQL的高可用。以下是两种工作模式的特性简介：

- 单主模型：从复制组中众多个MySQL节点中自动选举一个master节点，只有master节点可以写，其他节点自动设置为read only。当master节点故障时，会自动选举一个新的master节点，选举成功后，它将设置为可写，其他slave将指向这个新的master。
- 多主模型：复制组中的任何一个节点都可以写，因此没有master和slave的概念，只要突然故障的节点数量不太多，这个多主模型就能继续可用。

虽然多主模型的特性很诱人，但缺点是要配置和维护这种模式，必须要深入理解组复制的理论，更重要的是，多主模型限制较多，其一致性、安全性还需要多做测试。





## 二. 配置单主模式的组复制

### 2.1 实验环境

实验前请在hosts文件中设置好解析，或者局域网内搭建DNS服务器（推荐docker搭建[dnsmasq](https://hub.docker.com/r/jpillora/dnsmasq)）。当然也可以不设置解析，直接在my.cnf文件中使用IP地址即可。

|   系统   |   主机名   |      IP      |  MySQL版本   |
| :------: | :--------: | :----------: | :----------: |
| CentOS 7 | d1.mgr.com | 172.16.10.59 | mysql 8.0.19 |
| CentOS 7 | d2.mgr.com | 172.16.10.58 | mysql 8.0.19 |
| CentOS 7 | d3.mgr.com | 172.16.10.57 | mysql 8.0.19 |



### 2.2  配置第一个节点d1.mgr.com

#### 2.2.1 创建复制用户

连接donor（加组连接对象，由种子节点提供）的通道凭据（**channel credentials**）

```mysql
mysql> create user repl@'%' identified by 'P@ssword1!';
mysql> grant replication slave on *.* to repl@'%';
```

#### 2.2.2 修改配置文件

` vim /etc/my.cnf`

```shell
server-id=10                       # 必须
gtid_mode=ON                       # 必须，开启GTID模式
enforce_gtid_consistency=ON        # 必须，不允许事务违背GTID的一致性
binlog_format=ROW                  # 必须，以行方式记录
binlog_checksum=NONE               # 必须，关闭事件校验
master_info_repository=TABLE       # 必须，记录加入master服务器信息到mysql.slave_master_info
relay_log_info_repository=TABLE    # 必须，记录节点中继日志的位置到mysql.slave_relay_log_info
log_slave_updates=ON               # 必须，更新节点中继日志
sync_binlog=1                      # 建议，事务同步到binlog日志
group_replication_recovery_get_public_key=ON      # 必须，未使用SSL加密

transaction_write_set_extraction=XXHASH64         # 必须，事务写入算法
loose-group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" #必须，或使用uuidgen命令生成
loose-group_replication_start_on_boot=OFF         # 建议，关闭启动自开启复制
loose-group_replication_local_address="d1.mgr.com:20001"   # 必须，组复制本机地址及端口
loose-group_replication_group_seeds="d1.mgr.com:20001,d2.mgr.com:20002,d3.mgr.com:20003" # 必须，组复制种子地址及端口
loose-group_replication_ip_whitelist="172.16.10.0/24"	#建议，加组白名单
```

重启服务

`systemctl restart mysqld`

重启服务后生成通道的relay log文件，`group_replication_recovery`通道的relay log用于新节点加入组时，**当新节点联系上donor后，会从donor处以异步复制的方式将其binlog复制到这个通道的relay log中，新节点将从这个recovery通道的relay log中恢复数据。**

#### 2.2.3 配置加组通道

```mysql
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';
```

#### 2.2.4 安装插件并启用组复制

```mysql
mysql> install plugin group_replication soname 'group_replication.so';
mysql> reset master;
mysql> reset slave;
mysql> set @@global.group_replication_bootstrap_group=ON;
mysql> start group_replication;
mysql> set @@global.group_replication_bootstrap_group=OFF;
```

`reset master`清空`binlog.index`索引日志并新建`binlog.000001`

`reset slave` 清空`relay-bin-group_replication_applier.index`索引日志并新建`relay-bin-group_replication_applier.000001`

`reset master` 和`reset slave` 通常用于**第一次创建或加入数据库集群时使用**。

是为了避免下次重启组复制插件功能时再次引导创建一个组，`group_replication_bootstrap_group`变量临时启用。当启动组复制功能后，将生成通道的`binlog`和`group_replication_applier`（类似中继日志）相关文件。

#### 2.2.5 查看组复制成员情况

```mysql
mysql> select * from performance_schema.replication_group_members;
```



###  2.3配置第二个节点d2.mgr.com
在新节点加入组之前，应该先通过备份恢复的方式，从组中某节点上备份目前的数据到新节点上，然后再让新节点去加组，这样加组的过程将非常快，且能保证不会因为purge的原因而加组失败。
#### 2.3.1 创建复制用户

连接donor（加组连接对象，由种子节点提供）的通道凭据（**channel credentials**）

```shell
mysql> create user repl@'%' identified by 'P@ssword1!';
mysql> grant replication slave on *.* to repl@'%';
```

#### 2.3.2 修改配置文件

` vim /etc/my.cnf`

```shell
#### Group Replication d2.mgr.com ####
server-id=20                     
gtid_mode=ON                       
enforce_gtid_consistency=ON       
binlog_format=ROW                  
binlog_checksum=NONE               
master_info_repository=TABLE       
relay_log_info_repository=TABLE    
log_slave_updates=ON               
sync_binlog=1                      
group_replication_recovery_get_public_key=ON

transaction_write_set_extraction=XXHASH64         
loose-group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" 
loose-group_replication_start_on_boot=OFF        
loose-group_replication_local_address="d2.mgr.com:20002"   
loose-group_replication_group_seeds="d1.mgr.com:20001,d2.mgr.com:20002,d3.mgr.com:20003"
loose-group_replication_ip_whitelist="172.16.10.0/24"	
```

重启服务

`systemctl restart mysqld`

#### 2.3.3 配置加组通道

```shell
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';

```

#### 2.3.4 安装插件并加入到复制组

```mysql
mysql> install plugin group_replication soname 'group_replication.so';
mysql> reset master;
mysql> reset slave;
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';
mysql> start group_replication;
```

#### 2.3.5 查看组复制成员情况

```mysql
mysql> select * from performance_schema.replication_group_members;
```



### 2.4 添加第三个节点d3.mgr.com

#### 2.4.1 创建复制用户

连接donor（加组连接对象，由种子节点提供）的通道凭据（**channel credentials**）

```shell
mysql> create user repl@'%' identified by 'P@ssword1!';
mysql> grant replication slave on *.* to repl@'%';
```

#### 2.4.2 修改配置文件

```shell
#### Group Replication d3.mgr.com ####
server-id=30                     
gtid_mode=ON                       
enforce_gtid_consistency=ON        
binlog_format=ROW                 
binlog_checksum=NONE              
master_info_repository=TABLE       
relay_log_info_repository=TABLE    
log_slave_updates=ON               
sync_binlog=1                      
group_replication_recovery_get_public_key=ON

transaction_write_set_extraction=XXHASH64        
loose-group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" 
loose-group_replication_start_on_boot=OFF       
loose-group_replication_local_address="d3.mgr.com:20003"   
loose-group_replication_group_seeds="d1.mgr.com:20001,d2.mgr.com:20002,d3.mgr.com:20003"
loose-group_replication_ip_whitelist="172.16.10.0/24"	
```

重启服务

`systemctl restart mysqld`

#### 2.4.3 配置加组通道

```shell
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';

```

#### 2.4.4 安装插件并加入到复制组

```mysql
mysql> install plugin group_replication soname 'group_replication.so';
mysql> reset master;
mysql> reset slave;
mysql> change master to master_user='repl',master_password='P@ssword1!' for channel 'group_replication_recovery';
mysql> start group_replication;
```

#### 2.4.5 查看组复制成员情况

```mysql
mysql> select * from performance_schema.replication_group_members;
```





## 三. 参考

【1】[MySQL高可用之组复制技术(2)：配置单主模型的组复制](https://www.cnblogs.com/f-ck-need-u/p/9203154.html)  

【2】[Chapter 18 Group Replication](https://dev.mysql.com/doc/refman/8.0/en/group-replication.html)

【3】[MySQL 8.0.13 Group Replication Recovery Error MY-002061](https://stackoverflow.com/questions/53672176/mysql-8-0-13-group-replication-recovery-error-my-002061)
