import pyvisa
import time


class GPIB():
    def __init__(self,name):
        try:
            self.__rm=pyvisa.ResourceManager()      # NI/Keysight VISA
        except Exception:
            self.__rm=pyvisa.ResourceManager('@py') # 沒裝VISA時退回pyvisa-py
        self.gpib=self.__rm.open_resource(name)
        if name.upper().endswith('SOCKET'):         # raw socket需要指定終止字元
            self.gpib.read_termination='\n'
            self.gpib.write_termination='\n'
        
    def gpibDmm(self):  # for dmm calibration
        self.gpib.write(':VOLT:RANG:AUTO ON;')
        self.gpib.write(':CURR:RANG:AUTO ON;')
        self.gpib.write(':SOUR:FUNC VOLT')
        self.gpib.write(':SOUR:VOLT 0.0;')
        self.gpib.write(':SOUR:VOLT:ILIM 0.1;')
        self.gpib.write(':FUNC "VOLT"')
        self.gpib.write(':SOUR:VOLT:PROT PROT10')

    def gpibLSink(self):

        self.gpib.write(':VOLT:RANG:AUTO ON;')
        self.gpib.write(':SOUR:VOLT:RANG 7.0;')
        self.gpib.write(':CURR:RANG:AUTO ON;')
        self.gpib.write(':SOUR:FUNC VOLT')
        self.gpib.write(':SOUR:VOLT 0.0;')
        self.gpib.write(':SOUR:VOLT:ILIM 0.2;')
        self.gpib.write(':FUNC "CURR"')
        self.gpib.write(':SOUR:VOLT:PROT PROT5')
    def gpibSink(self):
        # gpib.write(':SOUR:FUNC VOLT')
        # gpib.write(':SOUR:VOLT:MODE FIXED')
        # gpib.write(':SOUR:CURR:RANG 5')
        # gpib.write(':SENS:FUNC "CURR"') 
        # gpib.write(':SENS:CURR:PROT 5')
        # gpib.write(':SENS:CURR:RANG:AUTO ON')

        self.gpib.write(':VOLT:RANG:AUTO ON;')
        self.gpib.write(':CURR:RANG 5.00;')
        self.gpib.write(':SOUR:FUNC VOLT')
        self.gpib.write(':SOUR:VOLT 0.0;')
        self.gpib.write(':SOUR:VOLT:ILIM 5.00;')
        self.gpib.write(':FUNC "CURR"')
        self.gpib.write(':SOUR:VOLT:PROT PROT5')

    def gpibDmmHV(self):  # for dmm calibration
        self.gpib.write(':VOLT:RANG:AUTO ON;')
        self.gpib.write(':CURR:RANG:AUTO ON;')
        self.gpib.write(':SOUR:FUNC VOLT')
        self.gpib.write(':SOUR:VOLT 0.0;')
        self.gpib.write(':SOUR:VOLT:ILIM 0.1;')
        self.gpib.write(':FUNC "VOLT"')
        self.gpib.write(':SOUR:VOLT:PROT PROT40')
        
    def gpibMv(self):   # for charger and battery calibration

        self.gpib.write(':VOLT:RANG:AUTO ON;')
        self.gpib.write(':CURR:RANG:AUTO ON;')
        self.gpib.write(':SOUR:FUNC CURR')
        self.gpib.write(':SOUR:CURR 0.0;')
        self.gpib.write(':SOUR:CURR:VLIM 12.0;')
        self.gpib.write(':FUNC "VOLT"')
        self.gpib.write(':SOUR:VOLT:PROT PROT10') 

    def gpibMvHv(self):   # for charger and battery calibration
        
        self.gpib.write(':VOLT:RANG:AUTO ON;')
        self.gpib.write(':CURR:RANG:AUTO ON;')
        self.gpib.write(':SOUR:FUNC CURR')
        self.gpib.write(':SOUR:CURR 0.0;')
        self.gpib.write(':SOUR:CURR:VLIM 21.0;')
        self.gpib.write(':FUNC "VOLT"')
        self.gpib.write(':SOUR:VOLT:PROT PROT40')  

    def gpibMi(self,comp):	# for batt, charger current calibration
      # gpib.write(':SOUR:FUNC:MODE CURR') # Select source function
      # gpib.write(':SOUR:CURR:MODE FIXED')  # Select fixed sourcing mode for V-source
      # gpib.write(':SENS:FUNC "CURR"')	   # Select measure function 
      # gpib.write(':SENS:CURR:PROT %s' %comp)   # Set voltage compliance <clamp i>
      # gpib.write(':SENS:CURR:RANG:AUTO ON') # Set voltage measure range
      
        self.gpib.write(':VOLT:RANG:AUTO ON;')
        self.gpib.write(':CURR:RANG:AUTO ON;')
        self.gpib.write(':SOUR:FUNC CURR')
        self.gpib.write(':SOUR:CURR 0.0;')
        self.gpib.write(':SOUR:CURR:VLIM 7.00;')
        self.gpib.write(':FUNC "CURR"')
        self.gpib.write(':SOUR:VOLT:PROT PROT10')


    def gpibCCS(self,range):
      # gpib.write(':SOUR:FUNC:MODE CURR') # Select source function
      # gpib.write(':SOUR:CURR:RANGE %s' %range)	   # Select measure function 
      # gpib.write(':SOUR:CURR:LEV -0.0')   # Set voltage compliance <clamp v>
      # gpib.write(':SENS:VOLT:PROT 0.1') # Set voltage measure range
      # gpib.write(':SOUR:VOLT:RANGE 0.1')
      # gpib.write(':SENS:FUNC "CURR"')
      # gpib.write(':SENS:CURR:PROT 0.01')
      # gpib.write(':SENS:CURR:RANGE:AUTO ON')

        self.gpib.write(':VOLT:RANG:AUTO ON;')
        self.gpib.write(':CURR:RANG:AUTO ON;')
        self.gpib.write(':SOUR:FUNC CURR')
        self.gpib.write(':SOUR:CURR %s;' %range)
        self.gpib.write(':SOUR:CURR:VLIM 0.1;')
        self.gpib.write(':FUNC "CURR"')
        self.gpib.write(':SOUR:VOLT:PROT PROT2')

    def gpibSetV(self,volt):
      # gpib.write(':SOUR:VOLT:RANG {}'.format(volt)) # Select V-source range
        self.gpib.write(':SOUR:VOLT {};'.format(volt))  # Set V-source amplitude

    def gpibSetI(self,curr):
      # gpib.write(':SOUR:CURR:RANG {};'.format(curr)) # Select V-source range
        self.gpib.write(':SOUR:CURR {};'.format(curr))  # Set V-source amplitude
    
    def gpibSetPLC(self,plc):
        self.gpib.write(':SENS:CURR:NPLC',plc) # Select PLC range
        gpib_voltage = self.gpib.write(':SENS:CURR:NPLC?') # Read PLC range
        return gpib_voltage

    def gpibOCPI(self,curr):
        self.gpib.write(':SOUR:CURR {};'.format(curr))  # Set V-source amplitude

    def gpibOn(self):
        self.gpib.write(':OUTP ON;')

    def gpibOff(self):
        self.gpib.write(':OUTP OFF;')
        #self.gpib.write('*RST')

    def gpibClose(self):
        self.gpib.close()
    
    def gpibRead(self,type):  
        # print('2460 wr Response={}'.format(self.gpib.write(':READ? "defbuffer1", READ')))
        self.gpib.write(':READ? "defbuffer1", READ')
        gpib_read=self.gpib.read()
        # print('2460 rd Response={}'.format(gpib_read))
        time.sleep(0.1)
        if type=='volt' :
          gpib_voltage=gpib_read.split(',')[0]
        elif type == 'curr':
          gpib_voltage=gpib_read.split(',')[0]
        else:
          raise Exception("Input string should be volt or curr")
        return gpib_voltage
    
    def gpibCmd(self,cmd):
        self.gpib.write(cmd)
    
