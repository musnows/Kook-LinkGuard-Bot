import json
import aiohttp
import asyncio
import traceback
import os

from khl import Bot,Cert, Message,PrivateMessage,requester
from khl.card import Card,CardMessage,Types,Module,Element
from aiohttp import client_exceptions

from utils.files import *
from utils.myLog import get_time,log_flush,log_msg,_log
from utils.dataLog import log_invite_code 

# 用读取来的 config 初始化 bot
bot = Bot(token=config['token']) # websocket
if not config["ws"]: # webhook
    _log.info(f"[BOT] using webhook at {config['webhook_port']}")
    bot = Bot(cert=Cert(token=config['token'], verify_token=config['verify_token'],encrypt_key=config['encrypt']),
              port=config["webhook_port"])
# 配置kook头链接
kook = "https://www.kookapp.cn"
headers = {f'Authorization': f"Bot {config['token']}"}
SetCmdLock = asyncio.Lock()
"""配置命令上锁"""

#####################################################################################

async def get_card_msg(text:str,sub_text="",header_text="",err_card=False):
    """获取一个简单卡片的函数"""
    c = Card()
    if header_text !="":
        c.append(Module.Header(header_text))
        c.append(Module.Divider())
    if err_card:# 错误卡
        text += f"\n```\n{traceback.format_exc()}\n```\n"
    # 总有内容
    c.append(Module.Section(Element.Text(text,Types.Text.KMD)))
    if sub_text != "":
        c.append(Module.Context(Element.Text(sub_text,Types.Text.KMD)))
    return CardMessage(c)

# 查看bot状态
@bot.command(name='alive',case_sensitive=False)
async def alive_check(msg:Message,*arg):
    try:
        log_msg(msg)
        await msg.reply(f"bot alive here")# 回复
    except:
        _log.exception(f"Err in help")

# 帮助命令
@bot.command(name='lgh',aliases=['lghelp'],case_sensitive=False)
async def help(msg:Message,*arg):
    try:
        log_msg(msg)
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
        cm = await get_card_msg(f"ERR! [{get_time()}] help",err_card=True)
        await msg.reply(cm)

# 设置日志频道
@bot.command(name='setch',case_sensitive=False)
async def set_channel(msg:Message,*arg):
    try:
        log_msg(msg)
        global LinkLog,LinkConf,SetCmdLock
        async with SetCmdLock: # 上锁
            # 不在内，则创建键值
            if msg.ctx.guild.id not in LinkConf['set']:
                LinkConf['set'][msg.ctx.guild.id] = {'log_ch':'','ign_ch':[]}
            # 设置当前频道为通知频道
            LinkConf['set'][msg.ctx.guild.id]['log_ch'] = msg.ctx.channel.id

        # 发送消息
        text = f"频道信息：(chn){msg.ctx.channel.id}(chn)\n"
        text+= f"频道ID：  {msg.ctx.channel.id}"
        cm = await get_card_msg(text,header_text="已将当前频道设置为 LinkGuard 的日志频道")
        await msg.reply(cm)
        # 写入文件
        await write_link_conf()
        _log.info(f"[setch] G:{msg.ctx.guild.id} C:{msg.ctx.channel.id}")
    except Exception as result:
        _log.exception(f"Err in setch")
        cm = await get_card_msg(f"ERR! [{get_time()}] setch",err_card=True)
        await msg.reply(cm)
        await bot.client.send(debug_ch,cm)#发送错误信息到指定频道

