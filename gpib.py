import pyvisa
import time

class GPIB():
    def __init__(self,name):
        self.__rm=pyvisa.ResourceManager()
        self.gpib=self.__rm.open_resource(name)
    def gpibDmm(self):  # for dmm calibration
        self.gpib.write(':SOUR:FUNC VOLT')
        self.gpib.write(':SOUR:VOLT:MODE FIXED')
        self.gpib.write(':SOUR:CURR:RANG MIN')
        self.gpib.write(':SOUR:CURR:LEV -0.0')
        self.gpib.write(':SENS:FUNC "CURR"')
        #gpib.write(':SENS:VOLT:PROT 6')
        self.gpib.write(':SENS:CURR:PROT 0.01')
        self.gpib.write(':SENS:CURR:RANG 10E-3')
        #gpib.write(':SOUR:CURR:RANG 0.5')
        self.gpib.write(':SENS:CURR:RANG:AUTO ON')
        #gpib.write(':SENS:VOLT:RANG:AUTO ON')

    def gpibLSink(self):
        self.gpib.write(':SOUR:FUNC VOLT')
        self.gpib.write(':SOUR:VOLT:MODE FIXED')
        self.gpib.write(':SOUR:CURR:RANG 1')
        self.gpib.write(':SENS:FUNC "CURR"') 
        self.gpib.write(':SENS:CURR:PROT 1')

    def gpibSink(self):
        self.gpib.write(':SOUR:FUNC VOLT')
        self.gpib.write(':SOUR:VOLT:MODE FIXED')
        self.gpib.write(':SOUR:CURR:RANG 5')
        self.gpib.write(':SENS:FUNC "CURR"') 
        self.gpib.write(':SENS:CURR:PROT 5')
        self.gpib.write(':SENS:CURR:RANG:AUTO ON')

    def gpibDmmHV(self):  # for dmm calibration
        self.gpib.write(':SOUR:FUNC VOLT')
        self.gpib.write(':SOUR:VOLT:MODE FIXED')
        self.gpib.write(':SOUR:CURR:RANG MIN')
        self.gpib.write(':SOUR:CURR:LEV -0.0')
        self.gpib.write(':SENS:FUNC "CURR"')
        #gpib.write(':SENS:VOLT:PROT 20')
        self.gpib.write(':SENS:CURR:PROT 0.01')
        self.gpib.write(':SENS:CURR:RANG 10E-3')
        #gpib.write(':SENS:CURR:RANG:AUTO ON')
        #gpib.write(':SENS:VOLT:RANG 6')
        self.gpib.write(':SENS:VOLT:RANG:AUTO ON')
        
    def gpibMv(self):   # for charger and battery calibration
        self.gpib.write(':SOUR:FUNC CURR') 
        self.gpib.write(':SOUR:CURR:MODE FIXED') 
        self.gpib.write(':SOUR:CURR:RANG MIN')
        self.gpib.write(':SOUR:CURR:LEV -0.0')	  
        self.gpib.write(':SENS:FUNC "VOLT"')  
        self.gpib.write(':SENS:VOLT:PROT 12') 
        self.gpib.write(':SENS:VOLT:RANG 12') 
        self.gpib.write(':SENS:VOLT:RANG:AUTO ON') 

    def gpibMvHv(self):   # for charger and battery calibration
        self.gpib.write(':SOUR:FUNC CURR') 
        self.gpib.write(':SOUR:CURR:MODE FIXED') 
        self.gpib.write(':SOUR:CURR:RANG MIN')
        self.gpib.write(':SOUR:CURR:LEV -0.0')	  
        self.gpib.write(':SENS:FUNC "VOLT"')  
        self.gpib.write(':SENS:VOLT:PROT 24') 
        self.gpib.write(':SENS:VOLT:RANG 24') 
        self.gpib.write(':SENS:VOLT:RANG:AUTO ON') 

    def gpibMi(self,comp):	# for batt, charger current calibration
        self.gpib.write(':SOUR:FUNC:MODE CURR') # Select source function
        self.gpib.write(':SOUR:CURR:MODE FIXED')  # Select fixed sourcing mode for V-source
        self.gpib.write(':SENS:FUNC "CURR"')	   # Select measure function 
        self.gpib.write(':SENS:CURR:PROT %s' %comp)   # Set voltage compliance <clamp i>
        self.gpib.write(':SENS:CURR:RANG:AUTO ON') # Set voltage measure range

    def gpibCCS(self,range):
        self.gpib.write(':SOUR:FUNC:MODE CURR') # Select source function
        self.gpib.write(':SOUR:CURR:MODE FIX')  # Select fixed sourcing mode for V-source
        self.gpib.write(':SOUR:CURR:RANGE %s' %range)	   # Select measure function 
        self.gpib.write(':SOUR:CURR:LEV -0.0')   # Set voltage compliance <clamp v>
        self.gpib.write(':SENS:VOLT:PROT 0.1') # Set voltage measure range
        self.gpib.write(':SOUR:VOLT:RANGE 0.1')
        self.gpib.write(':SENS:FUNC "CURR"')
        self.gpib.write(':SENS:CURR:PROT 0.01')
        self.gpib.write(':SENS:CURR:RANGE:AUTO ON')

    def gpibSetV(self,volt):
        self.gpib.write(f':SOUR:VOLT:RANG {volt}') # Select V-source range
        self.gpib.write(f':SOUR:VOLT:LEV {volt}')  # Set V-source amplitude

    def gpibSetI(self,curr):
        self.gpib.write(':SOUR:CURR:RANG {}'.format(curr)) # Select V-source range
        self.gpib.write(':SOUR:CURR:LEV {}'.format(curr))  # Set V-source amplitude
    
    def gpibSetPLC(self,plc):
        self.gpib.write(':SENS:CURR:NPLC',plc) # Select PLC range
        gpib_voltage = self.gpib.write(':SENS:CURR:NPLC?') # Read PLC range
        return gpib_voltage

    def gpibOCPI(self,curr):
        self.gpib.write(':SOUR:CURR:LEV {}'.format(curr))  # Set V-source amplitude

    def gpibOn(self):
        self.gpib.write(':OUTP ON')

    def gpibOff(self):
        self.gpib.write(':OUTP OFF')
        self.gpib.write('*RST')

    def gpibClose(self):
        self.gpib.close()
    
    def gpibRead(self,type):
        self.gpib.write(':READ?')
        gpib_read=self.gpib.read()
        time.sleep(0.1)
        if type=='volt' :
            gpib_voltage=gpib_read.split(',')[0]
        elif type == 'curr':
            gpib_voltage=gpib_read.split(',')[1]
        else:
            raise Exception("Input string should be volt or curr")
        return gpib_voltage
    
    def gpibCmd(self,cmd):
        self.gpib.write(cmd)
  

