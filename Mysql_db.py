import pymysql
import datetime


class MysqlConnect(object):
    # 魔法方法，初始化，构造函数
    def __init__(self, host, user, password, database, port):
        '''
        :param host: IP str
        :param user: 数据库用户 str
        :param password: 密码 str
        :param port: 端口号 int 
        :param database: 数据库名 str 
        :param chartset: 数据库码格式
        '''
        self.db = pymysql.connect(host=host, user=user, password=password, port=port, database=database, charset='utf8')
        self.cursor = self.db.cursor()
    
    # 将插入的数据写成元组传入
    def exec_data(self, sql, data=None):
        # 执行SQL语句
        self.cursor.execute(sql, data)
        # 提交到数据库执行
        self.db.commit()
    
    # sql拼接时使用repr()，将字符串原样输出
    def exec(self, sql):
        self.cursor.execute(sql)
        # 提交到数据库执行
        self.db.commit()
    
    def select(self, sql):
        self.cursor.execute(sql)
        # 获取所有记录列表
        results = self.cursor.fetchall()
        return len(results) # 返回总条数

    def selectall(self, sql):
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        return results

    def selectone(self, sql):
        self.cursor.execute(sql)
        results = self.cursor.fetchone()
        return results
    
    def __del__(self):
        self.cursor.close()
        self.db.close()

    def getidbyserial(self, serial):
        sql = "select id from device_device where serial=%s" % repr(serial)
        res = self.selectone(sql)
        if res == None or len(res) <= 0:
            return -1;
        else:
            return res[0]

      # 0905170211: 2020/7/20 18:19
    def getidbyalarm_typename(self, typename):
        sql = "select id from device_alarmtype where name=%s" % repr(typename)
        res = self.selectone(sql)
        if res == None or len(res) <= 0:
            return -1;
        else:
            return res[0]
    # end

    # 0905170211: 2020/7/20 19:27
    def insertNormalData_ontimedata(self, dev_id, data):
        sql = "insert into device_devicedata(PM25, PM10, SO2, NO2, CO, O3, \
               WindSpeed, WindDirection, Light, CO2, Temperature, Humidity, \
               AirPressure, time, device_id) \
               values(%d, %d, %d, %d, %d, %d, %d, %s, %d, %d, %d, %d, %f, %s, %d)" \
              % (data["PM25"], data["PM10"], data["SO2"], data["NO2"], data["CO"], \
                 data["O3"], data["WindSpeed"], repr(data["WindDirection"]), data["Light"], \
                 data["CO2"], data["Temperature"], data["Humidity"], data["AirPressure"], \
                 repr(str(datetime.datetime.now())), dev_id)

        self.exec_data(sql)


    def getidbydevicedata_device_id(self, device_id):
        sql = "select id from device_devicedata where device_id=%d" % device_id
        # print(sql)
        res = self.selectone(sql)
        # print(res, type(res))
        if res == None or len(res) <= 0:
            return False
        else:
            return True

    # end

    def getkeybyserial(self, serial):
        dev_id = self.getidbyserial(serial)
        if dev_id < 0:
            return "null"
        sql = "select dev_key from device_devicesecret where device_id=%d" % dev_id
        res = self.selectone(sql)
        if res == None or len(res) <= 0:
            return "null";
        else:
            return res[0]

    def updateSettingsResp(self, serial):
        dev_id = self.getidbyserial(serial)
        if dev_id < 0:
            return False
        sql = "update device_deviceconf set update_status=%d, device_update_time=%s where device_id_id=%d" \
              % (True, repr(str(datetime.datetime.now())), dev_id)
        self.exec_data(sql)
        return True

    def updateLastLoginTime(self, serial):
        sql = "update device_device set last_login_time=%s where serial=%s" % (repr(str(datetime.datetime.now())), serial)
        self.exec_data(sql)
        return True

    def updateLastLogoutTime(self, serial):
        sql = "update device_device set last_logout_time=%s where serial=%s" % (repr(str(datetime.datetime.now())), serial)
        self.exec_data(sql)
        return True

    def insertNormalData(self, serial, data):
        dev_id = self.getidbyserial(serial)
        if dev_id < 0:
            return False
        sql = "insert into device_devicehistorydata(PM25, PM10, SO2, NO2, CO, O3, \
               WindSpeed, WindDirection, Light, CO2, Temperature, Humidity, \
               AirPressure, time, device_id) \
               values(%d, %d, %d, %d, %d, %d, %d, %s, %d, %d, %d, %d, %f, %s, %d)" \
              % (data["PM25"], data["PM10"], data["SO2"], data["NO2"], data["CO"], \
                 data["O3"], data["WindSpeed"], repr(data["WindDirection"]), data["Light"], \
                 data["CO2"], data["Temperature"], data["Humidity"], data["AirPressure"], \
                 repr(str(datetime.datetime.now())), dev_id)
        # print(sql)
        self.exec_data(sql)

        sql = "update device_devicedata set PM25=%d, PM10=%d, SO2=%d, NO2=%d, CO=%d, O3=%d, \
               WindSpeed=%d, WindDirection=%s, Light=%d, CO2=%d, Temperature=%d, Humidity=%d, \
               AirPressure=%f, time=%s where device_id=%d" \
              % (data["PM25"], data["PM10"], data["SO2"], data["NO2"], data["CO"], \
                 data["O3"], data["WindSpeed"], repr(data["WindDirection"]), data["Light"], \
                 data["CO2"], data["Temperature"], data["Humidity"], data["AirPressure"], \
                 repr(str(datetime.datetime.now())), dev_id)

        # 0905170211: 2020/7/20
        dev_id = self.getidbyserial(serial)
        if dev_id < 0:
            return False

        bool = self.getidbydevicedata_device_id(dev_id)
        print(bool)
        if bool:
            self.exec(sql)
        else:
            self.insertNormalData_ontimedata(dev_id, data)

        # end

        return True

