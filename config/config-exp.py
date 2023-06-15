# 请根据注释内容，修改本示例文件里面对应的字段，并重命名文件为 config.py
# 请直接将token填入英文的双引号内，不要删除双引号！
# 请不要删除、重命名本页中的任何变量！

# 1.机器人配置项，请前往 https://developer.kookapp.cn/app/index 创建机器人并获取对应的token

BOT_TOKEN  = ""
"""机器人的 webhook/websocket token """
VERIFY_TOKEN =  ""
"""webhook only | 只有webhook需要"""
ENCRYPT_TOKEN = ""
"""webhook only | 只有webhook需要"""
WEBHOOK_PORT =  50000
"""运行webhook的端口。webhook only | 只有webhook需要"""
USING_WS = False
"""是否使用websocket？
如果是replit部署，强烈建议用webhook！

- False 用webhook
- True  用websocket 
"""

# 2.日志频道ID和管理员用户ID
#   各类id获取办法：kook设置-高级设置-打开开发者模式；
#   右键服务器头像，复制服务器id；右键用户头像即可复制用户id，右键频道/分组即可复制频道/分组id。

DEBUG_CH = ""
"""
用于发送debug信息的文字频道

text channel for sending debug msg
"""
ADMIN_USER = []
"""
开发者用户ID的list（可以填入多个用户），用于执行管理员命令；

developer user id for admin command;

示例 ["用户ID1","用户ID2"]
"""

NOTICE_INFO = ""
"""会出现在帮助命令之前的信息，并非帮助命令本身！本字段可以留空"""