'''
CMD EXAMPLE LIST

'*RST'                        Reset K2460
':OUTP ON;'                    Output ON
':OUTP OFF;'                   Output OFF
':VOLT:RANG:AUTO ON;'         Voltage measure range AUTO
':VOLT:RANG 1.000000;'        Voltage measure range FIXED 1V
':CURR:RANG:AUTO ON;'         Current measure range AUTO
':CURR:RANG 1.000000;'        Current measure range FIXED 1A
':RES:RANG:AUTO ON;'          Voltage measure range AUTO
':RES:RANG 1.000000;'         Voltage measure range FIXED 1ohm
':SOUR:VOLT 1.000000;'        Voltage source level 1V
':SOUR:VOLT:ILIM 2.000000;'   Voltage source current limit 2A
':SOUR:CURR 0.500000;'        Voltage source level 500mA
':SOUR:CURR:VLIM 2.500000;'   Voltage source current limit 2.5V
':SOUR:FUNC VOLT'             Source function voltage
':SOUR:FUNC CURR'             Source function current
':FUNC "VOLT"'                Measure function voltage
':FUNC "CURR"'                Measure function current
':FUNC "RES"'                 Measure function AUTO resistance
'SENSE:VOLT:UNIT OHM'         Measure function MANUAL resistance @source current
'SENSE:CURR:UNIT OHM'         Measure function MANUAL resistance @source voltage
':SOUR:FUNC?'                 Get Source function
':READ? "defbuffer1", READ'   Read measurement value
':VOLT:NPLC 1.0'              Set voltage read PLC range
':CURR:NPLC 1.0'              Set current read PLC range
':VOLT:RSEN ON;'              Remote sense ON
':VOLT:RSEN OFF;'              Remote sense OFF

'''
