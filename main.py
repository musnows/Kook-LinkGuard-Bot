import json
import aiohttp
import asyncio
import traceback
import os

from khl import Bot,Cert, Message,PrivateMessage,requester
from khl.card import Card,CardMessage,Types,Module,Element
from aiohttp import client_exceptions

from utils import open_file,write_file,GetTime,logFlush,_log

# 用读取来的 config 初始化 bot
config = open_file('./config/config.json')
"""机器人配置文件"""
bot = Bot(token=config['token']) # websocket
if not config["ws"]: # webhook
    _log.info(f"[BOT] using webhook at {config['webhook_port']}")
    bot = Bot(cert=Cert(token=config['token'], verify_token=config['verify_token'],encrypt_key=config['encrypt']),
              port=config["webhook_port"])
# 配置kook头链接
kook = "https://www.kookapp.cn"
headers = {f'Authorization': f"Bot {config['token']}"}
# 打开日志文件
LinkLogPath = './config/linklog.json'
"""日志文件路径"""
LinkLog = open_file(LinkLogPath)
"""日志文件 {"data":{}}"""
FlieSaveLock = asyncio.Lock()
"""用于日志文件写入的锁"""

#####################################################################################

def logMsg(msg:Message):
    """命令日志"""
    try:
        gid,chid = "pm","pm"
        if not isinstance(msg, PrivateMessage): # 不是私聊
            chid = msg.ctx.channel.id
            gid = msg.ctx.guild.id
        # 打印日志
        _log.info(
            f"G:{gid} | C:{chid} | Au:{msg.author_id} {msg.author.username}#{msg.author.identify_num} = {msg.content}"
        )
        logFlush() # 刷缓冲区
    except:
        _log.exception(f"err in logging")

async def write_link_log():
    """写入日志"""
    async with FlieSaveLock:
        write_file(LinkLogPath,LinkLog)
        _log.info(f"[write_file] LinkLog to {LinkLogPath}")

# 查看bot状态
@bot.command(name='alive',case_sensitive=False)
async def alive_check(msg:Message,*arg):
    try:
        logMsg(msg)
        await msg.reply(f"bot alive here")# 回复
    except:
        _log.exception(f"Err in help")

# 帮助命令
@bot.command(name='lgh',case_sensitive=False)
async def help(msg:Message,*arg):
    try:
        logMsg(msg)
        text = "" if not "notice" in config else config["notice"]
        text+= "「/alive」看看bot是否在线\n"
        text+= "「/setch」将本频道设置为日志频道 (执行后才会开始监看)\n"
        text+= "「/ignch」在监看中忽略本频道\n"
        text+= "「/clear」清除本服务器的设置\n"
        text+= " 出现其他频道链接时，机器人会提醒用户、删除该消息，并发送链接相关信息到日志频道"
        cm = CardMessage()
        c = Card(
            Module.Header(f"LinkGuard 的帮助命令"),
            Module.Divider(),
            Module.Section(Element.Text(text,Types.Text.KMD)),
            Module.Container(Element.Image(src="https://img.kookapp.cn/assets/2023-04/T56YuWvvuQ0hm095.png"))
        )
        cm.append(c)
        await msg.reply(cm)
    except Exception as result:
        _log.exception(f"Err in help")
        await msg.reply(f"ERR! [{GetTime()}] help - {result}")

# 设置日志频道
@bot.command(name='setch',case_sensitive=False)
async def set_channel(msg:Message,*arg):
    try:
        logMsg(msg)
        global LinkLog
        # 不在内，则创建键值
        if msg.ctx.guild.id not in LinkLog['set']:
            LinkLog['set'][msg.ctx.guild.id] = {'log_ch':'','ign_ch':[]}
        # 设置当前频道为通知频道
        LinkLog['set'][msg.ctx.guild.id]['log_ch'] = msg.ctx.channel.id
        await msg.reply(f"已将当前频道设置为LinkGuard Bot的日志频道")
        # 写入文件
        await write_link_log()
        _log.info(f"[setch] G:{msg.ctx.guild.id} C:{msg.ctx.channel.id}")
    except Exception as result:
        err_str=f"ERR! [{GetTime()}] setch - {result}"
        _log.exception(f"Err in setch")
        await msg.reply(err_str)
        await bot.client.send(debug_ch,err_str)#发送错误信息到指定频道

# 忽略某个频道
@bot.command(name='ignch',case_sensitive=False)
async def ignore_channel(msg:Message,*arg):
    try:
        logMsg(msg)
        global LinkLog
        gid = msg.ctx.guild.id
        chid = msg.ctx.channel.id
        if gid not in LinkLog['set']:
            await msg.reply(f"请先使用「/setch」命令设置日志频道，详见「/lgh」帮助命令")
            return
        # 如果文字频道id不在ign里面，则追加
        if chid not in LinkLog['set'][gid]['ign_ch']:
            LinkLog['set'][gid]['ign_ch'].append(chid)
        # 写入文件
        await msg.reply(f"已将本频道忽略")
        await write_link_log()
        _log.info(f"[ignch] G:{msg.ctx.guild.id} C:{msg.ctx.channel.id}")
    except Exception as result:
        err_str=f"ERR! [{GetTime()}] ignch - {result}"
        _log.exception(f"Err in ignch")
        await msg.reply(err_str)
        await bot.client.send(debug_ch,err_str)#发送错误信息到指定频道

