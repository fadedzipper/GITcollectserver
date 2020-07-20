# 模拟网关
# 功能介绍：
# 1、发送设备组中各设备、传感器实时数据
# 2、发送设备组中设备告警数据
import time
import sys
import random
import socket
import threading
import json
from multiprocessing.pool import ThreadPool
import conf
import uuid
import data_package


def get_mac_address():
    '''
    windows下的获取设备mac地址的方法
    '''
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])


DEV_MAC = get_mac_address()
DEV_IP = socket.gethostname()
# windows下的获取设备IP地址的方法
# DEV_IP = socket.gethostbyname(socket.gethostname())
# 获取设备静态配置信息
deviceConfig = conf.DeviceConfigure()
# 中控服务器配置
TCP_HOST = deviceConfig.server_ip
TCP_PORT = deviceConfig.server_port
BUFSIZ = 2048
keylist = ["PM25", "PM10", "SO2", "NO2", "CO", "O3", "WindSpeed", "WindDirection", "Light", "CO2", "Temperature",
           "Humidity", "AirPressure"]
windDir = ['None', 'N', 'WN', 'W', 'WS', 'S', 'ES', 'E', 'EN']

# TCP客户端套接字
tcpCliSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpCliSock.connect((TCP_HOST, TCP_PORT))

delimiter = b'\r\n\r\n'
ecoding = 'gb2312'
# 线程池
pool = ThreadPool(processes=10)
# 设备是否已经激活状态标记 0-未注册 1-已注册
is_register = deviceConfig.device_register
# 设备是否需要关机
is_shutdown = False


# 上线申请
class OnlineRequest(object):
    def __init__(self, data, rdata):
        self.data = data
        self.rdata = rdata

    def login(self):
        global is_register
        if not is_register:
            is_register = 0
            # 登录时检测到未注册，发送注册申请，无需发送上线申请
            self.rdata['serialnum'] = deviceConfig.device_serial
            self.rdata['key'] = str("www.briup.com/"+deviceConfig.device_serial)
            self.rdata['passwd'] = deviceConfig.device_passwd
            self.rdata['ip'] = DEV_IP
            self.rdata['mac'] = DEV_MAC
            self.rdata['active'] = is_register
            tcpCliSock.sendall(json.dumps(self.rdata).encode(ecoding) + delimiter)
            # time.sleep(1)
            frame = tcpCliSock.recv(BUFSIZ).decode(ecoding)
            rdf = json.loads(frame)
            t = rdf['type']
            ops = rdf['option']
            if t == 'download':
                if ops == 'resp-register':
                    is_register = 1
                    deviceConfig.device_register = is_register
                    deviceConfig.update_configure('device', 'is_register', str(is_register))
                    return True
                elif ops == 'register-except':
                    print("设备信息注册时发生异常，注册失败.")
                    return False
                else:
                    print("无法识别的注册反馈信息.")
                    return False
            else:
                print("注册时，接收到无法识别的数据包.")
                return False
        else:
            is_register = 1
            self.data['serialnum'] = deviceConfig.device_serial
            self.data['key'] = deviceConfig.device_key
            self.data['ways'] = 'manual'
            self.data['ip'] = DEV_IP
            self.data['mac'] = DEV_MAC
            self.data['active'] = deviceConfig.device_active
            tcpCliSock.sendall(json.dumps(self.data).encode(ecoding) + delimiter)
        return True

    def logout(self):
        global is_register
        if not deviceConfig.device_key or deviceConfig.device_key == "unregister":
            is_register = 0
        else:
            is_register = 1
        self.data['option'] = 'offline'
        self.data['serialnum'] = deviceConfig.device_serial
        self.data['key'] = deviceConfig.device_key
        self.data['ways'] = 'manual'
        self.data['ip'] = DEV_IP
        self.data['mac'] = DEV_MAC
        self.data['active'] = is_register
        tcpCliSock.sendall(json.dumps(self.data).encode(ecoding) + delimiter)


# 激活认证，每次设备上线，检查是否是已经激活的设备（未完善）
# class ConfirmDataProcessing(object):
#     def __init__(self, client, data):
#         self.client = client
#         self.data = data
#
#     def confirm(self):
#         global is_register
#         if not deviceConfig.device_key or deviceConfig.device_key == "unregister":
#             is_register = 0
#             tcpCliSock.sendall(json.dumps())
#         tcpCliSock.sendall(json.dumps(self.data).encode(ecoding) + delimiter)
#         return True


class HeartedData(object):
    def __init__(self, data):
        self.data = data

    def send(self):
        self.data['serialnum'] = deviceConfig.device_serial
        self.data['ip'] = DEV_IP
        self.data['mac'] = DEV_MAC
        self.data['active'] = deviceConfig.device_active
        tcpCliSock.sendall(json.dumps(self.data).encode('gb2312')+delimiter)


