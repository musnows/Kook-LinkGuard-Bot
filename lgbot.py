# encoding: utf-8
import json
import aiohttp
import asyncio
import traceback
import os

from khl import Bot, Cert, Message, PrivateMessage, requester, MessageTypes
from khl.card import Card, CardMessage, Types, Module, Element
from aiohttp import client_exceptions

from config import config
from utils import dataLog
from utils.myLog import get_time, log_msg, _log

# 用读取来的 config 初始化 bot，字段对应即可
bot = Bot(token=config.BOT_TOKEN)  # websocket
"""main bot"""
if not config.USING_WS:
    _log.info(f"[BOT] using webhook at port:{config.WEBHOOK_PORT}")
    bot = Bot(
        cert=Cert(
            token=config.BOT_TOKEN,
            verify_token=config.VERIFY_TOKEN,
            encrypt_key=config.ENCRYPT_TOKEN,
        ),
        port=config.WEBHOOK_PORT,
    )  # webhook


kook_base_url = "https://www.kookapp.cn"
"""kook api头链接"""
kook_base_headers = {f"Authorization": f"Bot {config.BOT_TOKEN}"}
"""kook 请求头"""
BOT_START_TIME = get_time()
"""机器人启动时间"""


#####################################################################################


async def get_card_msg(text: str, sub_text="", header_text="", err_card=False):
    """获取一个简单卡片的函数"""
    c = Card()
    if header_text != "":
        c.append(Module.Header(header_text))
        c.append(Module.Divider())
    if err_card:  # 错误卡
        text += f"\n```\n{traceback.format_exc()}\n```\n"
    # 总有内容
    c.append(Module.Section(Element.Text(text, Types.Text.KMD)))
    if sub_text != "":
        c.append(Module.Context(Element.Text(sub_text, Types.Text.KMD)))
    return CardMessage(c)


def is_admin(user_id: str):
    """判断是否为管理用户"""
    return user_id in config.ADMIN_USER


# 查看bot状态
@bot.command(name="alive", case_sensitive=False)
async def alive_check(msg: Message, *arg):
    try:
        log_msg(msg)
        await msg.reply(f"bot alive here")  # 回复
    except:
        _log.exception(f"Err in help")


# 帮助命令
@bot.command(name="lgh", aliases=["lghelp"], case_sensitive=False)
async def help(msg: Message, *arg):
    try:
        log_msg(msg)
        text = config.NOTICE_INFO + "\n"  # 自带一个回车
        text += "「/alive」看看bot是否在线\n"
        text += "「/setch」将本频道设置为日志频道 (执行后才会开始监看)\n"
        text += "「/setifo」自定义撤回提示消息 [教程](https://blog.musnow.top/posts/1370917284/?f=kook)\n"
        text += "「/ignch」在链接监看中忽略本频道\n"
        text += "「/clear」清除本服务器的设置 (清除后机器人不再监看本服务器)\n"
        text += " 出现其他频道链接时，机器人会提醒用户、删除该消息，并发送链接相关信息到当前服务器设定的日志频道以供管理员查看。"
        cm = CardMessage()
        c = Card(
            Module.Header(f"LinkGuard 的帮助命令"),
            Module.Context(
                Element.Text(
                    f"帮助频道：[点我加入](https://kook.top/gpbTwZ) | 开源仓库：[Github](https://github.com/musnows/Kook-LinkGuard-Bot)\n机器人启动于：{BOT_START_TIME}",
                    Types.Text.KMD,
                )
            ),
            Module.Divider(),
            Module.Section(Element.Text(text, Types.Text.KMD)),
            Module.Container(
                Element.Image(
                    src="https://img.kookapp.cn/assets/2023-06/424QcWiOFu0ht0bp.png"
                )
            ),
        )
        cm.append(c)
        await msg.reply(cm)
    except Exception as result:
        _log.exception(f"Err in help")
        cm = await get_card_msg(f"ERR! [{get_time()}] help", err_card=True)
        await msg.reply(cm)


# 设置日志频道
@bot.command(name="setch", case_sensitive=False)
async def set_channel(msg: Message, *arg):
    try:
        log_msg(msg)
        # 记录配置
        await dataLog.log_link_conf(msg.ctx.guild.id, msg.author_id, msg.ctx.channel.id)
        # 发送消息
        text = f"频道信息：(chn){msg.ctx.channel.id}(chn)\n"
        text += f"频道ID：  {msg.ctx.channel.id}"
        cm = await get_card_msg(text, header_text="已将当前频道设置为 LinkGuard 的日志频道")
        await msg.reply(cm)
        _log.info(f"[setch] G:{msg.ctx.guild.id} C:{msg.ctx.channel.id}")
    except Exception as result:
        _log.exception(f"Err in setch | G:{msg.ctx.guild.id} | Au:{msg.author_id}")
        cm = await get_card_msg(f"ERR! [{get_time()}] setch", err_card=True)
        await msg.reply(cm)
        await bot.client.send(debug_ch, cm)  # 发送错误信息到指定频道


