# -*- coding : UTF-8 -*-
# 开发团队：杰普软件
# 开发人员：lllze
# 开发时间：2020/4/20 9:17
# 文件名称：web_server.PY
# 开发工具：PyCharm


import sys
import os
import hashlib
import json
import threading
from twisted.internet.protocol import ServerFactory, ProcessProtocol, connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet import reactor, threads
web_req_queue, web_resp_queue = None, None


class ActiveProcess(object):
    def __init__(self, client, data):
        self.data = data
        self.client = client

    def execute(self):
        global web_req_queue
        web_req_queue.put(self.data)


class DeviceControlProcess(object):
    """
    处理设备控制类
    """
    def __init__(self, client, data):
        self.data = data
        self.client = client

    def execute(self):
        global web_req_queue
        web_req_queue.put(self.data)


# class DeviceControlResponseProcess(object):
#     def __init__(self, client, data):
#         self.data = data
#         self.client = client


def control_response():
    global web_resp_queue
    while True:
        if not web_resp_queue.empty():
            log.msg("消息队列不为空")
            data = web_resp_queue.get()
            print(data)
            msg_type = data['msg_type']
            if msg_type == 'device_operations':
                group_code = data['group_code']
                for client in factory.clients:
                    if not hasattr(client, 'group_code'):
                        continue
                    if client.group_code == group_code:
                        client.send(json.dumps(data))
                        break
                    else:
                        log.msg('没有合适的网关')
            else:
                log.msg('-------')
            # print('20000控制返回队列释放：'+json.dumps(data))


class CmdProtocol(LineReceiver):
    delimiter = b'\r\n\r\n'
    encoding = 'gb2312'

    def send(self, data):
        self.transport.write(data.encode(self.encoding) + self.delimiter)

    def processCmd(self, line):
        try:
            data = json.loads(line)
            msg_type = data['type']
            if msg_type == 'download':
                # msg_option = data['option']
                # if msg_option == "active":
                #     #
                # elif msg_option == 'updateconf':
                #     #
                # else:
                #     print("无法识别的Web申请")
                DeviceControlProcess(self, data).execute()
            else:
                log.msg('消息类型不识别')
        except Exception as e:
            log.msg(e)
            log.msg('msg not json type')

    def connectionMade(self):
        self.client_ip, self.client_port = self.transport.getPeer().host, self.transport.getPeer().port
        log.msg("Client connection from %s, %s" % (self.client_ip, self.client_port))
        if len(self.factory.clients) >= self.factory.clients_max:
            log.msg("Too many connection. bye!")
            self.client_ip = None
            self.transport.loseConneciont()
        else:
            self.factory.clients.append(self.client_ip)

    def connectionLost(self, reason=connectionDone):
        log.msg('Lost client connection. Reason: %s' % reason)
        if self.client_ip:
            self.factory.clients.remove(self.client_ip)

    def lineReceived(self, line):
        # print(line)
        # print("原始数据接收:" + str(line))
        log.msg('Cmd received from %s : %s' % (self.client_ip, line.decode(self.encoding)))
        self.processCmd(line.decode(self.encoding))


class MyFactory(ServerFactory):
    protocol = CmdProtocol

    def __init__(self, clients_max=10):
        self.clients_max = clients_max
        self.clients = []


factory = MyFactory(5)


def startup(web_req_queue_parm, web_resp_queue_parm):
    global web_req_queue, web_resp_queue
    web_req_queue = web_req_queue_parm
    web_resp_queue = web_resp_queue_parm

    threading.Thread(target=control_response).start()
    log.startLogging(sys.stdout)
    reactor.listenTCP(20001, factory)
    reactor.run()
    log.msg("后台服务已经启动")