# 忽略某个频道
@bot.command(name='ignch',case_sensitive=False)
async def ignore_channel(msg:Message,*arg):
    try:
        log_msg(msg)
        global LinkLog,LinkConf
        gid = msg.ctx.guild.id
        chid = msg.ctx.channel.id
        if gid not in LinkConf['set']:
            await msg.reply(f"请先使用「/setch」命令设置日志频道，详见「/lgh」帮助命令")
            return
        # 如果文字频道id不在ign里面，则追加
        if chid not in LinkConf['set'][gid]['ign_ch']:
            LinkConf['set'][gid]['ign_ch'].append(chid)
        # 构造卡片
        text = f"忽略频道：(chn){msg.ctx.channel.id}(chn)\n"
        text+= f"频道ID：{msg.ctx.channel.id}"
        cm = await get_card_msg(text,header_text="已将当前频道从 LinkGuard 的监看中忽略")
        await msg.reply(cm)
        # 写入文件
        await write_link_conf()
        _log.info(f"[ignch] G:{msg.ctx.guild.id} C:{msg.ctx.channel.id}")
    except Exception as result:
        _log.exception(f"Err in ignch")
        cm = await get_card_msg(f"ERR! [{get_time()}] ignch",err_card=True)
        await msg.reply(cm)
        await bot.client.send(debug_ch,cm)#发送错误信息到指定频道

@bot.command(name='clear',case_sensitive=False)
async def clear_setting(msg:Message,*arg):
    try:
        log_msg(msg)
        global LinkLog,LinkConf
        gid = msg.ctx.guild.id
        if gid not in LinkConf['set']:
            text = f"本频道并没有配置日志频道，机器人尚未启用\n可使用「/setch」命令设置日志频道\n详见「/lgh」帮助命令"
            cm = await get_card_msg(text)
            return await msg.reply(cm)
            
        ch_id = LinkConf['set'][gid]['log_ch']
        text = f"监听频道信息：(chn){ch_id}(chn)\n"
        text+= f"监听频道ID：  {ch_id}"
        # 删除键值
        del LinkConf['set'][gid] 
        # 发送信息
        cm = await get_card_msg(text,header_text="已清除本服务器的监听设置")
        await msg.reply(cm)
        # 写入文件
        await write_link_conf()
        _log.info(f"[clear] G:{msg.ctx.guild.id}")
    except Exception as result:
        _log.exception(f"Err in clear")
        cm = await get_card_msg(f"ERR! [{get_time()}] clear",err_card=True)
        await msg.reply(cm)
        await bot.client.send(debug_ch,cm)#发送错误信息到指定频道

#####################################################################################


async def check_invites(code:str):
    """判断邀请链接的api"""
    url = kook+'/api/v2/invites/' + code
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            ret = json.loads(await response.text())
            return ret


async def send_log(gid:str,usrid:str,usrname:str,code:str,ret:str):
    """发送通知到日志频道"""
    text= f"用户id: {usrid}\n昵称: {usrname}\n"
    text+=f"该用户发送的邀请码: {code}\n"
    text+=f"```\n{ret}\n```"
    cm = await get_card_msg(text,header_text=f"[{get_time()}] LinkGuard")
    ch = await bot.client.fetch_public_channel(LinkConf['set'][gid]['log_ch'])
    await bot.client.send(ch,cm)


async def invite_ck(msg:Message,code: str):
    """监看url是否为当前频道
    Return Value:
    - True: not same guild_id
    - False: is same guild_id
    """
    gid = msg.ctx.guild.id    # 服务器id
    chid = msg.ctx.channel.id # 文字频道id
    usrid = msg.author_id     # 发送链接的用户id
    usrname = f"{msg.author.username}#{msg.author.identify_num}"
    ret = "none"
    try:
        # 之前配置过ign，忽略此频道
        if chid in LinkConf['set'][gid]['ign_ch']:
            return False
        # 判断是否为当前服务器
        ret = await check_invites(code)
        if ret['guild']['id'] != gid:
            await log_invite_code(gid,usrid,code,ret['guild'])  # 写入日志
            await send_log(gid,usrid,usrname,code,ret['guild'])  # 发送通知
            _log.info(f"G:{gid} C:{chid} Au:{usrid}\n[ret] {code} : {ret['guild']}")
            return True # 不是本服务器的邀请链接，返回true
        # 是本服务器返回false
        return False 
    except KeyError as result:
        if 'guild' in str(result) or 'id' in str(result):
            _log.warning(f"G:{gid} C:{chid} Au:{usrid} | code:{code} | keyErr {result} | ret:{ret}")
            return False # 出现了keyerr无法正常判断，认为是本服务器id
        # 其他情况依旧raise
        raise result