async def card_msg_replace(text: str):
    """修改转义字符"""
    text = text.replace("```auto", "")
    text = text.replace("```", "")
    # text = text.replace('\\(','(')
    # text = text.replace('\\)',')')
    # text = text.replace('\\[','[')
    # text = text.replace('\\]',']')
    text = text.replace("plain-text", "kmarkdown")  # 一律使用kmd
    return text


@bot.command(name="setifo")
async def set_inform_text_cmd(msg: Message, *arg):
    try:
        log_msg(msg)
        if not arg:
            return await msg.reply(await get_card_msg("请依照帮助命令，正确提供合格的卡片消息json"))
        if "button" in msg.content:
            _log.warning(
                f"'button' in content | G:{msg.ctx.guild.id} | Au:{msg.author_id}"
            )
            return await msg.reply(await get_card_msg("卡片消息内不能包含按钮！"))
        # 测试卡片消息
        cm_text = msg.content.replace("/setifo", "")
        try:
            cm_text = await card_msg_replace(cm_text)
            send_text = cm_text
            if r"{met}" in cm_text:  # at用户
                send_text = cm_text.replace(r"{met}", f"(met){msg.author_id}(met)")
            await msg.reply(
                send_text, use_quote=False, type=MessageTypes.CARD
            )  # 卡片消息发送尝试
        except Exception as result:
            if "json" not in str(result):
                raise result
            _log.warning(f"invaild json | G:{msg.ctx.guild.id} | Au:{msg.author_id}")
            return await msg.reply(await get_card_msg("卡片消息格式错误，无法正常发送", err_card=True))

        # 通过测试，记录
        await dataLog.log_link_inform(msg.ctx.guild.id, msg.author_id, cm_text)
        # 发送回复
        await msg.reply(await get_card_msg("撤回回复自定义成功，示例消息已在上方发送！"))
        _log.info(f"[setifo] G:{msg.ctx.guild.id} Au:{msg.author_id}")
    except Exception as result:
        _log.exception(f"Err in setifo | G:{msg.ctx.guild.id} | Au:{msg.author_id}")
        cm = await get_card_msg(f"ERR! [{get_time()}] setch", err_card=True)
        await msg.reply(cm)
        # await bot.client.send(debug_ch,cm)#发送错误信息到指定频道


# 忽略某个频道
@bot.command(name="ignch", case_sensitive=False)
async def ignore_channel(msg: Message, *arg):
    try:
        log_msg(msg)
        gid = msg.ctx.guild.id
        chid = msg.ctx.channel.id
        # 1.先看看是否已有配置
        conf_ret = await dataLog.select_link_conf(gid)
        if conf_ret == {}:  # 空dict代表无效
            return await msg.reply(
                await get_card_msg("请先使用「/setch」命令设置日志频道，详见「/lgh」帮助命令")
            )

        # 2.如果文字频道id不在ign里面，则追加
        if chid not in conf_ret["ign_ch"]:
            conf_ret["ign_ch"].append(chid)
        # 3.写入数据库
        await dataLog.log_link_conf(
            msg.ctx.guild.id, msg.author_id, conf_ret["log_ch"], conf_ret["ign_ch"]
        )
        # 4.构造卡片并回复用户
        text = f"忽略频道：(chn){msg.ctx.channel.id}(chn)\n"
        text += f"频道ID：{msg.ctx.channel.id}"
        cm = await get_card_msg(text, header_text="已将当前频道从 LinkGuard 的监看中忽略")
        await msg.reply(cm)
        _log.info(f"[ignch] G:{msg.ctx.guild.id} C:{msg.ctx.channel.id}")
    except Exception as result:
        _log.exception(f"Err in ignch | G:{msg.ctx.guild.id} | Au:{msg.author_id}")
        cm = await get_card_msg(f"ERR! [{get_time()}] ignch", err_card=True)
        await msg.reply(cm)
        await bot.client.send(debug_ch, cm)  # 发送错误信息到指定频道


