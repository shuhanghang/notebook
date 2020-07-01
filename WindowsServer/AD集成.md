# AD集成

## 一. Gitlab LDAP

### 1.1 Gitlab配置 

```shell
[root@localhost ~]# vim /etc/gitlab/gitlab.rb
```

```yml
gitlab_rails['ldap_enabled'] = true
gitlab_rails['ldap_servers'] = {
'main' => {
  'label' => 'AD',                                # Gitlab AD认证界面的标签
  'host' =>  '172.16.10.6',                       # DC 服务器地址
  'port' => 389,                                   
  'uid' => 'sAMAccountName',                      # Gitlab使用登录域用户属性
  'encryption' => 'plain',                        # AD DC 认证传输的加密方法     
  'bind_dn' => 'CN=Administrator,CN=Users,DC=test,DC=io',   #绑定管理员的dn
  'password' => 'password',                     # 管理员密码
  'allow_username_or_email_login': true,        # 允许用户使用@的方式登录
  'block_auto_created_users': true,             # 新建用户首次登录Gitlab是否被锁定
  'active_directory' => true,                   # 此设置指定LDAP服务器是否为AD服务器
  'base' => 'OU=test,DC=test,DC=io',            # 搜索指定组织下的用户
  'user_filter' =>'memberOf=CN=GITLAB_USERS,CN=Users,DC=test,DC=io' # 过滤LDAP用户
  }
}
```

```shell
[root@localhost ~]# gitlab-ctl reconfigure
```

检查测试ldap配置

```shell
[root@localhost ~]# gitlab-rake gitlab:ldap:check
```

如果从LDAP服务器中删除了用户，则该用户也会在GitLab中被阻止。用户将立即被阻止登录。但是，LDAP检查缓存时间为一小时（请参阅注释），这意味着已经登录或通过SSH使用Git的用户仍然可以访问GitLab最多一个。小时。在GitLab管理区域中手动阻止用户以立即阻止所有访问。

### 1.2 Gitlab EE

1. GitLab每天运行一次，默认情况下，GitLab将在服务器时间上午01:30每天运行一次worker，以根据LDAP检查和更新GitLab用户。

```shell
gitlab_rails['ldap_sync_worker_cron'] = "30 1 * * *"
```

2. 运行群组同步（ee）

```shell
[root@localhost ~]# gitlab-rake gitlab:ldap:group_sync
```

### 1.3 SMTP设置

[SMTP设置](https://docs.gitlab.com/omnibus/settings/smtp.html)

### 1.4 Gitlab账号与AD账号

Gitlab账号与AD账号共用: 集成AD后，只需保证 **Username、电子邮箱一致**即可，登录享用同一用户空间。



## 二. JumpServer LDAP

1. 后台LDAP设置

   `LDAP地址`          `ldap://192.168.10.10:389`
    `绑定DN`             `cn=admin,cn=Users,dc=test,dc=com`
    `用户OU`             `ou=jumpserver,dc=test,dc=com`
    `用户过滤器`       `(sAMAccountName=%(user)s)`
    `LADP属性映射`  `{"username": "sAMAccountName", "name": "sn", "email": "mail"}`
    `启动LDAP认证`  ☑️

2. 修改配置文件

```shell
[root@localhost ~]# vim /opt/jumpserver/config.yml 
```

```shell
# LDAP/AD settings
# LDAP 搜索分页数量
#AUTH_LDAP_SEARCH_PAGED_SIZE: 1000
#
# 定时同步用户
# 启用 / 禁用
AUTH_LDAP_SYNC_IS_PERIODIC: True
# 同步间隔 (单位: 时) (优先）
#AUTH_LDAP_SYNC_INTERVAL: 12
# Crontab 表达式，每隔半个小时同步一次
AUTH_LDAP_SYNC_CRONTAB: "*/30 * * * *"
#
# LDAP 用户登录时仅允许在用户列表中的用户执行 LDAP Server 认证
AUTH_LDAP_USER_LOGIN_ONLY_IN_USERS: True
#
# LDAP 认证时如果日志中出现以下信息将参数设置为 0 (详情参见：https://www.python-ldap.org/en/latest/faq.html)
# In order to perform this operation a successful bind must be completed on the connection
#AUTH_LDAP_OPTIONS_OPT_REFERRALS: -1
```



##  三. Nginx LDAP

### 3.1 编译安装Nginx

1. 下载Nginx源码包

```shell
[root@NGINX_LDAP home]# wget http://nginx.org/download/nginx-1.18.0.tar.gz
```

2. 安装编译nginx依赖包

```shell
[root@NGINX_LDAP home]# yum install -y gcc gcc-c++ pcre pcre-devel zlib zlib-devel openssl openssl-devel openldap-devel
```

3. 解压nginx包

```shell
[root@NGINX_LDAP home]# tar zxvf nginx-1.18.0.tar.gz
```

4. 克隆nginx第三方模块

```shell
[root@NGINX_LDAP home]# git clone https://github.com/kvspb/nginx-auth-ldap.git
```

5. 配置

```shell
[root@NGINX_LDAP nginx-1.18.0]# ./configure --prefix=/usr/local/nginx  --add-module=/home/nginx-auth-ldap
```

6. 编译安装

```shell
[root@NGINX_LDAP nginx-1.18.0]# make && make install
```

7. 修改nginx.conf

```shell
[root@NGINX_LDAP conf]# cat /usr/local/nginx/conf/nginx.conf
   worker_processes  1;
   
   events {
       worker_connections  1024;
   }
   
   http {
       include       mime.types;
       default_type  application/octet-stream;
   
       sendfile        on;
       keepalive_timeout  65;
   
       # define ldap server
       ldap_server ad_1 {
         # user search base.
         url "ldap://192.168.10.10:3268/DC=test,DC=com?sAMAccountName?sub?(objectClass=person)";
         # bind as
         binddn "test\\admin";
         # bind pw
         binddn_passwd "12345678";
         # group attribute name which contains member object
         group_attribute member;
         # search for full DN in member object
         group_attribute_is_dn on;
         # matching algorithm (any / all)
         satisfy any;
         # list of allowed groups
         require group "CN=Nginx登录,OU=权限组,DC=test,DC=com";
         # list of allowed users
         # require 'valid_user' cannot be used together with 'user' as valid user is a superset
         # require valid_user;
         #require user "CN=Batman,OU=Users,OU=New York Office,OU=Offices,DC=company,DC=com";
         #require user "CN=Robocop,OU=Users,OU=New York Office,OU=Offices,DC=company,DC=com";
       }
   
   server {
     listen       80;
     server_name  localhost;
   
     location / {
       # adding ldap authentication
       auth_ldap "Closed content";
       auth_ldap_servers ad_1;
   
       root html;
       index index.html index.htm;
     }
   
     error_page   500 502 503 504  /50x.html;
   
     location = /50x.html {
       root html;
     }
   }
}
```

   

## 四. 参考

【1】[How to configure LDAP with GitLab CE](http://www.obsis.unb.br/gitlab/help/administration/auth/how_to_configure_ldap_gitlab_ce/index.md)

【2】[General LDAP Setup](https://docs.gitlab.com/ee/administration/auth/ldap/index.html#adjusting-ldap-user-sync-schedule-starter-only)

【3】 [nginx-auth-ldap](https://github.com/kvspb/nginx-auth-ldap)

【4】[LDAP 认证](https://docs.jumpserver.org/zh/master/admin-guide/authentication/ldap/)