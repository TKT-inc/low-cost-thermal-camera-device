import time
import yaml
from datetime import datetime
with open("configuration.yaml") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

# development flags
DEV_PRINT_PROCESS = cfg['developmentFlags']['printProcessTime']
DEV_PRINT_SEND_RECORD = cfg['developmentFlags']['printRecord']
DEV_PRINT_SEND_RECOGNIZE = cfg['developmentFlags']['printRecognize']
DEV_PRINT_SEND_REGISTER = cfg['developmentFlags']['printRegister']
DEV_PRINT_CONNECTION = cfg['developmentFlags']['printIoTConn']
DEV_PRINT_RECEIVE_DATA = cfg['developmentFlags']['printReceiveData']
DEV_PRINT_SEND_DATA = cfg['developmentFlags']['printSendData']

def logDetail(topic, content):
    print(topic + '___' + datetime.utcnow().strftime("%H:%M:%S.%f"))
    print('   ' + content)

def Log(topic='DEFAULT', message='content'):
    if (topic == 'PROCESS' and DEV_PRINT_PROCESS):
        logDetail(topic, message)

    elif (topic == 'REGISTER' and DEV_PRINT_SEND_REGISTER):
        logDetail(topic, message)

    elif (topic == 'RECORD' and DEV_PRINT_SEND_RECORD):
        logDetail(topic, message)

    elif (topic == 'RECOGNIZE' and DEV_PRINT_SEND_RECOGNIZE):
        logDetail(topic, message)

    elif (topic == 'CONNECTION' and DEV_PRINT_CONNECTION):
        logDetail(topic, message)

    elif (topic == 'RECEIVE_DATA' and DEV_PRINT_RECEIVE_DATA):
        logDetail(topic, message)

    elif (topic == 'SEND_DATA' and DEV_PRINT_SEND_DATA):
        logDetail(topic, message)

    elif (topic == 'DEFAULT'):
        logDetail(topic, message)