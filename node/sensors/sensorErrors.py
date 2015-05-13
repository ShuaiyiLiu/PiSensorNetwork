'''
    This module provides error classes for sensors
'''

class SensorError(Exception):
    '''Exception baseclass for sensor errors'''
    pass

class NoSensorFoundError(SensorError):
    '''Exception when no sensor is found'''
    def __init__(self, sensorName):
        SensorError.__init__(self,
                             "No sensor with name '%s' found." % sensorName)

class UnexpectedSensorError(SensorError):
    '''Exception when unexpected error occurs'''
    def __init__(self, sensorName):
        sensorError.__init__(self,
                             '''Unexpected error occurs with sensor '%s'. The
                             sensor might not be ready to read.''' %
                             sensorName)


