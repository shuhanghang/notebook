# ProxySQL简单实现MGR读写分离



## 一. ProxySQL

### 1.1简介

ProxySQL是MySQL、Percona Server、MariaDB的高性能、高可用中间件，能实现的功能包括：

+ 允许**动态更新配置**。
+ 允许回滚无效的配置。

- 最基本的读/写分离，且方式有多种。
- 可定制基于用户、基于schema、基于语句的规则对SQL语句进行路由。换句话说，规则很灵活。基于schema和与语句级的规则，可以实现简单的sharding。
- 可缓存查询结果。虽然ProxySQL的缓存策略比较简陋，但实现了基本的缓存功能，绝大多数时候也够用了。此外，作者已经打算实现更丰富的缓存策略。
- 监控后端节点。ProxySQL可以监控后端节点的多个指标，包括：ProxySQL和后端的心跳信息，后端节点的read-only/read-write，slave和master的数据同步延迟性(replication lag)。

### 1.2 安装说明

[官方发行版](https://github.com/sysown/proxysql/releases)

[官方Docker仓库](https://hub.docker.com/r/proxysql/proxysql)

[官方手册](https://github.com/sysown/proxysql/wiki)

### 1.3 ProxySQL配置系统

#### 1.3.1 配置系统

ProxySQL是通过多级配置系统实现的，允许尽可能多地动态修改配置项，而无需重新启动ProxySQL进程。修改配置后将配置从运行时移动到内存，并根据需要持久保存到磁盘。

```txt
+-------------------------+
|         RUNTIME         |
+-------------------------+
       /|\          |
        |           |
        |           |
        |          \|/
+-------------------------+
|         MEMORY          |
+-------------------------+ _
       /|\          |      |\
        |           |        \ proxysql --initial
        |           |         \ 
        |          \|/         \
+-------------------------+  +-------------------------+
|          DISK           |  |       CONFIG FILE       |
+-------------------------+  +-------------------------+
```
**RUNTIME**表示处理请求的线程使用的ProxySQL的内存中数据结构，包含：

+ 全局变量中定义的实际值

+ 分组为主机组的后端服务器列表

+ 可以连接到代理的MySQL用户列表

**MEMORY**表示一个**内存数据库**，该数据库通过与MySQL兼容的接口公开。用户可以使用MySQL客户端连接到此接口，并查询各种ProxySQL配置表/数据库，包含：

 + mysql_servers： ProxySQL连接的后端服务器节点表

 + mysql_users： 连接到ProxySQL的用户及其授权表。请注意，**ProxySQL也将使用相同的凭据连接到后端服务器！**

 + mysql_query_rules：定义ProxySQL路由到后端服务器的查询规则表

 + global_variables：代理配置全局变量表（MySQL变量和ADMIN变量）

**DISK**：磁盘上的SQLite3数据库，默认位置为`$(DATADIR)/proxysql.db`，主要用于持久化保存配置。

**CONFIG FILE**：ProxySQL初始启动时读取的配置文件。

#### 1.3.2 加载保存

激活配置更改（RUNTIME）以及保存更改到磁盘（DISK），**任何更改在未加载到RUNITME之前，都不会生效**。

```mysql
LOAD MYSQL USERS TO RUNTIME;
SAVE MYSQL USERS TO DISK;
LOAD MYSQL SERVERS TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;
LOAD MYSQL QUERY RULES TO RUNTIME;
SAVE MYSQL QUERY RULES TO DISK;
LOAD MYSQL VARIABLES TO RUNTIME;
SAVE MYSQL VARIABLES TO DISK;

LOAD ADMIN VARIABLES TO RUNTIME;
SAVE ADMIN VARIABLES TO DISK;
```



## 二.  配置ProxySQL

### 2.1. 实验环境

mysql 8.0 默认使用caching_sha2_password授权插件，为了避免因通过中间件认证后端服务器时发生错误，这里使用的mysql版本为 5.7.29。关于组复制请参照[这里](https://shuhanghang.gitlab.io/2020/04/08/MySQL%E7%BB%84%E5%A4%8D%E5%88%B6/)。

|   系统   | 默认角色 |    主机名     |      IP      |    软件版本     |
| :------: | :------: | :-----------: | :----------: | :-------------: |
| CentOS 7 | ProxySQL | proxy.mgr.com | 172.16.10.60 | ProxySQL 2.0.10 |
| CentOS 7 |  Master  |  d1.mgr.com   | 172.16.10.59 |  mysql 5.7.29   |
| CentOS 7 |  Node1   |  d2.mgr.com   | 172.16.10.58 |  mysql 5.7.29   |
| CentOS 7 |  Node2   |  d3.mgr.com   | 172.16.10.57 |  mysql 5.7.29   |

### 2.2 读写分离

#### 2.2.1 初始化ProxySQL

```shell
[root@proxy ~]# proxysql --initial
```

ProxySQL`读取`proxysql.cnf文件并加载到内存数据库，启动后会监听两个端口，默认为6032和6033。6032端口是ProxySQL的管理端口；6033是ProxySQL对外提供服务的端口。

#### 2.2.2 连接ProxySQL管理端口

```shell
[root@proxy ~]# mysql -uadmin -padmin -P6032 -h127.0.0.1 --prompt 'admin> '
```

#### 2.2.3 添加后端服务器到主机组

```shell
admin> insert into mysql_servers(hostgroup_id,hostname,port) values(10,'172.16.10.59',3306);
admin> insert into mysql_servers(hostgroup_id,hostname,port) values(10,'172.16.10.58',3306);
admin> insert into mysql_servers(hostgroup_id,hostname,port) values(10,'172.16.10.57',3306);
```

ProxySQL内部使用的SQLite3数据库引擎，所以这里可以不用USE或"."来选择数据库对象。

 查看并加载到RUNTIME ,保存到disk

```shell
admin> select * from mysql_servers\G;
admin> load mysql servers to runtime;
admin> save mysql servers to disk;
```

#### 2.2.4 添加监控后端服务器账户
添加节点之后，还需要监控后端节点。对于后端是主从复制的环境来说，这是必须的，因为ProxySQL需要通过每个节点的`read_only`值来自动调整它们是属于读组还是写组。

+ 后端MySQL Server上创建

    ```mysql
    admin> create user monitor@'172.16.%.%' identified by 'P@ssword1!';
    admin> grant all on *.* to monitor@'172.16.%.%';	
    ```
    
+ ProxySQL添加连接后端服务器器监控账号

    ```mysql
    admin> set mysql-monitor_username='monitor';
    admin> set mysql-monitor_password='P@ssword1!';
    ```
    
+ 加载到RUNTIME ，保存到DISK

    ```mysql
    admin> load mysql variables to runtime;
    admin> save mysql variables to disk;
    ```
    
+ 查看监控结果
  
  查看连接日志
  
  ```mysql
  admin> select * from mysql_server_connect_log;
  ```
  
  查看ping节点日志
  
  ```mysql
  admin> select * from mysql_server_ping_log;    
  ```

#### 2.2.5 添加读写组
在ProxySQL上添加写组（10），读组（20）

```mysql
admin> insert into mysql_replication_hostgroups(writer_hostgroup,reader_hostgroup) values(10,20);
```

查看后端服务器MySQL server所在组（默认都在10写组）

```mysql
admin> select hostgroup_id,hostname,port,status,weight from mysql_servers; 
```

加载到RUNTIME并保存到disk

```mysql
admin> load mysql servers to runtime;
admin> save mysql servers to disk;
```

**一加载后Monitor模块就会开始监控后端的read_only值，当监控到read_only值后，就会按照read_only的值将某些节点自动移动到读/写组。**

在ProxySQL上查看加载后后端服务器读写组

```mysql
admin> select hostgroup_id,hostname,port,status,weight from mysql_servers;
```

#### 2.2.6 配置mysql_users

客户端连接到ProxySQL与ProxySQL连接到MySQL Server使用同样的账号，主要用来接受客户端的连接以及操作MySQL Server。

在MySQL Server上配置后端proxysql用户

```mysql
mysql> create user proxysql@'172.16.%.%'  identified by 'proxysql'; 
mysql> grant all on *.* to proxysql@'172.16.%.%';
```

在ProxySQL上添加ProxySQL用户

```mysql
admin> insert into mysql_users(username,password,default_hostgroup) values('proxysql','proxysql',10);
```

加载到RUNTIME ，保存到DISK

```mysql
admin> load mysql users to runtime;
admin> save mysql users to disk;
```

查看ProxySQL用户表

```mysql
admin> select * from mysql_users\G;
```

#### 2.2.7 配置读写分离规则

将select语句分配到`hostgroup_id=20`的读组，其他分配到10写组。由于select语句中有一个特殊语句`SELECT...FOR UPDATE`它会申请写锁，所以应该路由到`hostgroup_id=10`的写组。

```mysql
admin> insert into mysql_query_rules(rule_id,active,match_digest,destination_hostgroup,apply)
VALUES (1,1,'^SELECT.*FOR UPDATE$',10,1), (2,1,'^SELECT',20,1);
```

加载到RUNTIME ，保存到DISK

```mysql
admin> load mysql query rules to runtime;
admin> save mysql query rules to disk;
```

验证，多次执行观察server_id值变化

```mysql
[root@proxy ~]# mysql -uproxysql -p'proxysql' -P6033 -h127.0.0.1 -e 'select @@server_id'
```



## 三. 参考

【1】[MySQL中间件之ProxySQL(2)：初试读写分离](https://www.cnblogs.com/f-ck-need-u/p/9278839.html)

【2】[Official ProxySQL Documentation](https://proxysql.com/documentation/)

