# Kook-LinkGuard-Bot
检查邀请链接是否为当前服务器的bot (khl.py)


## 使用

邀请bot进入频道后，选定一个文字频道作为bot的日志频道，在频道内发送`/setch`，bot将此频道设置为日志频道，并开启对整个服务器的邀请链接监控

`/alive`命令，测试bot是否在线


## 私有部署

保证python版本大于3.7，安装如下包
```
pip install khl.py
```

新建`config/config.json`文件，在里面写入如下字段

```json
{
    "token":"bot websocket token",
    "debug_ch":"错误日志文字频道"
}
```

新建`config/linklog.json`文件，在里面写入如下字段

```json
{
    "data":{},
    "set":{}   
}
```

配置完毕以后，就可以运行bot了

```
python main.py
```