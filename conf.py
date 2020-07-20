import configparser

conf_path = './device_config.cfg'


class DeviceConfigure(object):
    def __init__(self):
        try:
            config = configparser.ConfigParser()
            config.read(conf_path)
            self.config = config
        except Exception as e:
            print(e)

        try:
            self.server_ip = config.get('server', 'ip')
            self.server_port = config.getint('server', 'port')
            self.device_serial = config.get('device', 'serial')
            self.device_passwd = config.get('device', 'passwd')
            self.device_key = config.get('device', 'key')
            self.device_disabled = config.getint('device', 'is_disabled')
            self.device_register = config.getint('device', 'is_register')
            self.device_active = config.getint('device', 'is_active')

            self.set_pm25 = config.getint('settings', 'PM25')
            self.set_pm10 = config.getint('settings', 'PM10')
            self.set_so2 = config.getint('settings', 'SO2')
            self.set_no2 = config.getint('settings', 'NO2')
            self.set_co = config.getint('settings', 'CO')
            self.set_o3 = config.getint('settings', 'O3')
            self.set_windspeed = config.getint('settings', 'WindSpeed')
            self.set_light = config.getint('settings', 'Light')
            self.set_co2 = config.getint('settings', 'CO2')
            self.set_temperature = config.getint('settings', 'Temperature')
            self.set_humidity = config.getint('settings', 'Humidity')
            self.set_airpressure = config.getint('settings', 'AirPressure')
            self.set_frequency = config.getint('settings', 'Frequency')
        except Exception as e:
            print(e)

    def __repr__(self):
        fmt = """
        [server]
        ip=%s
        port=%d
        [device]
        serial=%s
        passwd=%s
        key=%s
        is_disabled=%d
        is_register=%d
        is_active=%d
        [settings]
        PM25=%d
        PM10=%d
        SO2=%d
        NO2=%d
        CO=%d
        O3=%d
        WindSpeed=%d
        Light=%d
        CO2=%d
        Temperature=%d
        Humidity=%d
        AirPressure=%d
        Frequency=%d
        """
        return fmt % (
            self.server_ip, self.server_port, self.device_serial, self.device_passwd, self.device_key,
            self.device_disabled, self.device_register, self.device_active, self.device_timeout,
            self.set_pm25, self.set_pm10, self.set_so2, self.set_no2, self.set_co, set.set_o3,
            self.set_windspeed, self.set_light, self.set_co2, self.set_temperature, self.set_humidity,
            self.set_airpressure, self.set_frequency
        )

    def update_configure(self, group, key, value):
        self.config.set(group, key, value)
        with open(conf_path, "w") as f:
            self.config.write(f)


