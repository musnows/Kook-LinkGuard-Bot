import json
import aiohttp
import traceback
import os
from utils import *

from khl import Bot, Message,PrivateMessage
from khl.card import Card,CardMessage,Types,Module,Element

# 用读取来的 config 初始化 bot
config = open_file('./config/config.json')
bot = Bot(token=config['token'])
# 配置kook头链接
kook = "https://www.kookapp.cn"
headers = {f'Authorization': f"Bot {config['token']}"}
# 打开日志文件
LinkLogPath = './config/linklog.json'
LinkLog = open_file(LinkLogPath)

# 命令日志
def logging(msg:Message):
    chid = "PrivateMessage"
    if not isinstance(msg, PrivateMessage): # 不是私聊
        chid = msg.ctx.channel.id
    # 打印日志
    print(
        f"[{GetTime()}] G:{msg.ctx.guild.id} - C:{chid} - Au:{msg.author_id} {msg.author.username}#{msg.author.identify_num} = {msg.content}"
    )

# 查看bot状态
@bot.command(name='alive',case_sensitive=False)
async def alive_check(msg:Message,*arg):
    logging(msg)
    await msg.reply(f"bot alive here")# 回复

# 设置日志频道
@bot.command(name='setch',case_sensitive=False)
async def set_channel(msg:Message,*arg):
    try:
        logging(msg)
        global LinkLog
        # 设置当前频道为通知频道
        LinkLog['set'][msg.ctx.guild.id] = msg.ctx.channel.id
        await msg.reply(f"已将当前频道设置为LinkGuard Bot的日志频道")
    except Exception as result:
        err_str=f"ERR! [{GetTime()}] setch - {result}"
        print(err_str)
        await bot.client.send(debug_ch,err_str)#发送错误信息到指定频道


# 写入日志
def write_log(gid:str,usrid:str,ret:str):
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
    write_file(LinkLogPath,LinkLog) 
    print(f"[{GetTime()}] G:{gid} = Au:{usrid} = write_log")

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
    ch = await bot.client.fetch_public_channel(LinkLog['set'][gid])
    await bot.client.send(ch,cm)

# 监看url是否为当前频道
async def invite_ck(msg:Message,code: str):
    gid = msg.ctx.guild.id
    usrid = msg.author_id
    usrname = f"{msg.author.username}#{msg.author.identify_num}"
    print(f"[{GetTime()}] G:{gid} = {code}")
    url = kook+'/api/v2/invites/' + code
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            ret = json.loads(await response.text())
            # 判断是否为当前服务器
            if ret['guild']['id'] != gid:
                write_log(gid,usrid,ret['guild'])  # 写入日志
                await send_log(gid,usrid,usrname,code,ret['guild'])  # 发送通知
                print(f"[{GetTime()}] G:{gid} = {code} = {ret['guild']}")
                return True # 不是返回true
    return False # 是返回false


# 监看本频道的邀请链接
@bot.on_message()
async def link_guard(msg: Message):
    try:
        if msg.ctx.guild.id not in LinkLog['set']:
            return # 必须要配置日志频道，才会启用
        # 消息内容
        text = msg.content 
        # 判断消息里面有没有邀请链接
        link_index = text.find('https://kook.top/')  #返回子串开头的下标
        if link_index != -1: # 有
            code = text[link_index + 17:link_index + 23] # 取出邀请链接的code
            ret = await invite_ck(msg,code) # 检查是否为当前服务器
            if ret: # 不是
                await msg.reply(f"(met){msg.author_id}(met) 请不要发送其他服务器的邀请链接！")
                await msg.delete() # 删除邀请链接消息

    except Exception as result:
        err_str=f"ERR! [{GetTime()}] /ldck - {result}"
        print(err_str)
        await bot.client.send(debug_ch,err_str)#发送错误信息到指定频道




#############################################################################

# 开机任务
@bot.task.add_date()
async def startup_task():
    try:
        global debug_ch
        debug_ch = await bot.client.fetch_public_channel(config['debug_ch'])
        print(f"[BOT.START] fetch debug channel success")
    except:
        err_cur=str(traceback.format_exc())
        print(f"[BOT.START] ERR!\n{err_cur}")
        os._exit(-1)


print(f"[BOT.START] start at {GetTime()}")
# 开始运行
bot.run()