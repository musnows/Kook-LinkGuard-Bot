import time
import json
import sys

#将获取当前时间封装成函数方便使用
def GetTime():
    return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())
# 写入文件
def write_file(path: str, value):
    with open(path, 'w', encoding='utf-8') as fw2:
        json.dump(value, fw2, indent=2, sort_keys=True, ensure_ascii=False)
# 读取文件
def open_file(path:str):
    with open(path, 'r', encoding='utf-8') as f:
        tmp = json.load(f)
    return tmp


# 设置日志文件的重定向
def logDup(path:str='./log.txt'):
    file =  open(path, 'a')
    sys.stdout = file 
    sys.stderr = file
# 刷新缓冲区
def logFlush():
    sys.stdout.flush() # 刷新缓冲区
    sys.stderr.flush() # 刷新缓冲区