# 心跳包
# 已上线的未注册设备，或者已上线的注册设备被禁用，发送心跳包，提示服务器设备在线状态
Hearted_Data = {
    'type': 'hearted',
    'option': 'normal',
    'serialnum': 'ASN11000012',
    'ip': '127.0.0.1',
    'mac': "AA:DD:00:FF:22:3C",
    'active': 0
}

# 监测设备常采集规数据上传
device_normal_data = {
    "type": "upload",
    "option": "device-data",
    "serialnum": "ASN11000012",
    "key": "test_key",
    "message": {
        "PM25": 0,
        "PM10": 0,
        "SO2": 0,
        "NO2": 0,
        "CO": 0,
        "O3": 0,
        "WindSpeed": 0,
        "WindDirection": "WN",
        "Light": 0,
        "CO2": 0,
        "Temperature": 0,
        "Humidity": 0,
        "AirPressure": 0
    }
}

# 监测设备告警信息数据包
device_warn_data = {
    "type": "upload",
    "option": "warn-data",
    "serialnum": "ASN11000012",
    "key": "test_key",
    "WarnName": "None",
    "WarnCount": 0,
    "message": {
        "PM25": {"value": 0, "warn": False},
        "PM10": {"value": 0, "warn": False},
        "SO2": {"value": 0, "warn": False},
        "NO2": {"value": 0, "warn": False},
        "CO": {"value": 0, "warn": False},
        "O3": {"value": 0, "warn": False},
        "WindSpeed": {"value": 0, "warn": False},
        "WindDirection": "WN",
        "Light": {"value": 0, "warn": False},
        "CO2": {"value": 0, "warn": False},
        "Temperature": {"value": 0, "warn": False},
        "Humidity": {"value": 0, "warn": False},
        "AirPressure": {"value": 0, "warn": False}
    },
    "content": "none"
}

# 设备上线、下线申请
device_online_req = {
    'type': 'upload',
    'option': 'online', #offline
    'ways': 'auto', #manual
    'serialnum': 'ASN11000012',
    'key': "test_key",
    'ip': '127.0.0.1',
    'mac': "AA:DD:00:FF:22:3C",
    'active': 1
}

# 设备注册申请
device_register = {
    'type': 'upload',
    'option': 'register',
    'serialnum': 'ASN11000012',
    'key': 'www.briup.com/ASN11000012',
    'passwd': "123456",
    'ip': '127.0.0.1',
    'mac': "AA:DD:00:FF:22:3C",
    'active': 0
}

# 设备注册反馈
device_register_resp = {
    'type': 'upload',
    'option': 'resp-register',
    'serialnum': 'ASN11000012',
    'key': 'www.briup.com/ASN11000012',
    'active': 1
}

# 设备激活通知
device_active = {
    'type': 'download',
    'option': 'active',
    'serialnum': 'ASN11000012',
    'key': 'real_key',
    'status': 1
}

# 设备激活反馈信息，由设备在激活成功后发送给服务器
device_active_resp = {
    'type': 'upload',
    'option': 'active-resp',
    'serialnum': 'ASN11000012',
    'key': 'real_key',
    'status': 1
}

# 设备配置信息
settings_data = {
    "type": "download",
    "option": "settings",
    "serialnum": "ASN11000012",
    "key": "real_key",
    "message": {
        "PM25": 0,
        "PM10": 0,
        "SO2": 0,
        "NO2": 0,
        "CO": 0,
        "O3": 0,
        "WindSpeed": 0,
        "Light": 0,
        "CO2": 0,
        "Temperature": 0,
        "Humidity": 0,
        "AirPressure": 0,
        "Frequency": 10
    }
}

# 设备配置响应
settings_resp = {
    "type": "upload",
    "option": "settings",
    "serialnum": "ASN11000012",
    "key": "real_key",
    'status': 1
}