# 设备实时数据处理
class RealTimeDataProcessing(object):
    def __init__(self, data, warndata):
        self.data = data
        self.warndata = warndata
        self.warnflag = False

    def execute(self):
        # 含有数值的设备及传感器
        self.warnflag = False
        self.warndata['WarnCount'] = 0
        self.warndata['WarnName'] = 'None'
        self.warndata['content'] = 'None'
        self.warndata['key'] = deviceConfig.device_key
        self.data['key'] = deviceConfig.device_key
        for name in keylist:
            if name in self.data['message'].keys():
                # print(name)
                if name == "PM25":
                    value_pm25 = random.randrange(0, 240)
                    if value_pm25 > deviceConfig.set_pm25:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_pm25
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "PM25浓度过高，空气质量低"
                    else:
                        self.data['message'][name] = value_pm25
                elif name == 'PM10':
                    value_pm10 = random.randrange(0, 240)
                    if value_pm10 > deviceConfig.set_pm10:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_pm10
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "PM10浓度过高，空气质量低"
                    else:
                        self.data['message'][name] = value_pm10
                elif name == "SO2":
                    value_so2 = random.randrange(0, 1000)
                    if value_so2 > deviceConfig.set_so2:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_so2
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "空气中SO2浓度过高，空气质量低"
                    else:
                        self.data['message'][name] = value_so2
                elif name == "NO2":
                    value_no2 = random.randrange(0, 4000)
                    if value_no2 > deviceConfig.set_no2:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_no2
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "空气中NO2浓度过高，空气质量低"
                    else:
                        self.data['message'][name] = value_no2
                elif name == "CO":
                    value_co = random.randrange(0, 100)
                    if value_co > deviceConfig.set_co:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_co
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "空气中CO浓度过高，空气质量低"
                    else:
                        self.data['message'][name] = value_co
                elif name == "O3":
                    value_o3 = random.randrange(0, 850)
                    if value_o3 > deviceConfig.set_o3:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_o3
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "空气中O3浓度过高"
                    else:
                        self.data['message'][name] = value_o3
                elif name == "WindSpeed":
                    value_wspeed = random.randrange(0, 10)
                    if value_wspeed > deviceConfig.set_windspeed:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_wspeed
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "天气风力过大"
                    else:
                        self.data['message'][name] = value_wspeed
                elif name == "WindDirection":
                    value_wdir = random.randrange(0, 7)
                    if self.warnflag == True:
                        self.warndata['message'][name] = windDir[value_wdir]
                    else:
                        self.data['message'][name] = windDir[value_wdir]
                elif name == "Light":
                    value_light = random.randrange(0, 1800)
                    if value_light > deviceConfig.set_light:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_light
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "天气紫外线光照太强"
                    else:
                        self.data['message'][name] = value_light
                elif name == "CO2":
                    value_co2 = random.randrange(0, 1300)
                    if value_co2 > deviceConfig.set_co2:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_co2
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "空气中CO2浓度过高"
                    else:
                        self.data['message'][name] = value_co2
                elif name == "Temperature":
                    value_temp = random.randrange(-12, 60)
                    if value_temp > deviceConfig.set_temperature or value_temp < -10:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_temp
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "空气温度异常"
                    else:
                        self.data['message'][name] = value_temp
                elif name == "Humidity":
                    value_humi = random.randrange(0, 90)
                    if value_humi > deviceConfig.set_humidity:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_humi
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "空气过于潮湿"
                    else:
                        self.data['message'][name] = value_humi
                elif name == "AirPressure":
                    value_ap = round(random.uniform(0.5, 0.1), 2)
                    # if value_ap > 1.5 or value_ap < 0.8:
                    if value_ap > deviceConfig.set_airpressure:
                        self.warnflag = True
                        self.warndata['message'][name]['value'] = value_ap
                        self.warndata['message'][name]['warn'] = True
                        self.warndata['WarnName'] = name
                        self.warndata['WarnCount'] = self.warndata['WarnCount'] + 1
                        if self.warndata['WarnCount'] > 1:
                            self.warndata['content'] = "多项参数指标报警"
                            self.warndata['WarnName'] = "MultiWarn"
                        else:
                            self.warndata['content'] = "大气压强异常"
                    else:
                        self.data['message'][name] = value_ap
        if self.warnflag:
            return self.warndata
        else:
            return self.data

    def process(self):
        async_result = pool.apply_async(RealTimeDataProcessing.execute, (self,))
        return_val = async_result.get()
        return return_val


# 数据发送处理
class SendDataProcessing(object):
    def __init__(self, data):
        self.data = data

    def execute(self):
        send_data = json.dumps(self.data).encode(ecoding) + delimiter
        print(send_data)
        try:
            tcpCliSock.sendall(send_data)

        except Exception as e:
            return e

    def process(self):
        time_delay = deviceConfig.set_frequency
        if not time_delay:
            time_delay = 300
            print("Get timeout setting value error")
        pool.apply_async(SendDataProcessing.execute, (self,))
        time.sleep(time_delay)


