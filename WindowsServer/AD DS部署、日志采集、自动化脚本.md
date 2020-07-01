## 一. AD DS简介

Active Directory域服务 (AD DS) 可存储有关网络上的用户、计算机和其他资源的信息。AD DS  可帮助管理员安全地管理此信息。还便于在用户中实现共享和协作。AD DS 是启用了目录的应用程序（如 Microsoft Exchange  Server）和其他 Windows Server 技术（如组策略）所必需的。

[AD域登录认证过程](https://blog.csdn.net/wulantian/article/details/42418231)



## 二. 服务器

#### 1.DC服务器

|    主机名    |    主机IP     |  角色   |       系统        |
| :----------: | :-----------: | :-----: | :---------------: |
| ad1.test.com | 192.168.10.10 | master1 | WindowsServer2019 |
| ad2.test.com | 192.168.10.11 | master2 | WindowsServer2019 |

1. [AD DS服务安装](https://blog.51cto.com/lumay0526/2051317#%E6%B7%BB%E5%8A%A0%E5%9F%9F%E6%8E%A7%E5%88%B6%E5%99%A8)

2. 两台DC安装Winlogbeat

#### 2.ELK服务器

请使用三台及以上的es来搭建群集，我这里只是实现数据的冗余并没有实现高可用

| 主机名 |    主机IP     |  角色   |      系统      |
| :----: | :-----------: | :-----: | :------------: |
|  ELK   | 192.168.20.10 | master1 | CentOS7.5.1804 |
|  ELK2  | 192.168.20.11 |  node1  | CentOS7.5.1804 |



## 三. 组织架构

[![](https://upload-images.jianshu.io/upload_images/1641063-e9aeba01b4c44c1b.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)](https://imgchr.com/i/No4sYT)



## 四. 配置常规组策略
#### 1. 自动锁屏（默认开启）
组策略管理编辑器 => 用户配置 => 策略 => 管理模板 => 控制面板 => 个性化

`启用屏幕保护程序` 配置为已启用
`阻止更改屏幕保护程序` 配置为已启用
`带密码的屏幕保护程序` 配置为已启用
`屏幕保护程序超时` 配置为已启用 秒：300

#### 2.账号密码设置（默认开启）

组策略管理器编辑器 => 计算机配置 => 策略 => Windows 设置 => 安全设置 => 账户策略 => 密码策略

`密码必须符合复杂性要求`：已启用

`密码长度最小值`：8个字符

`密码最短使用期限`：0

`密码最长使用期限`：0

`强制密码历史`：没有定义

#### 3.账户锁定（默认开启）

组策略管理器编辑器 => 计算机配置 => 策略 => Windows 设置 => 安全设置 => 账户策略 => 账户锁定策略

`账户锁定时间`  设置为0，需管理员手动解锁

`账户锁定阀值` 设置为8，用户连续输入错误8次则该用户被锁定

`重置账户锁定计数器` 设置为30分钟之后，表示在8次内输入的次数计数器在30分钟后重置为0

#### 4.登录时间限制（暂未开启）

用户属性 => 账户 => 登录时间

#### 5.用户登录指定主机（修改密码后自动绑定）

用户属性 => 账户 => 登录到 => 下列计算机



#### 6.USB禁用（暂未开启）

组策略管理编辑器 => 用户配置 => 策略 => 管理模板 =>  系统 => 可移动存储访问 

`可移动磁盘：拒绝读取权限` 配置已启动

#### 7.桌面设置（暂未使用）

组策略管理编辑器 => 用户配置 => 策略 => 管理模板 => 桌面 => 桌面

`桌面墙纸` 创建共享，将设置的用户或组添加到照片上

注：组策略设置用户桌面配置后，用户无法再手动设置桌面

#### 8.下发证书（暂未使用）

计算机配置 => 策略 => Windows设置 => 安全设置 => 公钥策略 => 受信任的根证书颁发机构 => 导入只读共享目录下的证书

#### 9.msi软件下发（暂未使用）

组策略管理编辑器 => 用户配置 => 策略 => 软件设置 => 软件安装

新建数据包 =>  选择共享目录下的msi文件 => 部署类型为“ 已分配” => 部署选项“在登录时安装此应用程序”

#### 10.AD用户本地管理员权限（默认开启）

组策略管理编辑器 => 用户配置 => 首选项 => 控制面板设置 => 本地用户和组 => 新建本地组
操作：更新
组名：Administrators
添加当前用户、删除所有成员用户、删除所有成员组
添加Domain Adminis 组



## 五. DC安全

AD DS 服务涉及到的固定[端口](https://docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2008-R2-and-2008/dd772723(v=ws.10)?redirectedfrom=MSDN)，同事其中组策略和RPC会使用动态TCP和UDP端口，为了保证服务的可靠性，我们使用防火墙默认开通的AD DS服务的相关规则，关闭其他非相关服务，同时入站对389端口、445端口、3389端口等做IP地址的限制。

固定TCP端口：389,636,3268,3269,88,53,445,445,25,135,5722,464,138,9369,139
固定UDP端口：389,88,53,445,123,464,138,137

#### 1. 开启AD DC防火墙

#### 2. 关闭其他非相关服务规则，关键端口IP限制

135、389、445、636、3389端口对指定网段放通



## 六. Windows安全事件日志收集

#### 1. DC开启身份验证服务组策略

通常用户每次在登录域主机时，都会向DC的DS进行身份认证并由TGS颁发服务请求票据（TGT），根据事件的event.code和winlog.event_data.Status可以筛选出用户登录成功和失败以及非法登录。

参考[Windows Security Log Events](https://www.ultimatewindowssecurity.com/securitylog/encyclopedia/default.aspx)，这里需要用到的域主机登录事件：

|      登录情况分类      | event.code | winlog.event_data.Status |
| :--------------------: | :--------: | :----------------------: |
|     非AD用户名登录     |    0x6     |           4768           |
| AD用户名登录，密码错误 |    0x18    |           4771           |
| AD用户名登录，密码正确 |    0x0     |           4768           |
|    一个帐户无法登录    |            |           4625           |
|  尝试使用显式凭据登录  |            |           4648           |
|    用户帐户已被锁定    |            |           4740           |
|    试图更改帐户密码    |            |           4723           |

+ 组策略管理编辑器 => 计算机配置 => 策略 => Windows 设置 => 安全设置 => 高级审查策略配置 => 审核策略 => 账户登录 => 审核Kerberos 身份验证服务 => 勾选 “成功” 和“失败”
+ 组策略管理编辑器 => 计算机配置 => 策略 => Windows 设置 => 安全设置 => 高级审查策略配置 => 审核策略 => 账户管理=> 审核用户账户管理 => 勾选 “成功” 和“失败”
+ 组策略管理编辑器 => 计算机配置 => 策略 => Windows 设置 => 安全设置 => 高级审查策略配置 => 审核策略 => 登录/注销 => 审核登录 => 勾选 “成功” 和“失败”
+ 打开CMD窗口输入 `gpupdate  /force` 强制刷新组策略
+ 使用域用户账号登录已加入域的主机，在AD DC上查看 事件查看器 => Windows 日志 => 安全

#### 2. 安装Winlogbeat + Logstash + Elasticsearch + Kibana

1. [官网下载](https://www.elastic.co/cn/downloads/) Winlogbeat解压包和其他RPM安装

2. 配置Winlogbeat客户端

   将Winlogbeat 收集的日志以负载均衡的方式发送到Logstash

   ```yml
   output.logstash:
     # The Logstash hosts
     hosts: ["192.168.20.11:5044","192.168.20.10:5044"]
     loadbalance: true
   ```

   .\winlogbeat.exe run 或  安装启动winlogbeat服务

3. 配置logstash，以192.168.20.10为例

```shell
[root@ELK ~]# vim  /etc/logstash/conf.d/windowsServerAD_events.conf
```

```yaml
input {
  beats {
    port => 5044
  }
}

# Active Directory Kerberos pre-authentication failed  
# Add field user_ip to store ip of host
filter {
    if [winlog][channel] == "Security" and [winlog][event_id] == 4771  and [winlog][event_data][IpAddress] == "::1" {
        mutate {
	    add_field => {"user_ip" => "%{[host][ip]}"}
  }
 }
}

# Active Directory A Kerberos authentication ticket (TGT) was requested
# Add field user_ip to store ip of host
filter {
    if [winlog][channel] == "Security" and [winlog][event_id] == 4768 and [winlog][event_data][IpAddress] == "::1" {
        mutate {
	    add_field  => {"user_ip" => "%{[host][ip]}"}
  }
 }
}

# Filter ip of client 
filter {
    if  "ffff" in [winlog][event_data][IpAddress] {
        grok {
            match => {"[winlog][event_data][IpAddress]" => "%{IPV4:user_ip}"}
   }
 }
}

# Output to elasticsearch
output {
  if [winlog][channel] == "Security" and ([winlog][event_id] == 4771 or [winlog][event_id] == 4723 ) and "192.168.20" not in [user_ip] {
  elasticsearch {
    hosts => ["http://192.168.20.10:9200"]
    index => "%{[@metadata][beat]}-%{[@metadata][version]}-%{+YYYY.MM.dd}"
    #user => "elastic"
    #password => "changeme"
  }
 } 

  # Get useful events
  else if [winlog][channel] == "Security" and [winlog][event_id] == 4768 and "$" not in [winlog][event_data][TargetUserName] and "TEST" in [winlog][event_data][TargetDomainName]{
    elasticsearch {
    hosts => ["http://192.168.20.10:9200"]
    index => "%{[@metadata][beat]}-%{[@metadata][version]}-%{+YYYY.MM.dd}"
    #user => "elastic"
    #password => "changeme"
  }
 }
   
 else if [winlog][channel] == "Security" and [winlog][event_id] == 4625 and "$" not in [winlog][event_data][TargetUserName] {
  elasticsearch {
    hosts => ["http://192.168.20.10:9200"]
    index => "%{[@metadata][beat]}-%{[@metadata][version]}-%{+YYYY.MM.dd}"
    #user => "elastic"
    #password => "changeme"
  }
 }

 else if [winlog][channel] == "Security" and [winlog][event_id] == 4740 and "$" not in [winlog][event_data][TargetUserName] {
  elasticsearch {
    hosts => ["http://192.168.20.10:9200"]
    index => "%{[@metadata][beat]}-%{[@metadata][version]}-%{+YYYY.MM.dd}"
    #user => "elastic"
    #password => "changeme"
  }
 }

 else if [winlog][channel] == "Security" and [winlog][event_id] == 4648 and "$" not in [winlog][event_data][TargetUserName] {
  elasticsearch {
    hosts => ["http://192.168.20.10:9200"]
    index => "%{[@metadata][beat]}-%{[@metadata][version]}-%{+YYYY.MM.dd}"
    #user => "elastic"
    #password => "changeme"
  }
 }

}
```

4. 配置 Elasticsearch，以192.168.20.10为例

```shell
[root@ELK ~]# vim /etc/elasticsearch/elasticsearch.yml
cluster.name: elk-cluster
node.name: ELK
network.host: 192.168.20.10
discovery.seed_hosts: ["192.168.20.10", "192.168.20.11"]
cluster.initial_master_nodes: ["192.168.20.10","192.168.20.11"]
```

5. 配置Kibana ，以192.168.20.10为例

```shell
[root@ELK ~]# vim /etc/kibana/kibana.yml
server.host: "192.168.20.10"
i18n.locale: "zh-CN"
```

6. 启动服务

```shell
[root@ELK ~]# systemctl start logstash elasticsearch kibana
```

#### 3. 配置 kibana dashboard

1. kibana可视化数据筛选

   ```yml
   1.0 当日域用户登录域主机失败记录
   winlog.event_data.Status:0x18                                            
   event.code:4771   
   1.1 当日域用户登录域主机失败时序图
   winlog.event_data.Status.keyword : "0x6" or (event.code: 4771 and winlog.event_data.Status.keyword : "0x18")
   ---------------------------------------------
   2.0 当日错误域用户登录域主机记录
   winlog.event_data.Status:0x6                                            
   event.code:4768   or  event.code:4771
   ----------------------------------------------
   3.0 当日用户锁定记录
   event.code:4740
   ----------------------------------------------
   4.0 当日登录DC失败详细记录
   event.code:4625
   ----------------------------------------------
   4.1 当日登录DC成功详细记录（使用显式凭据登录）
   event.code:4648   winlog.event_data.Status:0x0  
   ```

2. 配置Kibana dashboard可视化界面

[![](https://upload-images.jianshu.io/upload_images/1641063-35d86c73c63f6c9b.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)](https://imgchr.com/i/No4fmR)

当日域用户登录域主机失败记录：记录当日用户登录域主机或域控的失败次数，该数据可视为账户锁定和周期性尝试登录的依据

当日错误域用户登录域主机记录：统计使用非AD域账户登录域主机的数据

当日用户锁定记录：记录域用户使用错误密码尝试登录连续超过8次，账号被锁定

当日登录DC失败详细记录：记录当日登录域控制器失败的情况

当日登录DC成功详细记录：记录当日登录域控制器成功的情况



## 七. DC Python自动化脚本

#### 1.主机绑定到用户（用户-主机）

1. 获取用户第一次登录修改密码成功，logstash收集修改密码事件4723到Elasticsearch

2. Python脚本周期读取Elasticsearch日志，当读检索到修改密码事件后获取用户名、IP、主机名，并将event.code 修改为666666（用于kibana展示），最后将主机绑定到用户下

3. Python绑定脚本，以脚本运行在192.168.20.10（Centos7）为例，请提前安装[第三方wmi rpm包]([https://centos.pkgs.org/7/atomic-x86_64/wmi-1.3.14-4.el7.art.x86_64.rpm.html](https://centos.pkgs.org/7/atomic-x86_64/wmi-1.3.14-4.el7.art.x86_64.rpm.html)
)

   ```python
   #! /usr/bin/env python3
   # -*- coding: utf-8 -*-
   # 使用前建议关闭windows客户端域防火墙
   
   import logging
   import logging.handlers
   import wmi_client_wrapper as wmi
   from elasticsearch import Elasticsearch
   from ldap3 import Server, Connection, ALL, MODIFY_REPLACE
   
   ELASTIC_PORT = 9200
   ELASTIC_IP = "192.168.20.10"
   INDEX_NAME = "winlogbeat*"
   DC_SERVER = "192.168.10.10"
   AD_ADMIN_USER = r"test\PythonScript"
   AD_ADMIN_PASS = "12345678"
   logger = None
   
   # 日志配置：记录器、处理程序、过滤器和格式化程序
   def init_logger():
       global logger
   
       # 创建记录器
       logger = logging.getLogger('bindhost_aduser')
       # 指定记录器处理的最低严重性日志消息
       logger.setLevel(logging.INFO)
   
       # 定义处理程序,并添加到记录器
       logger_hander = logging.handlers.RotatingFileHandler(
           filename="/var/log/bindhost_aduser/bindhost_aduser.log", maxBytes=20*1024, backupCount=10)
   
       # logger_hander = logging.StreamHandler()
       logger.addHandler(logger_hander)
   
       # 格式化程序，添加到处理程序
       formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
       logger_hander.setFormatter(formatter)
   
   
   # Python WMI 远程登录获取主机名
   def get_hostName(userIP):
       try:
           wmic = wmi.WmiClientWrapper(
               username=AD_ADMIN_USER, password=AD_ADMIN_PASS, host=userIP)
           hostName = wmic.query(
               "select * from Win32_OperatingSystem")[0]["CSName"]
           if "ad1" != hostName.lower() and "ad2" != hostName.lower():
               return hostName
           else:
               logger.info(f"获取主机名为{hostName}")
               return 0
       except:
           # 记录到日志中
           logger.warning(f"wmi登录主机:{userIP} 失败！")
           return 0
   
   # 获取更改密码用户的IP地址
   def query_userIP(indexName, userName):
   
       # 查询修改密码用户的登录的主机IP
       QUERY_USER_IP = {
           "query": {
               "bool": {
                   "must": [
                       {
                           "term": {
                               "event.code": 4768
                           }
                       },
                       {
                           "term": {
                               "winlog.event_data.TargetUserName": userName
                           }
                       }
                   ]
               }
           },
           "sort": [{"@timestamp": {"order": "desc"}}]
       }
   
       try:
           queryUserIP = es.search(
               index=indexName, body=QUERY_USER_IP)
           lenResult = len(queryUserIP['hits']['hits'])
           if lenResult >= 1:
               userIP = queryUserIP['hits']['hits'][0]['_source']['user_ip']
               return userIP
       except Exception as e:
           # 记录到日志
           logger.exception(e)
           return 0
   
   # 获取更改密码用户名
   def query_userName(indexName):
       # 查询用户修改密码成功事件
       QUERY_USER = {
           "query": {
               "bool": {
                   "must": [
                       {
                           "term": {
                               "event.code": 4723
                           }
                       },
                       {
                           "term": {
                               "winlog.keywords.keyword": '审核成功'
                           }
                       },    
                       {  
                            "range": {
                               "@timestamp":{
                                   "gt": "now-30m"
                               }
                           }
                       }
                   ]
               }
           },
           "sort": [{"@timestamp": {"order": "desc"}}],
           "size": 10
       }
   
       # 绑定成功修改时间ID，用户kibana展示绑定成功
       SUCCESS_EVENT = {
           "doc": {
               "event": {
                   "code": 666666
               }
           }
       }
   
       try:
           queryUser = es.search(index=indexName, body=QUERY_USER)
           lenResult = len(queryUser['hits']['hits'])
           if lenResult >= 1:
               # 一次获取最近10个
               users_list = queryUser['hits']['hits']
               for user in users_list:
                   logIndex = user['_index']
                   logId = user['_id']
                   userName = user['_source']['winlog']['event_data']['TargetUserName']
   
                   logger.info(f"捕捉AD用户:{userName} 在:{user['_source']['@timestamp']} 修改密码！")
   
                   # 调用query_userIP获取用户登录IP
                   userIP = query_userIP(indexName, userName)
                   if userIP:
                       # 调用get_hostName登录主机获取主机名
                       hostName = get_hostName(userIP)
                       if hostName:
                           bind_result = bind_hostName(userName, hostName)
                           if bind_result:
                               # 修改事件ID,用于kibana展示修改成功的用户名和主机名,主要用来检查是否绑定
                               es.update(index=logIndex, doc_type="_doc",id=logId, body=SUCCESS_EVENT)
   
       except Exception as e:
           # 记录到日志
           logger.exception(e)
   
   
   # 将新用户绑定到修改密码的主机上,默认运维部人员(devops)不用绑定
   def bind_hostName(userName, hostName):
       server = Server(DC_SERVER, get_info=ALL)
       conn = Connection(server, AD_ADMIN_USER, AD_ADMIN_PASS, auto_bind=True)
       try:
           conn.search(search_base="ou=test,dc=test,dc=io",
                       search_filter=f'(sAMAccountName={userName})', attributes=['cn', 'userWorkstations'])
           # 查找用户DN，如果用户未曾绑定过主机则绑定主机
           user_dn = conn.response[0]["dn"]
        user_host = conn.response[0]["attributes"]["userWorkstations"]
           if user_host == [] and "devops" not in user_dn:
            conn.modify(user_dn, {'userWorkstations': [
                           (MODIFY_REPLACE, [hostName])]})
               if conn.result['description'] == "success":
                   # 打印日志
                   logger.info(f"绑定主机:{hostName} 到用户:{userName} 状态:{conn.result['description']}")
           else:
               logger.info(f"用户：{userName} 已经绑定或运维人员不需要绑定！")
           return 1
   
       except Exception as e:
           # 打印日志
           logger.exception(e)
           return 0 
   
   if __name__ == "__main__":
       init_logger()
       es = Elasticsearch(
           [{'host': ELASTIC_IP, 'port': ELASTIC_PORT}], timeout=3600)
       query_userName(INDEX_NAME)
   ```
   
   
   
   #### 2.Python批量创建、删除用户脚本




## 八.主机加入域及用户登录

#### 1.加域及初始化配置

1. 确保分配到了DHCP下发的地址，DNS服务器为192.168.10.10或192.168.10.11
2. 设置本地管理员账号密码
3. 计算机 -> 属性 -> 高级系统设置 -> 计算机名 -> 更改 -> 隶属于 -> 域 -> test.com -> 输入域管理账号 -> 确定 -> 应用 -> 重启主机
4. 关闭本地域防火墙

#### 2.AD用户登录

1. 用户名为用户的拼音全拼如张三：zhangsan
2. 初始密码为12345678，首次登录会提示修改密码（必须符合密码复杂度要求），修改密码后即可登录
3. 首次登录后，如果安装软件或卸载软件等提示没有权限，注销再次登录即可