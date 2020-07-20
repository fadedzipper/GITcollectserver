import sys
import json
from twisted.internet.protocol import ServerFactory, connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.python import log
import threading
import Mysql_db
import datetime
import data_package


mdb = Mysql_db.MysqlConnect('127.0.0.1', 'root', 'root', 'dcs03', 3306)
keylist = ["PM25", "PM10", "SO2", "NO2", "CO", "O3", "WindSpeed", "Light", "CO2", "Temperature", "Humidity", "AirPressure"]
# 队列
web_req_queue, web_resp_queue = None, None
delimiter = b'\r\n\r\n'
encoding = 'gb2312'

class DeviceControlResponseProcess(object):
    """
    设备控制返回处理
    """
    def __init__(self, client, data):
        self.client = client
        self.data = data

    def execute(self):
        key = mdb.getkeybyserial(self.data['serialnum'])
        # 秘钥不对数据丢弃
        if key != self.data['key']:
            return
        device_data = self.data
        global web_resp_queue
        web_resp_queue.put(device_data)


class RealTimeDataProcess(object):
    """
    采集数据处理类
    """
    def __init__(self, client, data):
        self.client = client
        self.data = data

    def execute(self):
        key = mdb.getkeybyserial(self.data['serialnum'])
        # 秘钥不对数据丢弃
        if key != self.data['key']:
            return
        # 整理数据，或存入数据库，或发往队列
        print(self.data)
        # mdb.insertNormalData(self.data['serialnum'], self.data['message'])


class AlarmDataProcess(object):
    """
    处理报警数据类
    """
    def __init__(self, client, data):
        self.client = client
        self.data = data

    def execute(self):
        print(self.data)
        key = mdb.getkeybyserial(self.data['serialnum'])
        # 秘钥不对数据丢弃
        if key != self.data['key']:
            return
        dev_id = mdb.getidbyserial(self.data['serialnum'])
        if dev_id < 0:
            return
        for k in keylist:
            if self.data['message'][k]['warn']:

                # 0905170211: insert into database
                print("insert data to db.")
                typename = k + "over"
                mdb.insertAlarmData(self.data['serialnum'], typename, self.data['message'][k]['value'])
                # 0905170211: end


class RegisterDataProcess(object):
    """
    处理注册数据类
    """
    def __init__(self, client, data):
        self.client = client
        self.data = data

    def execute(self):
        sql = "insert into device_device(serial, mac, is_register, is_enable, is_online, register_time, last_login_time) \
                values(%s, %s, %d, %d, %d, %s, %s)" \
              % (repr(self.data['serialnum']), repr(self.data['mac']),
                 False, True, True, repr(str(datetime.datetime.now())), repr(str(datetime.datetime.now())))
        try:
            mdb.exec_data(sql)
        except Exception as e:
            print(e)
            register_resp_except = {
                'type': 'download',
                'option': 'register-except',
                'code': 1
            }
            self.client.send(json.dumps(register_resp_except))
            return
        sql = "select id from device_device where serial = %s and mac = %s" \
              % (repr(self.data['serialnum']), repr(self.data['mac']))
        res = mdb.selectone(sql)
        if len(res) <= 0:
            print("注册设备时，未查询到相应设备信息")
            register_resp_except = {
                'type': 'download',
                'option': 'register-except',
                'code': 2
            }
            self.client.send(json.dumps(register_resp_except))
            return

        sql = "insert into device_devicesecret(dev_passwd, dev_key, device_id)  \
               values(%s, %s, %d)" \
            % (repr(self.data['passwd']), repr(self.data['key']), res[0])
        try:
            mdb.exec_data(sql)
        except Exception as e:
            print(e)
            register_resp_except = {
                'type': 'download',
                'option': 'register-except',
                'code': 3
            }
            self.client.send(json.dumps(register_resp_except))
            return

        device_register_resp = {
            'type': 'download',
            'option': 'resp-register',
            'serialnum': 'ASN11000012',
            'key': 'www.briup.com/ASN11000012',
            'active': 1
        }
        self.client.send(json.dumps(device_register_resp))


class OnlineDataProcess(object):
    """
    处理设备上线、下线数据类
    """
    def __init__(self, client, data):
        self.client = client
        self.data = data

    def login(self):
        mdb.updateLastLoginTime(self.data['serialnum'])

    def logout(self):
        mdb.updateLastLogoutTime(self.data['serialnum'])


class SettingRespProcess(object):
    """
    处理设备配置反馈数据
    """
    def __init__(self, client, data):
        self.client = client
        self.data = data

    def handle(self):
        dev_key = mdb.getkeybyserial(self.data['serialnum'])
        if dev_key == self.data['key']:
            ret = mdb.updateSettingsResp(self.data['serialnum'])
            if not ret:
                log.msg("处理配置反馈信息时，更新数据库失败.")


class ActiveRespProcess(object):
    """
    处理设备激活反馈数据
    """
    def __init__(self, client, data):
        self.client = client
        self.data = data

    def handle(self):
        key = mdb.getkeybyserial(self.data['serialnum'])
        # 秘钥不对数据丢弃
        if key != self.data['key']:
            return
        log.msg("设备(%s)已经激活完成." % self.data['serialnum'])
        # -- [201700100010012：2020-07-20 11:08]
        # coding here
        # -- [201700100010012: End]