# 接收服务器数据，并发线程函数
def received_data():
    frame = ''
    print('接收服务器数据线程已启动.')
    while True:
        frame = tcpCliSock.recv(BUFSIZ)
        if len(frame) == 0:
            print("网络连接已断开，请重新启动客户端")
            global is_shutdown
            is_shutdown = True
            break
        else:
            data = json.loads(frame.decode(ecoding))
            msg_type = data['type']
            if msg_type == 'download':
                msg_option = data['option']
                if msg_option == 'active':
                    if data['serialnum'] == deviceConfig.device_serial:
                        deviceConfig.device_key = data['key']
                        deviceConfig.device_active = data['status']
                        deviceConfig.update_configure('device', 'is_active', str(data['status']))
                        deviceConfig.update_configure('device', 'key', str(data['key']))
                        # 发送激活成功反馈[设备端配置成功]信息 给 服务器
                        data_package.device_active_resp['serialnum'] = deviceConfig.device_serial
                        data_package.device_active_resp['key'] = deviceConfig.device_key
                        data_package.device_active_resp['status'] = deviceConfig.device_active
                        tcpCliSock.sendall(json.dumps(data_package.device_active_resp).encode('gb2312') + delimiter)
                elif msg_option == 'updateconf':
                    if data['serialnum'] == deviceConfig.device_serial:
                        deviceConfig.update_configure('settings', 'PM25', str(data['message']['PM25']))
                        deviceConfig.update_configure('settings', 'PM10', str(data['message']['PM10']))
                        deviceConfig.update_configure('settings', 'SO2', str(data['message']['SO2']))
                        deviceConfig.update_configure('settings', 'NO2', str(data['message']['NO2']))
                        deviceConfig.update_configure('settings', 'CO', str(data['message']['CO']))
                        deviceConfig.update_configure('settings', 'O3', str(data['message']['O3']))
                        deviceConfig.update_configure('settings', 'WindSpeed', str(data['message']['WindSpeed']))
                        deviceConfig.update_configure('settings', 'Light', str(data['message']['Light']))
                        deviceConfig.update_configure('settings', 'CO2', str(data['message']['CO2']))
                        deviceConfig.update_configure('settings', 'Temperature', str(data['message']['Temperature']))
                        deviceConfig.update_configure('settings', 'Humidity', str(data['message']['Humidity']))
                        deviceConfig.update_configure('settings', 'AirPressure', str(data['message']['AirPressure']))
                        deviceConfig.update_configure('settings', 'Frequency', str(data['message']['Frequency']))
                        deviceConfig.set_pm25 = data['message']['PM25']
                        deviceConfig.set_pm10 = data['message']['PM10']
                        deviceConfig.set_so2 = data['message']['SO2']
                        deviceConfig.set_no2 = data['message']['NO2']
                        deviceConfig.set_co = data['message']['CO']
                        deviceConfig.set_o3 = data['message']['O3']
                        deviceConfig.set_windspeed = data['message']['WindSpeed']
                        deviceConfig.set_light = data['message']['Light']
                        deviceConfig.set_co2 = data['message']['CO2']
                        deviceConfig.set_temperature = data['message']['Temperature']
                        deviceConfig.set_humidity = data['message']['Humidity']
                        deviceConfig.set_airpressure = data['message']['AirPressure']
                        deviceConfig.set_frequency = data['message']['Frequency']
                        # 告诉服务器已经配置完成
                        data_package.settings_resp['serialnum'] = data['serialnum']
                        data_package.settings_resp['key'] = data['key']
                        data_package.settings_resp['status'] = 1
                        tcpCliSock.sendall(json.dumps(data_package.settings_resp).encode('gb2312')+delimiter)
                else:
                    print('无法识别的服务器操作')
            else:
                print("无法识别的服务器数据包.")
        time.sleep(1)


if __name__ == "__main__":
    # 设备登录 - 上线
    login_res = OnlineRequest(data_package.device_online_req, data_package.device_register).login()
    if not login_res:
        print("设备注册失败")
        sys.exit(-1)
    # 启动一个读取数据的线程
    print("启动一个读取数据的线程")
    # multiprocessing.Process(target=received_data).start()
    read_thread = threading.Thread(target=received_data)
    # read_thread.setDaemon(True)
    read_thread.start()
    # 若设备未注册，则持续发送心跳包
    print('若设备未激活，则持续发送心跳包')
    while deviceConfig.device_active == 0:
        HeartedData(data_package.Hearted_Data).send()
        time.sleep(deviceConfig.set_frequency)
    print("设备已经激活，开始发送采集数据...")
    while not is_shutdown:
        # 若注册设备被禁用，则持续发送心跳包
        if deviceConfig.device_disabled == 1:
            HeartedData(data_package.Hearted_Data).send()
            time.sleep(deviceConfig.set_frequency)
            continue
        # 发送采集数据
        realtimedataprocess = RealTimeDataProcessing(data_package.device_normal_data, data_package.device_warn_data)
        real_time_data = realtimedataprocess.process()
        send_real_time_data = SendDataProcessing(real_time_data)
        send_real_time_data.process()
