# pyCfDdns
a python script to update ddns. Version: `0.0.2`

---
## Some introduction
This is a script for ddns updating used in cloudflare(cf).  

Does not support ipv6. Maybe this feature will be added in the future.  

There are 2 methods to update ddns though cf api. One is updating by api keys (legacy) while the other is by api token.
It is recommended to use api token since Principle of Minimum Permission. Someone using api keys to update ddns also
has the privilege to do anything else. However, this would not happen on token.

HOW_TO_USE  
1. install python3.
2. replace the following User Infomation with your own.(Token or Keys must be given. Zone name, record name and account
name are also needed. It is ok without optional information but it is recommended to filled in with zone id. Because the
less information is given here, the more privilege the token should be set. If zone id is given, only right to edit dns
record is needed while if every optional information is missing, it needs rights to edit dns record, to read zone
details[to get zone id] and to read account information[to get account id to get zone id].)
3. python3 pycfddns.py -token
4. set a timing function to check the current ip periodically.(like using crond)

---

## 中文介绍
### 用法
1. 安装python3
2. 下载并替换pycfddns.py文件中，User Information内的信息。可以选择Token更新或Keys（目前暂不支持，可以先使用另一个[shell脚本](https://github.com/MstKenway/cf-ddns)）更新，推荐使用Token，Token需要手动生成，限制权限，更安全；Keys有最高权限，安全级别较高。Token(令牌)必要，其他zone name（区域名，也就是域名）, record name（记录名，也就是具体的子域名）, account name（cf里账户名）这些也是必要的。最后optional information是可选信息，可填可不填。建议填写zone id，其他信息可自行获取，或者不需要。如果可选信息都不填，对token的权限要求较高，需要【1.修改dns记录权限】、【2.读取区域信息权限（为了获取zone id以及record id）】和【3.读取账户权限（为了获取account id从而获取zone id）】。如果填写zone id则单【1.修改dns记录权限】即可。）
  ```shell
  mkdir /etc/pycfddns
  wget https://raw.githubusercontent.com/MstKenway/pyCfDdns/main/pycfddns.py -O /etc/pycfddns/pycfddns.py
  
  ```
3. 执行
  ```shell
  python3 /etc/pycfddns/pycfddns.py -token
  ```
4. 设置定时任务
  ```shell
  crontab -e
  ```
  填写
  ```shell
  */2 * * * * python3 /etc/pycfddns/pycfddns.py > /dev/null 2>&1
  ```
---
### 参数
```
pycfdns.py [-h] [-f] -token/-keys 

-h help information/说明文档  
-token update ddns by token(either token or keys are required)/使用token方式更新ddns(token与keys需要二选一，优先使用token)
-keys update ddns by keys/使用个人私钥更新ddns   
-f force to update ddns/强制更新ddns记录，无论当前解析的ip与待更新ip是否相等  
```

---
### 优势
1. 无第三方库依赖，安装简单
2. 使用Token为主的方式更新DDNS，更安全

---
附上[生成Token教程](https://support.cloudflare.com/hc/zh-cn/articles/200167836-%E7%AE%A1%E7%90%86-API-%E4%BB%A4%E7%89%8C%E5%92%8C%E5%AF%86%E9%92%A5)   
选择DNS模板  
需要：  
1. 区域 DNS 编辑（必须）
2. 区域 区域 读取
3. 账户 账户设置 读取

如果给了zone id，后两个权限就不用了。zone id 可以在DashBoard-账户-概述 的右侧栏中找到，zone id 下方就是account id。
