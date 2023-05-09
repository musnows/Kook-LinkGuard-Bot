import json
from .files import config,LinkLog,write_link_log
from .myLog import _log

SQLITE_ENABLE = False if 'sqlite_enable' not in config else config['sqlite_enable']
"""是否启用sqlite3数据库"""

if SQLITE_ENABLE:
    import sqlite3
    DB_NAME = 'config/linkLog.db'
    """数据库名"""
    TB_CREATE = "CREATE TABLE IF NOT EXISTS link_log(guild_id TEXT NOT NULL,user_id TEXT NOT NULL,invite_code TEXT NOT NULL,invite_info TEXT NOT NULL);"
    """创建表"""
    # 先创建数据库中的表
    db = sqlite3.connect(DB_NAME)
    query = db.cursor()
    query.execute(TB_CREATE) # 需要执行的sql命令
    db.commit() # 执行
    db.close() # 关闭

    # 只有使用才会调用这个函数
    async def log_invite_code_sql(gid:str,usrid:str,invite_code:str,ret:dict):
        """将邀请码写入sql"""
        db = sqlite3.connect(DB_NAME)
        query = db.cursor()
        json_str = fr"{json.dumps(ret)}" # 原始字符串
        sql = f"INSERT INTO link_log values ('{gid}','{usrid}','{invite_code}','{json_str}');"
        _log.info(f"G:{gid} | Au:{usrid} | sql: {sql}")
        query.execute(sql) # 需要执行的sql命令
        db.commit() # 执行
        db.close() # 关闭
        _log.info(f"G:{gid} | Au:{usrid} | sqlite3 log | {ret['id']}")


async def log_invite_code_json(gid:str,usrid:str,ret:dict):
    """将邀请码写入json日志"""
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
    _log.info(f"G:{gid} | Au:{usrid} | write log | {ret['id']}")


async def log_invite_code(gid:str,usrid:str,invite_code:str,api_ret:dict):
    """服务器id，用户id，和邀请码api返回值 ret['guild']"""
    try:
        if SQLITE_ENABLE:
            await log_invite_code_sql(gid,usrid,invite_code,api_ret)
        else:
            await log_invite_code_json(gid,usrid,api_ret)
    except:
        _log.exception(f"ERR! G:{gid} | Au:{usrid}")