# 0905170211: 2020/7/20 18:38 tested
    def insertAlarmData(self, serial, typename, value):
        dev_id = self.getidbyserial(serial)
        # print(dev_id)
        alarm_id = self.getidbyalarm_typename(typename)
        # print(alarm_id)
        if dev_id < 0:
            return False
        sql = "insert into device_alarmdata(value, time, status, alarmtype_id, device_id) \
               values(%d, %s, %d, %d, %d)" \
               % (value, repr(str(datetime.datetime.now())), 0, alarm_id, dev_id)
        self.exec_data(sql)
        return True
# end

# 0905170211: 2020/7/20 18:28
# if __name__ == '__main__':
#     # def __init__(self, host, user, password, database, port):
#     mc = MysqlConnect('127.0.0.1', 'root', 'root', 'dcs03', 3306)
#     # mc.exec('insert into auth_user(id, name, salary) values(%d, %s, %f)'%(1, repr('lize'), 4566.7))
#     res = mc.insertAlarmData("ASN11000012", "O3over", 10000)
#     print(res)
# end

# 0905170211: 2020/7/20
# if __name__ == '__main__':
#     keylist = ["PM25", "PM10", "SO2", "NO2", "CO", "O3", "WindSpeed", "Light", "CO2", "Temperature", "Humidity", "AirPressure"]
#     for k in keylist:
#         typename = k + "over"
#         print(typename)
# end

# 0905170211: 2020/7/20 19:01
# if __name__ == '__main__':
#     # # def __init__(self, host, user, password, database, port):
#     mc = MysqlConnect('127.0.0.1', 'root', 'root', 'dcs03', 3306)
#     # # mc.exec('insert into auth_user(id, name, salary) values(%d, %s, %f)'%(1, repr('lize'), 4566.7))
#     data = {'PM25': 120, 'PM10': 88, 'SO2': 391, 'NO2': 3294, 'CO': 22, 'O3': 20, 'WindSpeed': 7, 'WindDirection': 'WS', 'Light': 575, 'CO2': 569, 'Temperature': 25, 'Humidity': 80, 'AirPressure': 0.4}
#     # res = mc.insertNormalData("ASN11000012", message)
#     # # print(res)
#
#     dev_id = 8
#     sql = "update device_devicedata set PM25=%d, PM10=%d, SO2=%d, NO2=%d, CO=%d, O3=%d, \
#                WindSpeed=%d, WindDirection=%s, Light=%d, CO2=%d, Temperature=%d, Humidity=%d, \
#                AirPressure=%f, time=%s where device_id = %d " \
#           % (data["PM25"], data["PM10"], data["SO2"], data["NO2"], data["CO"], \
#              data["O3"], data["WindSpeed"], repr(data["WindDirection"]), data["Light"], \
#              data["CO2"], data["Temperature"], data["Humidity"], data["AirPressure"], \
#              repr(str(datetime.datetime.now())), dev_id)
#
#     mc.exec(sql)
# 哎，sql语句里面, time后面多了一个逗号，太坑了
# end
