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
        if len(res) <= 0:
            return -1;
        else:
            return res[0]

    def getkeybyserial(self, serial):
        dev_id = self.getidbyserial(serial)
        if dev_id < 0:
            return "null"
        sql = "select dev_key from device_devicesecret where device_id=%d" % dev_id
        res = self.selectone(sql)
        if len(res) <= 0:
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
        self.exec_data(sql)

        sql = "update device_devicedata set PM25=%d, PM10=%d, SO2=%d, NO2=%d, CO=%d, O3=%d, \
               WindSpeed=%d, WindDirection=%s, Light=%d, CO2=%d, Temperature=%d, Humidity=%d, \
               AirPressure=%f, time=%s, where device_id=%d" \
              % (data["PM25"], data["PM10"], data["SO2"], data["NO2"], data["CO"], \
                 data["O3"], data["WindSpeed"], repr(data["WindDirection"]), data["Light"], \
                 data["CO2"], data["Temperature"], data["Humidity"], data["AirPressure"], \
                 repr(str(datetime.datetime.now())), dev_id)
        return True


# if __name__ == '__main__':
#     # def __init__(self, host, user, password, database, port):
#     mc = MysqlConnect('127.0.0.1', 'root', '740123', 'db_test', 3306)
#     # mc.exec('insert into auth_user(id, name, salary) values(%d, %s, %f)'%(1, repr('lize'), 4566.7))
#     res = mc.select('select * from auth_user')
#     print(res)


