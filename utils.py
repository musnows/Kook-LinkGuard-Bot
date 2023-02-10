import time
import json

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