@bot.command(name="clear", case_sensitive=False)
async def clear_setting(msg: Message, *arg):
    try:
        log_msg(msg)
        gid = msg.ctx.guild.id
        conf_ret = await dataLog.select_link_conf(gid)
        if conf_ret == {}:  # 空dict代表无效
            text = "本频道并没有配置日志频道，机器人尚未启用\n可使用「/setch」命令设置日志频道\n详见「/lgh」帮助命令"
            return await msg.reply(await get_card_msg(text))

        ch_id = conf_ret["log_ch"]
        text = f"监听频道信息：(chn){ch_id}(chn)\n"
        text += f"监听频道ID：  {ch_id}"
        # 删除键值
        await dataLog.remove_link_conf(gid)
        # 发送信息
        cm = await get_card_msg(text, header_text="已清除本服务器的监听设置")
        await msg.reply(cm)
        _log.info(f"[clear] G:{msg.ctx.guild.id} | Au:{msg.author_id}")
    except Exception as result:
        _log.exception(f"Err in clear | G:{msg.ctx.guild.id} | Au:{msg.author_id}")
        cm = await get_card_msg(f"ERR! [{get_time()}] clear", err_card=True)
        await msg.reply(cm)
        await bot.client.send(debug_ch, cm)  # 发送错误信息到指定频道


#####################################################################################


async def check_invites(code: str):
    """判断邀请链接的api"""
    url = kook_base_url + "/api/v2/invites/" + code
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            ret = json.loads(await response.text())
            return ret


async def send_log(
    gid: str, chid: str, usrid: str, usrname: str, code: str, ret: str, log_ch_id: str
):
    """发送通知到日志频道"""
    text = f"用户id: {usrid}\n用户昵称: {usrname}\n"
    text += f"文字频道：(chn){chid}(chn)\n"
    text += f"该用户发送的邀请码: {code}\n"
    text += f"```\n{ret}\n```"
    cm = await get_card_msg(text, header_text=f"[{get_time()}] LinkGuard")
    # 发送日志
    log_ch = await bot.client.fetch_public_channel(log_ch_id)
    await log_ch.send(cm)


async def invite_ck(msg: Message, code: str, conf_info: dict):
    """监看url是否为当前频道,conf_info 为数据库中select的结果。
    Return Value:
    - True: not same guild_id
    - False: is same guild_id
    """
    gid = msg.ctx.guild.id  # 服务器id
    chid = msg.ctx.channel.id  # 文字频道id
    usrid = msg.author_id  # 发送链接的用户id
    usrname = f"{msg.author.username}#{msg.author.identify_num}"
    api_ret = "none"
    try:
        # 之前配置过ign，忽略此频道
        if chid in conf_info["ign_ch"]:
            return False
        # 判断是否为当前服务器
        api_ret = await check_invites(code)
        if api_ret["guild"]["id"] != gid:
            await dataLog.log_invite_code(
                gid, usrid, chid, code, api_ret["guild"]
            )  # 写入日志
            await send_log(
                gid, chid, usrid, usrname, code, api_ret["guild"], conf_info["log_ch"]
            )  # 发送通知
            _log.info(
                f"G:{gid} C:{chid} Au:{usrid}\n[ret] code:{code} | {api_ret['guild']}"
            )  # 日志
            return True  # 不是本服务器的邀请链接，返回true
        # 是本服务器返回false
        return False
    except KeyError as result:
        if "guild" in str(result) or "id" in str(result):
            _log.warning(
                f"G:{gid} C:{chid} Au:{usrid} | code:{code} | keyErr {result} | ret:{api_ret}"
            )
            return False  # 出现了keyerr无法正常判断，认为是本服务器id
        # 其他情况依旧raise
        raise result