@bot.on_message()
async def link_guard(msg: Message):
    """监看本频道的邀请链接"""
    try:
        # 是私聊，直接退出
        if isinstance(msg, PrivateMessage):
            return
        if msg.ctx.guild.id not in LinkConf['set']:
            return # 必须要配置日志频道，才会启用
        # 消息内容
        text = msg.content 
        # 判断消息里面有没有邀请链接
        link_index = text.find('https://kook.top/')  #返回子串开头的下标
        if link_index == -1: # 没有，直接退出
            return
        # 取出邀请链接的code
        code = text[link_index + 17:link_index + 23] 
        ret = await invite_ck(msg,code) # 检查是否为当前服务器
        if ret: # 不是本服务器的邀请链接
            card_text = f"(met){msg.author_id}(met)\n请勿发送其他服务器的邀请链接！"
            cm = CardMessage(Card(Module.Section(Element.Text(card_text,Types.Text.KMD))))
            await msg.reply(cm) 
            await msg.delete() # 删除邀请链接消息
            _log.info(f"G:{msg.ctx.guild.id} C:{msg.ctx.channel.id} Au:{msg.author_id} | inform & msg.delete")
        
    except requester.HTTPRequester.APIRequestFailed as result:
        _log.exception(f"APIRequestFailed in link_guard")
        if "无删除权限" in str(result):
            ch = await bot.client.fetch_public_channel(LinkConf['set'][msg.ctx.guild.id]['log_ch'])
            await ch.send(await get_card_msg("【重要】请为机器人开启本服务器的 `消息管理` 权限"))
            del LinkConf['set'][msg.ctx.guild.id] # 删除服务器键值
            _log.warning(f"[APIRequestFailed] del G:{msg.ctx.guild.id} in set")
        elif "message/create" in str(result) and "没有权限" in str(result):
            pass
    except client_exceptions.ClientConnectorError as result:
        if 'kookapp.cn' in str(result):
            return _log.error(f"ERR! {str(result)}")
        _log.exception(f"aiohttp Err in link_guard")
    except Exception as result:
        err_str=f"ERR! [{get_time()}] link_guard\n```\n{traceback.format_exc()}\n```"
        _log.exception("Err in link_guard")
        await bot.client.send(debug_ch,await get_card_msg(err_str))#发送错误信息到指定频道


#############################################################################

# 开机任务
@bot.on_startup
async def startup_task(b:Bot):
    try:
        global debug_ch
        # 暴力测试是否有data键值，没有是有问题的（file init失败）
        assert('data' in LinkLog)
        assert('set' in LinkConf)
        # 获取debug频道
        debug_ch = await bot.client.fetch_public_channel(config['debug_ch'])
        _log.info("[BOT.START] fetch debug channel success")
    except:
        _log.exception(f"[BOT.START] ERR!")
        os.abort()

# botmarket通信
@bot.task.add_interval(minutes=25)
async def botmarket():
    api = "http://bot.gekj.net/api/v1/online.bot"
    headers = {'uuid': '1d266c78-30b2-4299-b470-df0441862711'}
    async with aiohttp.ClientSession() as session:
        await session.post(api, headers=headers)
# 定时写文件，因为很多地方都写了，所以这里只需要10分钟执行一次
@bot.task.add_interval(minutes=10)
async def save_log_file_task():
    await write_link_log(log_info="[BOT.TASK]")

# 开机 （如果是主文件就开机）
if __name__ == '__main__':
    # 开机的时候打印一次时间，记录开启时间
    _log.info(f"[BOT] Start at {get_time()}")
    bot.run()