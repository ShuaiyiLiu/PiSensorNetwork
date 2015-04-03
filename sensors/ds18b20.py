'''
    This script gets values obtained from DS18B20 Temperature Sensor.
'''
import os
import sensorErrors

SENSOR_NAME = 'DS18B20'
VAL_NAME = 'Temperature'
VAL_UNIT = 'Celsius'
DEVICES_DIR = '/sys/bus/w1/devices'
SLAVE_DIR = 'w1_slave'
DIR_DIGITS = '28' # sensor's dirctory name starts with 28


def _load_kernel_modules():
    '''Load kernel module needed by temperature sensor'''
    os.system('modprobe w1-gpio');
    os.system('modprobe w1-therm');

def getUnit():
    return VAL_UNIT

def getValueName():
    return VAL_NAME

def getValue():
    '''Return temperature in Celsius'''
    if not os.path.isdir(DEVICES_DIR):
        _load_kernel_nodules()
    sensorPaths = [s for s in os.listdir(DEVICES_DIR) if s.startswith(DIR_DIGITS)]
    if len(sensorPaths) == 0: 
        raise sensorErrors.NoSensorFoundError(SENSOR_NAME)    
    # The following code won't work whenever any other loaded device has device
    # dir starts with '28'.
    sensorPath = os.path.join(DEVICES_DIR, sensorPaths[0], SLAVE_DIR)
    with open(sensorPath, 'r') as f:
        data = f.readlines()

    if data[0].strip()[-3:] != 'YES':
        raise sensorErrors.UnexpectedSensorError
    return float(data[1].split('=')[1]) / 1000.0
