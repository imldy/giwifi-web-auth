# 通过GiWiFi网页认证接口进行认证

仅需配置账户和密码，其他信息自动获取。

## 安装Python与pip

### RedHat/CentOS

```shell
yum install python3 python3-pip
```

### Debian/Ubuntu/Deepin

```shell
apt install python3 python3-pip
```

### OpenWrt

```shell
opkg install python3 python3-pip
```

## 获取代码与配置文件

### 获取代码

### 设置账号

新建文件`conf.txt`，第一行放手机号，第二行放密码，例如：

```text
18300000000
00000000
```

## 安装依赖

```
pip install -r requirements.txt
```

## 运行

```
python3 gwa.py [-d ${time}] # 附带上-d和秒数代表持续运行，不带则为运行一次
```

