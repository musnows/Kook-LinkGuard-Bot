# encoding: utf-8
import os
import json
import time
import sqlite3
import asyncio

from .myLog import _log

DBSqlLock = asyncio.Lock()
"""日志操作上锁"""

DB_NAME = 'config/linklog.db'
"""sqlite3数据库文件路径"""

LINK_LOG_CREATE = "CREATE TABLE IF NOT EXISTS link_log(\
                        guild_id TEXT NOT NULL,\
                        user_id TEXT NOT NULL,\
                        channel_id TEXT NOT NULL DEFAULT '',\
                        invite_code TEXT NOT NULL,\
                        invite_info TEXT NOT NULL,\
                        insert_time TIMESTAMP DEFAULT (datetime('now', '+8 hours')));"
"""监看日志表"""
LINK_CONF_CREATE = "CREATE TABLE IF NOT EXISTS link_conf(\
                        guild_id TEXT NOT NULL UNIQUE,\
                        user_id TEXT NOT NULL,\
                        log_ch TEXT NOT NULL,\
                        ign_ch TEXT NOT NULL DEFAULT '[]',\
                        wth_ch TEXT NOT NULL DEFAULT '[]',\
                        update_time TIMESTAMP DEFAULT (datetime('now', '+8 hours')),\
                        insert_time TIMESTAMP DEFAULT (datetime('now', '+8 hours')));"
"""监看配置表"""
LINK_INFO_CREATE = "CREATE TABLE IF NOT EXISTS link_inform(\
                        guild_id TEXT NOT NULL UNIQUE,\
                        user_id TEXT NOT NULL,\
                        inform TEXT NOT NULL,\
                        update_time TIMESTAMP DEFAULT (datetime('now', '+8 hours')),\
                        insert_time TIMESTAMP DEFAULT (datetime('now', '+8 hours')));"
"""服务器监看配置表"""

INSERT_LINK_LOG = "INSERT INTO link_log (guild_id,user_id,channel_id,invite_code,invite_info) values (?,?,?,?,?);"
"""插入link_log表"""
INSERT_LINK_CONF = "INSERT INTO link_conf (guild_id,user_id,log_ch,ign_ch,wth_ch,update_time) values (?,?,?,?,?,?);"
"""插入link_conf表"""
UPDATE_LINK_CONF = "UPDATE link_conf SET user_id = ?, log_ch = ?, ign_ch = ?, wth_ch = ?, update_time = ? WHERE guild_id = ?;"
"""更新link_conf表"""
SELECT_LINK_CONF = "select * from link_conf where guild_id = ?;"
"""搜索link_conf表"""
DROP_LINK_CONF = "drop from link_conf where guild_id = ?;"
"""删除link_conf服务器键值"""
DROP_LINK_INFO = "drop from link_inform where guild_id = ?;"
"""删除link_inform服务器键值"""
INSERT_LINK_INFO = "INSERT INTO link_inform (guild_id,user_id,inform) values (?,?,?);"
"""插入link_inform表"""
UPDATE_LINK_INFO = "UPDATE link_inform SET user_id = ?, inform = ?, update_time = ? WHERE guild_id = ?;"
"""更新link_inform表"""
SELECT_LINK_INFO = "select * from link_inform where guild_id = ?;"
"""搜索link_inform表"""


# 先创建数据库中的表
link_db = sqlite3.connect(DB_NAME)
query = link_db.cursor()
query.execute(LINK_LOG_CREATE)
query.execute(LINK_CONF_CREATE)
link_db.commit() # 执行
link_db.close() # 关闭数据库（写入文件）


async def log_invite_code(gid:str,usrid:str,chid:str,invite_code:str,api_ret:dict):
    """服务器id，用户id，频道id，和邀请码api返回值 ret['guild']"""
    with sqlite3.connect(DB_NAME) as db:
        query = db.cursor()
        json_str = fr"{json.dumps(api_ret)}" # 原始字符串
        query.execute(INSERT_LINK_LOG,(gid,usrid,chid,invite_code,json_str)) # 需要执行的sql命令
        db.commit() # 执行sql
        _log.info(f"G:{gid} | Au:{usrid} | {invite_code} | sqlite3 log")