@bot.command(name='clear',case_sensitive=False)
async def clear_setting(msg:Message,*arg):
    try:
        logMsg(msg)
        global LinkLog
        gid = msg.ctx.guild.id
        if gid not in LinkLog['set']:
            await msg.reply(f"请先使用「/setch」命令设置日志频道，详见「/lgh」帮助命令")
            return
        # 删除键值
        del LinkLog['set'][gid]
        await msg.reply(f"已清楚本服务器的设置")
        # 写入文件
        await write_link_log()
        _log.info(f"[clear] G:{msg.ctx.guild.id}")
    except Exception as result:
        _log.exception(f"Err in clear")
        err_str=f"ERR! [{GetTime()}] clear - {result}"
        await msg.reply(err_str)
        await bot.client.send(debug_ch,err_str)#发送错误信息到指定频道

#####################################################################################

# 写入日志
async def write_log(gid:str,usrid:str,ret:str):
    global LinkLog
    # 新建服务器键值
    if gid not in LinkLog['data']:
        LinkLog['data'][gid] = {}
    # 新建用户键值
    if usrid not in LinkLog['data'][gid]:
        LinkLog['data'][gid][usrid] = []
    # 插入返回值
    LinkLog['data'][gid][usrid].append(ret)
    # 写入文件
    await write_link_log()
    _log.info(f"G:{gid} = Au:{usrid} = write_log")
    logFlush() # 刷缓冲区

# 判断邀请链接的api
async def check_invites(code:str):
    url = kook+'/api/v2/invites/' + code
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            ret = json.loads(await response.text())
            return ret

# 发送通知
async def send_log(gid:str,usrid:str,usrname:str,code:str,ret:str):
    text= f"用户id: {usrid}\n昵称: {usrname}\n"
    text+=f"该用户发送的邀请码: {code}\n"
    text+=f"```\n{ret}\n```"
    cm = CardMessage()
    c = Card(
        Module.Header(f"[{GetTime()}] LinkGuard"),
        Module.Divider(),
        Module.Section(Element.Text(text,Types.Text.KMD))
    )
    cm.append(c)
    ch = await bot.client.fetch_public_channel(LinkLog['set'][gid]['log_ch'])
    await bot.client.send(ch,cm)

# 监看url是否为当前频道
async def invite_ck(msg:Message,code: str):
    """Return Value:
    - True: not same guild_id
    - False: is same guild_id
    """
    gid = msg.ctx.guild.id    # 服务器id
    chid = msg.ctx.channel.id # 文字频道id
    usrid = msg.author_id     # 发送链接的用户id
    usrname = f"{msg.author.username}#{msg.author.identify_num}"
    # 之前配置过ign，忽略此频道
    if chid in LinkLog['set'][gid]['ign_ch']:
        return False
    # 判断是否为当前服务器
    ret = await check_invites(code)
    if ret['guild']['id'] != gid:
        await write_log(gid,usrid,ret['guild'])  # 写入日志
        await send_log(gid,usrid,usrname,code,ret['guild'])  # 发送通知
        _log.info(f"G:{gid} C:{chid} Au:{usrid}\n[ret] {code} : {ret['guild']}")
        return True # 不是本服务器的邀请链接，返回true
    # 是本服务器返回false
    return False 


# 监看本频道的邀请链接
@bot.on_message()
async def link_guard(msg: Message):
    try:
        # 是私聊，直接退出
        if isinstance(msg, PrivateMessage):
            return
        if msg.ctx.guild.id not in LinkLog['set']:
            return # 必须要配置日志频道，才会启用
        # 消息内容
        text = msg.content 
        # 判断消息里面有没有邀请链接
        link_index = text.find('https://kook.top/')  #返回子串开头的下标
        if link_index != -1: # 有
            code = text[link_index + 17:link_index + 23] # 取出邀请链接的code
            ret = await invite_ck(msg,code) # 检查是否为当前服务器
            if ret: # 不是本服务器的邀请链接
                await msg.reply(f"(met){msg.author_id}(met) 请不要发送其他服务器的邀请链接！")
                await msg.delete() # 删除邀请链接消息
    except requester.HTTPRequester.APIRequestFailed as result:
        _log.exception(f"APIRequestFailed in link_guard")
        if "无删除权限" in str(result):
            ch = await bot.client.fetch_public_channel(LinkLog['set'][msg.ctx.guild.id]['log_ch'])
            await bot.client.send(ch,f"请开启本服务器的删除文字权限")
        elif "message/create" in str(result) and "没有权限" in str(result):
            pass
    except client_exceptions.ClientConnectorError as result:
        if 'kookapp.cn' in str(result):
            _log.error(f"ERR! {str(result)}")
            return
        _log.exception(f"aiohttp Err in link_guard")
    except Exception as result:
        err_str=f"ERR! [{GetTime()}] link_guard\n```\n{traceback.format_exc()}\n```"
        _log.exception("Err in link_guard")
        await bot.client.send(debug_ch,err_str)#发送错误信息到指定频道


#############################################################################

# 开机任务
@bot.task.add_date()
async def startup_task():
    try:
        global debug_ch
        debug_ch = await bot.client.fetch_public_channel(config['debug_ch'])
        _log.info("[BOT.START] fetch debug channel success")
        logFlush() # 刷缓冲区
    except:
        _log.exception(f"[BOT.START] ERR!")
        logFlush() # 刷缓冲区
        os.abort()

# botmarket通信
@bot.task.add_interval(minutes=30)
async def botmarket():
    api = "http://bot.gekj.net/api/v1/online.bot"
    headers = {'uuid': '1d266c78-30b2-4299-b470-df0441862711'}
    async with aiohttp.ClientSession() as session:
        await session.post(api, headers=headers)


# 开机 （如果是主文件就开机）
if __name__ == '__main__':
    # 开机的时候打印一次时间，记录开启时间
    _log.info(f"[BOT] Start at {GetTime()}")
    bot.run()