class CmdProtocol(LineReceiver):
    """
    客户端处理类
    """
    delimiter = b'\r\n\r\n'
    encoding = 'gb2312'

    def __init__(self):
        super().__init__()
        self.serial_code = '0'
        self.client_ip = "0.0.0.0"
        self.client_port = 0

    def send(self, data):
        self.transport.write(data.encode(self.encoding) + self.delimiter)

    def processCmd(self, line):
        """
        数据处理函数
        """
        try:
            data = json.loads(line)
            msg_type = data['type']
            if msg_type == 'hearted':
                print("hearted message, ignore.")
                # self.send(line)
            elif msg_type == 'upload':
                msg_option = data['option']
                if msg_option == 'device-data':
                    RealTimeDataProcess(self, data).execute()
                elif msg_option == 'warn-data':
                    AlarmDataProcess(self, data).execute()
                elif msg_option == 'register':
                    self.serial_code = data['serialnum']
                    RegisterDataProcess(self, data).execute()
                elif msg_option == 'online':
                    self.serial_code = data['serialnum']
                    OnlineDataProcess(self, data).login()
                elif msg_option == 'offline':
                    OnlineDataProcess(self, data).logout()
                elif msg_option == 'settings':
                    SettingRespProcess(self, data).handle()
                elif msg_option == 'active-resp':
                    ActiveRespProcess(self, data).handle()
                else:
                    print("Others")
            else:
                print('消息类型不识别')
        except Exception as e:
            return e

    def connectionMade(self):
        """
        客户端连接时自动调用
        """
        self.client_ip, self.client_port = self.transport.getPeer(), self.transport.getPeer().port
        print("client connection from %s" % self.client_ip)
        if len(self.factory.clients) >= self.factory.clients_max:
            print("too many connection, bye!")
            self.client_ip = None
            self.transport.loseConnection()
        else:
            self.factory.clients.append(self)

    def connectionLost(self, reason=connectionDone):
        """
        客户端断开时自动调用
        """
        serial_code = self.serial_code
        print('lost connection from %s' % serial_code)
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        """
        收到一行信息时自动调用
        """
        self.processCmd(line.decode(self.encoding))


def process_web_queue():
    """
    处理web请求
    """
    global web_req_queue
    while True:
        data = web_req_queue.get()
        # print("接收20001端口，命令："+str(data))
        # print(type(data))
        msg_type = data['type']
        if msg_type == 'download':
            serial_code = data['serialnum']
            for client in factory.clients:
                # print(client)
                if not hasattr(client, 'serial_code'):
                    continue
                if client.serial_code == serial_code:
                    msg_option = data['option']
                    if msg_option == 'active':
                        client.send(json.dumps(data))
                    elif msg_option == 'updateconf':
                        # 从数据库获取设备配置信息发送给硬件
                        print("updateconf")
                        sql = "select id from device_device where serial = %s" % (repr(data['serialnum']))
                        res = mdb.selectone(sql)
                        if len(res) <= 0:
                            print("查询设备配置时，未查询到指定设备")
                            break

                        sql = "select PM25, PM10, SO2, NO2, CO, O3, WindSpeed, Light, CO2, Temperature, Humidity, AirPressure, Frequency " \
                              " from device_deviceconf where device_id_id = %d" % (res[0])
                        res = mdb.selectone(sql)
                        if len(res) <= 0:
                            print("查询设备配置时，未查询到配置信息")
                            break
                        data_package.settings_data['serialnum'] = data['serialnum']
                        data_package.settings_data['key'] = data['key']
                        data_package.settings_data['message']['PM25'] = res[0]
                        data_package.settings_data['message']['PM10'] = res[1]
                        data_package.settings_data['message']['SO2'] = res[2]
                        data_package.settings_data['message']['NO2'] = res[3]
                        data_package.settings_data['message']['CO'] = res[4]
                        data_package.settings_data['message']['O3'] = res[5]
                        data_package.settings_data['message']['WindSpeed'] = res[6]
                        data_package.settings_data['message']['Light'] = res[7]
                        data_package.settings_data['message']['CO2'] = res[8]
                        data_package.settings_data['message']['Temperature'] = res[9]
                        data_package.settings_data['message']['Humidity'] = res[10]
                        data_package.settings_data['message']['AirPressure'] = res[11]
                        data_package.settings_data['message']['Frequency'] = res[12]
                        client.send(json.dumps(data_package.settings_data))
                    else:
                        print("无法识别的Web申请...")
                    break
            else:
                log.msg('没有合适的网关')
        else:
            log.msg('解析web请求时，遇到无法识别的数据包类型')


class MyFactory(ServerFactory):
    protocol = CmdProtocol

    def __init__(self, clients_max=10):
        self.clients_max = clients_max
        self.clients = []


factory = MyFactory(5)


def startup(web_req_queue_parm, web_resp_queue_parm):
    global web_req_queue, web_resp_queue
    web_req_queue, web_resp_queue = web_req_queue_parm, web_resp_queue_parm
    threading.Thread(target=process_web_queue).start()
    log.startLogging(sys.stdout)
    reactor.listenTCP(20000, factory)
    reactor.run()
    print('采集服务已启动')

