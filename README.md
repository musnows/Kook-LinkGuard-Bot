# Kook-LinkGuard-Bot

检查邀请链接是否为当前服务器的bot (khl.py)


## 使用

`/alive`命令，测试bot是否在线

邀请bot进入频道后，选定一个文字频道作为bot的日志频道。

在频道内发送`/setch`，bot将此频道设置为日志频道，并开启对整个服务器的邀请链接监控（必须执行此命令，否则bot不会工作）

更多命令详见 `/lgh` 帮助命令

```python
text+= "「/alive」看看bot是否在线\n"
text+= "「/setch」将本频道设置为日志频道 (执行后才会开始监看)\n"
text+= "「/ignch」在监看中忽略本频道\n"
text+= "「/clear」清除本服务器的设置\n"
```

### 功能截图

![log_cm](https://img.kookapp.cn/assets/2023-02/XnNCA8XoZl0jl0aa.png)

![msg_delete](https://img.kookapp.cn/assets/2023-02/ycJ3MJHzSJ0h603w.png)


## 私有部署

保证python版本大于3.9，安装如下包
```
pip3 install khl.py
```

根据`config/config-exp.json`，新建一个`config/config.json`文件，在里面写入相对应的字段。

配置完毕以后，就可以运行bot了

```
python3 main.py
```
