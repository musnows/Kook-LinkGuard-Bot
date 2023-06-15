# encoding: utf-8
# 本文件仅供replit部署使用
# https://blog.musnow.top/posts/2556995516/
# 如果您是在云服务器/本地电脑部署本bot，请忽略此文件
# 在replit部署之后，请使用类似uptimerobot的服务来请求replit的url，否则5分钟不活动会休眠

import asyncio
from aiohttp import web,web_request
## 主文件
from main import bot,get_time,_log,config
## 初始化节点
routes = web.RouteTableDef()

## 请求routes的根节点
@routes.get('/')
async def hello_world(request:web_request.Request):
    return web.Response(body="bot alive")

## 添加routes到app中
app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    _log.info(f"[BOT] Start in replit {get_time()}")
    if config["ws"]: # websocket 才需要同时运行web app和机器人
        HOST,PORT = '0.0.0.0',14725
        asyncio.get_event_loop().run_until_complete(
            asyncio.gather(web._run_app(app, host=HOST, port=PORT), bot.start()))
    else:
        bot.run() # webhook直接启动就可以了