async def log_link_conf(gid:str,usrid:str,log_ch:str,ign_ch=[],wth_ch=[]):
    """服务器id，用户id，日志频道，忽略频道，监看频道"""
    global DBSqlLock
    async with DBSqlLock:
        with sqlite3.connect(DB_NAME) as db:
            query = db.cursor()
            sret = query.execute(SELECT_LINK_CONF,(gid,))
            if not sret.fetchall(): # 没有找到
                query.execute(INSERT_LINK_CONF,(gid,usrid,log_ch,json.dumps(ign_ch),json.dumps(wth_ch),time.time()))
            else: # 找到了
                query.execute(UPDATE_LINK_CONF,(usrid,log_ch,json.dumps(ign_ch),json.dumps(wth_ch),time.time(),gid))
                
            db.commit() # 执行sql
        _log.info(f"G:{gid} | Au:{usrid} | C:{log_ch} | sqlite3 conf")
        
    
async def log_link_inform(gid:str,usrid:str,inform:str):
    """服务器id，用户id，提醒文字(提前检查合法性再传入，)"""
    global DBSqlLock
    async with DBSqlLock:
        with sqlite3.connect(DB_NAME) as db:
            query = db.cursor()
            sret = query.execute(SELECT_LINK_INFO,(gid,))
            if not sret.fetchall(): # 没有找到
                query.execute(SELECT_LINK_INFO,(gid,usrid,json.dumps(inform),time.time()))
            else: # 找到了
                query.execute(SELECT_LINK_INFO,(usrid,json.dumps(inform),time.time(),gid))
        
        db.commit() # 执行sql
        _log.info(f"G:{gid} | Au:{usrid} | sqlite3 link_inform")

async def select_link_conf(gid:str):
    """服务器id查询，返回结果为dict;空dict代表没找到"""
    global DBSqlLock
    async with DBSqlLock:
        with sqlite3.connect(DB_NAME) as db:
            query = db.cursor()
            sret = query.execute(SELECT_LINK_CONF,(gid,))
            sret_list = sret.fetchall()
            if not sret_list: # 没有找到
                return {}
            
            info = sret_list[0]
            return {
                'guild_id':info[0],
                'user_id':info[1],
                'log_ch':info[2],
                'ign_ch':json.loads(info[3]),
                'wth_ch':json.loads(info[4]),
                'update_time':info[5],
                'insert_time':info[6]
            }


async def select_link_inform(gid:str):
    """服务器id查询，返回结果为dict;空dict代表没找到"""
    global DBSqlLock
    async with DBSqlLock:
        with sqlite3.connect(DB_NAME) as db:
            query = db.cursor()
            sret = query.execute(SELECT_LINK_INFO,(gid,))
            sret_list = sret.fetchall()
            if not sret_list: # 没有找到
                return {}
            
            info = sret_list[0]
            return {
                'guild_id':info[0],
                'user_id':info[1],
                'inform':info[2],
                'update_time':info[3],
                'insert_time':info[4]
            }



async def remove_link_conf(gid:str):
    """给服务器id，删除配置"""
    global DBSqlLock
    async with DBSqlLock:
        with sqlite3.connect(DB_NAME) as db:
            query = db.cursor()
            query.execute(DROP_LINK_CONF,(gid,))
            db.commit() # 执行


async def link_conf_transfer(path = "config/linkconf.json"):
    """使用这个函数，将旧版本json的配置文件转为新版本sqlite数据文件"""
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        link_conf = json.load(f)
    # 已经转换过了
    if 'set_transfer' in link_conf and link_conf['set_transfer']:
        return
    # 转换
    for gid,info in link_conf['set'].items():
        await log_link_conf(gid,"",info['log_ch'],info['ign_ch'],[])
    
    # 新增键值标识已经转换完毕了
    link_conf['set_transfer'] = True
    with open(path, 'w+', encoding='utf-8') as fw2:
        json.dump(link_conf, fw2, indent=2, sort_keys=True, ensure_ascii=False)
    _log.info("link conf transfer to sqlite3!")