@bot.on_message()
async def link_guard(msg: Message):
    """监看本频道的邀请链接"""
    log_ch_id = config.DEBUG_CH
    gid, card_text = "none", "none"
    try:
        # 1.是私聊，直接退出
        if isinstance(msg, PrivateMessage):
            return
        # 2.查询配置
        gid = msg.ctx.guild.id  # 服务器id
        conf_ret = await dataLog.select_link_conf(gid)  # 查询
        if conf_ret == {}:
            return  # 必须要配置日志频道，才会启用
        log_ch_id = conf_ret["log_ch"]  # 日志频道
        # 3.判断消息里面有没有邀请链接
        text = msg.content  # 消息内容
        link_index = text.find("https://kook.top/")  # 返回子串开头的下标
        link_end_index = text.find("](")  # 链接会以markdown的方式传入[url](url)
        if link_index == -1:  # 没有这个子串，代表没有邀请链接，直接退出
            return
        # 4.取出邀请链接的code
        code = text[link_index + 17 : link_index + 23]  # 这里默认他是6位邀请链接，但出现过少于6个的情况
        if link_end_index == -1:  # 找不到代表传入的link格式不是md，尝试取6位并删除可能的超宽字符
            code = code.replace("]", "")  # 少于6个会多出来一个]
        else:  # 传入的格式是kmd，直接从下标处取
            code = text[link_index + 17 : link_end_index]

        ret = await invite_ck(msg, code, conf_ret)  # 检查是否为当前服务器
        if not ret:  # 是本服务器的邀请链接，推出
            return
        # 不是本服务器的邀请链接
        card_text = f"(met){msg.author_id}(met)\n请勿发送其他服务器的邀请链接！"
        # 判断是否有配置过个性化回复消息
        info_set = await dataLog.select_link_inform(gid)
        if info_set:
            card_text = info_set["inform"].replace(
                r"{met}", f"(met){msg.author_id}(met)"
            )
            await msg.reply(card_text, type=MessageTypes.CARD)
        else:
            cm = CardMessage(
                Card(Module.Section(Element.Text(card_text, Types.Text.KMD)))
            )
            await msg.reply(cm)  # 发送提示
        # 删除邀请链接消息
        await msg.delete()
        _log.info(
            f"G:{gid} C:{msg.ctx.channel.id} Au:{msg.author_id} | inform & msg.delete"
        )

    except requester.HTTPRequester.APIRequestFailed as result:
        _log.exception(f"APIRequestFailed in link_guard")
        if "无删除权限" in str(result):
            ch = await bot.client.fetch_public_channel(log_ch_id)
            await ch.send(await get_card_msg("【重要】请为机器人开启本服务器的 `消息管理` 权限"))
            await dataLog.remove_link_conf(gid)  # 删除服务器键值
            _log.warning(f"[APIRequestFailed] del G:{gid} in set")
        elif "message/create" in str(result) and "没有权限" in str(result):
            pass
        elif "json" in str(result):
            _log.info(f"[link_guard] card_text | {card_text}")
    except client_exceptions.ClientConnectorError as result:
        if "kookapp.cn" in str(result):
            return _log.warning(f"ERR! {str(result)}")
        _log.exception(f"aiohttp Err in link_guard| G:{gid}")
    except Exception as result:
        err_str = f"ERR! [{get_time()}] link_guard | G:{gid}\n```\n{traceback.format_exc()}\n```"
        _log.exception(f"Err in link_guard | G:{gid}")
        await debug_ch.send(await get_card_msg(err_str))  # 发送错误信息到指定频道


#############################################################################


# 开机任务
@bot.on_startup
async def startup_task(b: Bot):
    try:
        global debug_ch
        # 获取debug频道
        debug_ch = await bot.client.fetch_public_channel(config.DEBUG_CH)
        _log.info("[BOT.START] fetch debug channel success")
        await dataLog.link_conf_transfer()
    except:
        _log.exception(f"[BOT.START] ERR!")
        os.abort()


# botmarket通信
@bot.task.add_interval(minutes=25)
async def botmarket():
    api = "http://bot.gekj.net/api/v1/online.bot"
    headers = {"uuid": "1d266c78-30b2-4299-b470-df0441862711"}
    async with aiohttp.ClientSession() as session:
        await session.post(api, headers=headers)


# kill命令
@bot.command(name="kill", case_sensitive=False)
async def kill_bot_cmd(msg: Message, at_text="", *arg):
    """`/kill @机器人` 下线bot"""
    try:
        log_msg(msg)
        # 如果不是管理员直接退出，不要提示
        if not is_admin(msg.author_id):
            return
        # 必须要at机器人，或者私聊机器人
        cur_bot = await bot.client.fetch_me()
        if isinstance(msg, PrivateMessage) or f"(met){cur_bot.id}(met)" in at_text:
            # 发送信息
            cm = await get_card_msg(
                f"[KILL] 保存全局变量成功，linkguard bot下线\n当前时间：{get_time()}"
            )
            await msg.reply(cm)
            # 打印日志
            _log.info(f"KILL | bot-off\n")
            os._exit(0)  # 退出程序
        else:
            _log.info(f"[kill] invalid kill | {msg.content}")
    except:
        _log.exception(f"Err in kil | Au:{msg.author_id}")
        cm = await get_card_msg(f"ERR! [{get_time()}] kill", err_card=True)
        await msg.reply(cm)


# 开机 （如果是主文件就开机）
if __name__ == "__main__":
    # 开机的时候打印一次时间，记录开启时间
    _log.info(f"[BOT] Start at {get_time()}")
    bot.run()
