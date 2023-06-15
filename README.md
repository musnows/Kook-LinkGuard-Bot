# Kook-LinkGuard-Bot

检查邀请链接是否为当前服务器的bot (khl.py)


## 使用

#### 命令列表

- 「/lgh」帮助命令
- 「/alive」看看bot是否在线
- 「/setch」将本频道设置为日志频道 (执行后才会开始监看)
- 「/ignch」在监看中忽略本频道
- 「/clear」清除本服务器的设置

#### 操作流程

机器人启动后，可以使用`/alive`命令，测试bot是否在线。

邀请bot进入目标服务器后，选定一个**文字频道**作为bot在**该服务器**的日志频道。

在频道内发送`/setch`，bot将此频道设置为日志频道，并开启对整个服务器的邀请链接监控（必须执行此命令，否则bot不会工作）


### 功能截图

下图为机器人撤回用户带频道链接发言

![msg_delete](https://img.kookapp.cn/assets/2023-02/ycJ3MJHzSJ0h603w.png)

下图为机器人在`/setch`所设置的日志频道中发送的信息，包含发送了其他服务器邀请链接的用户ID，用户昵称，所发送的邀请码，和这个邀请码所对应服务器的详细信息。

![log_cm](https://img.kookapp.cn/assets/2023-02/XnNCA8XoZl0jl0aa.png)


## 私有部署

保证python版本大于3.9，安装如下包

```
pip3 install -r requirements.txt
```

根据 [config/config-exp.py](./config/config-exp.py)，新建一个 `config/config.py` 文件，根据示例配置文件中的注释，在里面写入相对应的字段。

配置完毕以后，就可以运行bot了！

```
python3 main.py
```

### 一键部署到replit

注册[replit](https://replit.com/)，创建一个Python的repl，随后进入`shell`粘贴如下命令

```
git clone https://github.com/musnows/Kook-LinkGuard-Bot.git && mv -b Kook-LinkGuard-Bot/* ./ && mv -b Kook-LinkGuard-Bot/.[^.]* ./  && rm -rf Kook-LinkGuard-Bot && pip install -r requirements.txt
```

克隆完成，replit自动加载好nix文件后，同样是修改 [config/config-exp.py](./config/config-exp.py) 的相关字段。随后点击上方绿色RUN按钮，即可运行bot。

运行后，将右侧webview中出现的url填入kook机器人后台中的webhook的callback-url，即可上线机器人。

请注意，callback-url后需要加上请求路径为 `/khl-wh`，假设replit中显示的url为

```
https://example.com
```

你应该将如下链接填入kook机器人后台的callback-url

```
https://example.com/khl-wh
```

填入后，点击callback-url的`重试`按钮（如果出现错误，请多点几次），出现`设置成功`，即可点击页面右下角的`机器人上线`，让机器人开始运行！

----

更多replit部署教程信息详见 [Kook-Ticket-Bot/wiki](https://github.com/musnows/Kook-Ticket-Bot/wiki)，基本步骤相同，repl保活工作二者都需要做。

若有不懂之处，可加入[帮助服务器](https://kook.top/gpbTwZ)咨询