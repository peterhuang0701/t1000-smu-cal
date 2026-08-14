import pyvisa
import time


class GPIB():
    def __init__(self,name):
        self.__rm=pyvisa.ResourceManager()
        self.gpib=self.__rm.open_resource(name)

    def gpibConfig(self,type='DC'):
        self.gpib.write(':MEAS:VOLT:{}?'.format(type))
        self.gpib.read()


    def gpibRead(self):
        self.gpib.write(':READ?')
        gpib_read=float(self.gpib.read())
        return gpib_read

    