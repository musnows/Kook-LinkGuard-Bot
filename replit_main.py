# encoding: utf-8
# 本文件仅供replit部署使用
# 如果您是在云服务器/本地电脑部署本bot，请忽略此文件

from flask import Flask
from threading import Thread
# 初始化
app = Flask(' ')


# 设立根路径作为api调用
@app.route('/')
def home():
    text = "bot online!"
    print(text)
    return text


# 开始运行，绑定ip和端口
def run():
    app.run(host='0.0.0.0', port=8000)


# 通过线程运行
def keep_alive():
    t = Thread(target=run)
    t.start()


# 标准输出重定向至文件
from main import logDup, bot

logDup('./log/log.txt')
# 开机 （如果是主文件就开机）
if __name__ == '__main__':
    # 开机的时候打印一次时间，记录开启时间
    print(f"[BOT] Start in replit")
    keep_alive()  # 运行Flask
    bot.run()  # 运行机器人