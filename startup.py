# -*- coding : UTF-8 -*-
# 开发团队：杰普软件
# 开发人员：lllze
# 开发时间：2020/4/20 10:23
# 文件名称：startup.py.PY
# 开发工具：PyCharm


import sys
import datetime
import test
import web_server
import multiprocessing
from multiprocessing import Process, Queue
from twisted.python import log

web_req_queue, web_resp_queue = Queue(), Queue()


if __name__ == "__main__":
    log.startLogging(sys.stdout)
    log.msg('中控采集服务器 启动于 ' + str(datetime.datetime.now()))
    # 启动网关服务器进程
    multiprocessing.Process(target=test.startup, args=(web_req_queue, web_resp_queue)).start()
    # 启动web后台服务器进程
    multiprocessing.Process(target=web_server.startup, args=(web_req_queue, web_resp_queue)).start()
    log.msg('后台服务器启动成功')
