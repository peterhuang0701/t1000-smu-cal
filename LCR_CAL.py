import socket
import sys
import time
import os
from LCR_ADC import ADCFunc
from LCR_FUN import Func
# from LCR_MUX import MuxFunc
from LCR_SRC import LCRSrc
import gvar


def FmtCurr(ma):
    # 依大小自動選單位顯示 (內部運算/EEPROM仍用mA)
    a = abs(ma)
    if a >= 1:
        return '{:.4f}mA'.format(ma)
    elif a >= 0.001:
        return '{:.4f}uA'.format(ma * 1000)
    else:
        return '{:.4f}nA'.format(ma * 1000000)


class CalFunc:
    def __init__(self,scpi):
        self.scpi=scpi
        self.ADC=ADCFunc()
        self.SubFunc=Func()
        self.SRC=LCRSrc()

    def DraLDcCal(self):
        print ('SRC1 1x Voltage Calibration Start.....\r\n')
        CalPoint=gvar.DraDcLCalPoint
        addrGain=gvar.DraDcLGainAddr
        addrOffset=gvar.DraDcLOffAddr
        volt_array=[]
        adc_array=[]
        # self.SubFunc.SetExPortRly('MP','ON')
        self.SubFunc.SelSrc('DCV')
        self.SubFunc.SelDr1Res('PASS')
        self.SubFunc.SetDr1OutRly('DR1MP','ON')
        self.scpi.gpibMv()
        self.scpi.gpibOn()
        for i in range(len(CalPoint)):
            self.SubFunc.SetDAC('CH1',CalPoint[i],CalPoint[i])
            adc_array.append(CalPoint[i])
            print ('SRC= {}'.format(CalPoint[i]))
            time.sleep(0.1)
            InsDmmV=self.scpi.gpibRead('volt')
            InsDmmV=float(InsDmmV)
            print('DMM = {}\r\n'.format(InsDmmV))
            volt_array.append(InsDmmV)
        cal_slope,cal_offset=self.SubFunc.SlopeOffset(adc_array,volt_array,1,0)
        self.SubFunc.WriteRom(addrGain,addrOffset,CalPoint,cal_slope,cal_offset)
        print ('SRC1 1x Voltage Calibration End.....\r\n')
    
        # print('SRC1 1x Voltage Calibration Check.....\r\n') #----
        # CalChkPoint=gvar.DraDcLChkPoint
        # for i in range(len(CalChkPoint)):
        #     self.SubFunc.SetDAC('CH1',CalChkPoint[i],CalChkPoint[i])
        #     print('SRC= {}'.format(CalChkPoint[i]))
        #     time.sleep(0.1)
        #     InsDmmV=self.scpi.gpibRead('volt')
        #     InsDmmV=float(InsDmmV)
        #     mvH=float(CalChkPoint[i])*1.0001+0.01
        #     mvL=float(CalChkPoint[i])*1.0001-0.01
        #     # print(mvL,mvH)
        #     if (mvL<InsDmmV<mvH):
        #         print('DMM = {} (PASS)\r\n'.format(InsDmmV))
        #     else:
        #         print('DMM = {} (FAIL)\r\n'.format(InsDmmV))
        #     time.sleep(0.1)         #-----
        self.scpi.gpibOff()
        self.SubFunc.SysARST()

    def DraHDcCal(self):
        print ('SRC1 5x Voltage Calibration Start.....\r\n')
        CalPoint=gvar.DraDcHCalPoint
        addrGain=gvar.DraDcHGainAddr
        addrOffset=gvar.DraDcHOffAddr
        volt_array=[]
        adc_array=[]
        # self.SubFunc.SetExPortRly('MP','ON')
        self.SubFunc.SelSrc('DCVx5')
        self.SubFunc.SelDr1Res('PASS')
        self.SubFunc.SetDr1OutRly('DR1MP','ON')
        self.scpi.gpibMv()
        self.scpi.gpibOn()
        for i in range(len(CalPoint)):
            self.SubFunc.SetDAC('CH1',CalPoint[i],CalPoint[i])
            adc_array.append(CalPoint[i])
            print ('SRC= {}'.format(CalPoint[i]))
            time.sleep(0.1)
            InsDmmV=self.scpi.gpibRead('volt')
            InsDmmV=float(InsDmmV)
            print('DMM = {}\r\n'.format(InsDmmV))
            volt_array.append(InsDmmV)
        cal_slope,cal_offset=self.SubFunc.SlopeOffset(adc_array,volt_array,1,0)
        self.SubFunc.WriteRom(addrGain,addrOffset,CalPoint,cal_slope,cal_offset)
        print ('SRC1 5x Voltage Calibration End.....\r\n')
        self.scpi.gpibOff()
        self.SubFunc.SysARST()

    def DrbCal(self):
        print ('SRC2 Voltage Calibration Start.....\r\n')
        CalPoint=gvar.DrbCalPoint
        addrGain=gvar.DrbGainAddr
        addrOffset=gvar.DrbOffAddr
        volt_array=[]
        adc_array=[]
        # self.SubFunc.SetExPortRly('MP','ON')
        self.SubFunc.SetDr2Rly('DCV','ON')
        self.SubFunc.SetDr2Rly('MP','ON')
        self.SubFunc.SetDr2Res('PASS')
        self.scpi.gpibMv()
        self.scpi.gpibOn()
        for i in range(len(CalPoint)):
            self.SubFunc.SetDAC('CH3',CalPoint[i],CalPoint[i])
            adc_array.append(CalPoint[i])
            print ('SRC= {}'.format(CalPoint[i]))
            time.sleep(0.1)
            InsDmmV=self.scpi.gpibRead('volt')
            InsDmmV=float(InsDmmV)
            print('DMM = {}\r\n'.format(InsDmmV))
            volt_array.append(InsDmmV)
        cal_slope,cal_offset=self.SubFunc.SlopeOffset(adc_array,volt_array,1,0)
        self.SubFunc.WriteRom(addrGain,addrOffset,CalPoint,cal_slope,cal_offset)
        print ('SRC2 Voltage Calibration End.....\r\n')
        self.scpi.gpibOff()
        self.SubFunc.SysARST()

    def CCSClampVCal(self):
        print ('CCS Clamp Voltage Calibration Start.....\r\n')
        CalPoint=gvar.CCSCvCalPoint
        addrGain=gvar.CCSCvGainAddr
        addrOffset=gvar.CCSCvOffAddr
        volt_array=[]
        adc_array=[]
        # self.SubFunc.SetExPortRly('MP','ON')
        self.SubFunc.SelSrc('DCVx5')
        self.SubFunc.SelDr1Res('1K')
        self.SubFunc.SetDr1OutRly('CCSEN','ON')
        self.SubFunc.SetDr1OutRly('CCSMP','ON')
        self.scpi.gpibMv()
        self.scpi.gpibOn()
        for i in range(len(CalPoint)):
            print ('CLAMPV = {}'.format(CalPoint[i]))
            self.SubFunc.SetDAC('CH4',CalPoint[i],CalPoint[i])
            adc_array.append(CalPoint[i])
            # print ('SRC= {}'.format(CalPoint[i]+1))
            self.SubFunc.SetDAC('CH1',CalPoint[i]+1,CalPoint[i]+1)
            time.sleep(0.1)
            InsDmmV=self.scpi.gpibRead('volt')
            InsDmmV=float(InsDmmV)
            print('DMM = {}\r\n'.format(InsDmmV))
            volt_array.append(InsDmmV)
        cal_slope,cal_offset=self.SubFunc.SlopeOffset(adc_array,volt_array,1,0)
        self.SubFunc.WriteRom(addrGain,addrOffset,CalPoint,cal_slope,cal_offset)
        self.SubFunc.SysARST()
        self.scpi.gpibOff()
        print ('CCS Clamp Voltage Calibration End.....\r\n')

    def CalRefV(self):
        print ('REF Voltage Calibration Start.....\r\n')
        self.SubFunc.SetMux5('p2V5R')
        self.SubFunc.SetDr1OutRly('CAL','ON')
        InsDmmV=float(self.scpi.gpibRead())
        print('DMM = {}\r\n'.format(InsDmmV))
        if 2.496<InsDmmV<2.502:
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.PP2V5RefAddr,InsDmmV))
        else:
            print('+2.5VREF Out Of Limit')

        # -2.5VREF 
        self.SubFunc.SetMux5('n2V5R')
        # self.SubFunc.SetDr1OutRly('CAL','ON')
        InsDmmV=float(self.scpi.gpibRead())
        print('DMM = {}\r\n'.format(InsDmmV))
        if -2.496>InsDmmV>-2.502:
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.PN2V5RefAddr,InsDmmV))
        else:
            print('-2.5VREF Out Of Limit')

    def CalMuxGain(self):
        self.scpi.gpibMv()
        self.scpi.gpibOn()
        calAddr=int(gvar.MUXGain2Addr,16)

        print ('MUX Calibration Start.....\r\n')
        self.SubFunc.SelSrc('DCV')
        self.SubFunc.SelDr1Res('PASS')
        self.SubFunc.SetMux1('DR1BUF')
        self.SubFunc.SetMux2('PASS')
        self.SubFunc.SetMux3('PASS')
        self.SubFunc.SetMux4('PASS')
        self.SubFunc.SetMux5('PASS')
        self.SubFunc.SetDAC('CH1',0.2,0.2)
        #self.SubFunc.SetDr1OutRly('CAL','ON')
        self.SubFunc.SetExPortRly('MP','ON')
        self.SubFunc.SetExPortRly('SP','ON')
        self.SubFunc.SetExPortRly('ADC1CAL','ON')

        src=float(self.scpi.gpibRead('volt'))
        # print('src=',src)
        # print('DMM GAIN1 = {}\r\n'.format(src))

        self.SubFunc.SetMux2('2X')
        src2x=float(self.scpi.gpibRead('volt'))
        #print('DMM GAIN2= {}\r\n'.format(src2x))

        self.SubFunc.SetMux2('4X')
        src4x=float(self.scpi.gpibRead('volt'))
        #print('DMM GAIN4= {}\r\n'.format(src4x))

        time.sleep(0.5) 

        self.SubFunc.SetMux2('12X')
        src12x=float(self.scpi.gpibRead('volt'))
        # print('DMM GAIN12= {}\r\n'.format(src12x))
        
        self.SubFunc.SetDAC('CH1',0.02,0.02)
        self.SubFunc.SetMux2('PASS')
        src002=float(self.scpi.gpibRead('volt'))
        # print('src002=',src002)
        # print('DMM GAIN1_002 = {}\r\n'.format(src002))

        time.sleep(0.5)

        self.SubFunc.SetMux2('36X')
        src36x=float(self.scpi.gpibRead('volt'))
        # print('DMM GAIN36= {}\r\n'.format(src36x))

        MuxG2 = src2x/src
        MuxG4 = src4x/src
        MuxG12 = src12x/src 
        MuxG36 = src36x/src002

        print('MuxG2={}'.format(MuxG2))
        print('MuxG4={}'.format(MuxG4))
        print('MuxG12={}'.format(MuxG12))
        print('MuxG36={}'.format(MuxG36))

        if 1.95 < MuxG2 < 2.05 :
            HexAddr = format(calAddr,'x')
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(HexAddr,MuxG2))
        else:
            print('Fail, MUX Gain2 Out of Range')

        if 3.95 < MuxG4 < 4.05 :
            HexAddr = format(calAddr+4,'x')
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(HexAddr,MuxG4))
        else:
            print('Fail, MUX Gain4 Out of Range')  

        if 11.93 < MuxG12 < 12.05 :
            HexAddr = format(calAddr+8,'x')
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(HexAddr,MuxG12))
        else:
            print('Fail, MUX Gain12 Out of Range')  

        if 34.5 < MuxG36 < 36.5 :
            HexAddr = format(calAddr+12,'x')
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(HexAddr,MuxG36))
        else:
            print('Fail, MUX Gain36 Out of Range')

        self.SubFunc.SelSrc('DCVx5')
        self.SubFunc.SetDAC('CH1',5,5)
        self.SubFunc.SetMux2('PASS')
        src=float(self.scpi.gpibRead('volt'))
        # print('DMM GAIN1 = {}\r\n'.format(src))

        self.SubFunc.SetMux2('0.2X')
        srcn02=float(self.scpi.gpibRead('volt'))
        # print('DMM GAIN1_n02 = {}\r\n'.format(srcn02))     

        self.SubFunc.SetMux2('PASS')
        self.SubFunc.SetMux5('-0.5X')
        srcn05=float(self.scpi.gpibRead('volt'))
        # print('DMM GAIN1_n02 = {}\r\n'.format(srcn05)) 

        MuxGn02 = srcn02/src 
        MuxGn05 = srcn05/src

        print('MuxGn02={}'.format(MuxGn02))
        print('MuxGn05={}'.format(MuxGn05))

        if -0.202 < MuxGn02 < -0.198 :
            HexAddr = format(calAddr+16,'x')
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(HexAddr,MuxGn02))
        else:
            print('Fail, MUX Gain02 Out of Range')

        if -0.502 < MuxGn05 < -0.498 :
            HexAddr = format(calAddr+20,'x')
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(HexAddr,MuxGn05))
        else:
            print('Fail, MUX MuxGn05 Out of Range')

        self.scpi.gpibOff()
        self.SubFunc.SysARST()


    def MuxOffsetCal(self):
        # MUX路徑offset校正: MUX1=AGND板內接地, 各增益組合讀ADC殘餘值存EEPROM
        # 不需2460/治具, 做法比照ATTPathOff
        print ('MUX Offset Calibration Start.....\r\n')
        combos = [
            ('PASS', 'PASS',  gvar.MuxOffPassAddr, 'MuxOffPass'),
            ('2X',   'PASS',  gvar.MuxOff2XAddr,   'MuxOff2X'  ),
            ('4X',   'PASS',  gvar.MuxOff4XAddr,   'MuxOff4X'  ),
            ('12X',  'PASS',  gvar.MuxOff12XAddr,  'MuxOff12X' ),
            ('36X',  'PASS',  gvar.MuxOff36XAddr,  'MuxOff36X' ),
            ('0.2X', 'PASS',  gvar.MuxOff02XAddr,  'MuxOff02X' ),
            ('PASS', '-0.5X', gvar.MuxOff05XAddr,  'MuxOff05X' ),
        ]
        self.SubFunc.SetMux1('AGND')
        self.SubFunc.SetMux3('PASS')
        self.SubFunc.SetMux4('PASS')
        for m2, m5, addr, name in combos:
            self.SubFunc.SetMux2(m2)
            self.SubFunc.SetMux5(m5)
            time.sleep(0.2)
            off=self.ADC.AdcMv(cnt=2500,type='DC',cal='Y')
            print ('{}={}'.format(name,off))
            if -0.01 < off < 0.01 :
                gvar.EthCmd('atk_eep_w_f_{}_{}'.format(addr,off))
            else:
                print('Fail, {} Out of Range'.format(name))
        self.SubFunc.SysARST()
        print ('MUX Offset Calibration End.....\r\n')

    def CCSCal(self):
        
        DictCCS={
            '100mA' : [ 3,    '10R'  ],
            '20mA'  : [ 4,    '100R' ],
            '10mA'  : [ 3,    '100R' ],
            '5mA'   : [ 2.5,  '100R' ],
            '2.5mA' : [ 2.25, '100R' ],
            '1mA'   : [ 3 ,   '1K'   ],
            '0.5mA' : [ 2.5,  '1K'   ],
            '0.25mA': [ 2.25, '1K'   ],
            '0.1mA' : [ 3,    '10K'  ],
            '50uA'  : [ 2.5,  '10K'  ],
            '25uA'  : [ 2.25, '10K'  ],
            '10uA'  : [ 3,    '100K' ],
            '5uA'   : [ 2.5,  '100K' ],
            '2.5uA' : [ 2.25, '100K' ],
            '1uA'   : [ 3,    '1M'   ],
            '0.1uA' : [ 2.1,  '1M'   ],
        }
        StrCCS=['100mA','20mA','10mA','5mA','2.5mA','1mA','0.5mA','0.25mA','0.1mA','50uA','25uA','10uA','5uA','2.5uA','1uA','0.1uA']
        self.scpi.gpibLSink()   # 先設定function再開output, 避免2460 Warning 5073
        self.scpi.gpibOn()
        self.SubFunc.SetDr1OutRly('CCSMP','ON')
        self.SRC.SetCCSClampV(2)
        self.SubFunc.SetDr1OutRly('CCSEN','ON')
        self.SubFunc.SelSrc('DCVx5')
        # self.SubFunc.SetExPortRly('MP','ON')

        CCs2WCalData=[]
        for i in range(len(StrCCS)):
            self.scpi.gpibOn()
            self.SRC.SetDraDcSrc(DictCCS[StrCCS[i]][0])
            self.SubFunc.SelDr1Res(DictCCS[StrCCS[i]][1])
            time.sleep(0.5)
            ccs=float(self.scpi.gpibRead('curr'))*1000   # 2460灌入方向讀值為負(慣例), 照原樣儲存
            CCs2WCalData.append(ccs)
            print('Setting Current={}'.format(StrCCS[i]))
            print('Measure Current={}\r\n'.format(FmtCurr(ccs)))

        calAddr=int(gvar.CCSCurr2WAddr,16)
        for i in range (len(CCs2WCalData)):
            HexAddr = format(calAddr,'x')
            print ('CCS Write Addr={}'.format(HexAddr))
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(HexAddr,CCs2WCalData[i]))
            print('Read From EEPROM={}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(HexAddr))))
            calAddr=calAddr+4
        self.scpi.gpibOff()
        self.scpi.gpibClose()
                
        # StrCCS=['100mA','20mA','10mA','5mA','2.5mA','1mA']
        # CCs4WCalData=[]
        # for i in range(len(StrCCS)):
        #     self.scpi.gpibOn()
        #     self.SRC.SetDraDcSrc(DictCCS[StrCCS[i]][0])
        #     self.SubFunc.SelDr1Res(DictCCS[StrCCS[i]][1])
        #     time.sleep(0.2)
        #     ccs=float(self.scpi.gpibRead('curr'))*-1000
        #     CCs4WCalData.append(ccs)
        #     print('Setting Current={}'.format(StrCCS[i]))
        #     print('Measure Currnet={}mA\r\n'.format(ccs))
        # self.scpi.gpibOff()
        # self.scpi.gpibClose()

        # calAddr=int(gvar.CCSCurr4WAddr,16)
        # for i in range (len(CCs4WCalData)):
        #     calAddr=calAddr+i*4
        #     HexAddr = format(calAddr,'x')
        #     gvar.EthCmd('atk_eep_w_f_{}_{}'.format(HexAddr,CCs4WCalData[i]))
        #     print('Read From EEPROM={}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(HexAddr))))

        self.SubFunc.SysARST()

    def ADC1Cal(self):
        # self.SubFunc.SysARST()
        MeterV=gvar.AdcCalPoint
        addrGain=gvar.AdcGainAddr
        addrOffset=gvar.AdcOffAddr
        volt_array=[]
        adc_array=[]
        # self.SubFunc.SetDr1OutRly('CAL','ON')
        # self.SubFunc.SetMux1('CAL_IN')
        # self.SubFunc.SetMux2('PASS')
        # self.SubFunc.SetMux3('PASS')
        # self.SubFunc.SetMux4('PASS')
        self.SubFunc.SetMux5('NC')
        self.SubFunc.SetExPortRly('MP','ON')
        self.SubFunc.SetExPortRly('SP','ON')
        self.SubFunc.SetExPortRly('ADC1CAL','ON')
        self.scpi.gpibDmm()
        self.scpi.gpibOn()
        # self.scpi.gpibSetV(1)
        ''
        for i in range(len(MeterV)):
            print('SetV     = {}'.format(MeterV[i]))
            self.scpi.gpibSetV(MeterV[i])
            time.sleep(0.1)
            readMeter=float(self.scpi.gpibRead('volt'))
            print('Meter MV = {}'.format(readMeter))
            readMeter=float(readMeter)
            volt_array.append(readMeter)
            adcv=self.ADC.ADC(1000,'DC')
            adc_array.append(adcv)
            print ('ADC MV   = {}\r\n'.format(adcv))
            time.sleep(0.1) 
        self.scpi.gpibOff()
        cal_slope,cal_offset=self.SubFunc.SlopeOffset(volt_array,adc_array,1,0)
        self.SubFunc.WriteRom(addrGain,addrOffset,MeterV,cal_slope,cal_offset)
        print('ADC Calibration End.....\r\n')

        print('ADC Calibration Check.....\r\n') #----
        self.SubFunc.SetMux5('NC')
        self.SubFunc.SetExPortRly('ADC1CAL','ON')
        self.scpi.gpibDmm()
        self.scpi.gpibOn()
        MeterChkV=gvar.AdcChkPoint
        for i in range(len(MeterChkV)):
            print('SetV     = {}'.format(MeterChkV[i]))
            self.scpi.gpibSetV(MeterChkV[i])
            time.sleep(0.1)
            readMeter=float(self.scpi.gpibRead('volt'))
            print('Meter MV = {}'.format(readMeter))
            # readMeter=float(readMeter)
            adcv=self.ADC.ADC(1000,'DC')
            CalV=self.SubFunc.FindGainOffset(adcv,MeterV,cal_slope,cal_offset)
            mvH=float(MeterChkV[i])*1.0001+0.1
            mvL=float(MeterChkV[i])*1.0001-0.1
            # print(mvL,mvH)
            if (mvL<adcv<mvH):
                print ('ADC MV   = {} (PASS)\r\n'.format(CalV))
            else:
                print ('ADC MV   = {} (FAIL)\r\n'.format(CalV))
            # print ('ADC MV   = {}\r\n'.format(adcv))
            time.sleep(0.1)         #-----

        self.scpi.gpibOff()   # 驗證結束關閉output, 避免下一步改function時跳Warning 5073
        self.SubFunc.SysARST()
        

    def UpScann(self,amp,acv,freq):
        ACMeter=acv
        ACVAmp=amp
        limit1 = 0.07
        limit2 = 0.0708

        for i in range (100):
            if ACMeter>limit1:  
                ACVAmp=ACVAmp+0.001
            elif ACMeter>limit2:  
                ACVAmp=ACVAmp+0.0001
            else:
                ACVAmp=ACVAmp-0.0001
                break
            print('ACVAmp={}'.format(ACVAmp))
            DACB= (ACVAmp-1.72)/1.72
            self.SubFunc.SetDAC('CH2',DACB,DACB)
            ACMeter=self.scpi.gpibRead()
            print('AC Meter={}'.format(ACMeter))
            time.sleep(0.1) 
           
        DACB= (ACVAmp-1.72)/1.72
        self.SubFunc.SetDAC('CH2',DACB,DACB)
        ACMeter=self.scpi.gpibRead()
        print('AC Meter={}'.format(ACMeter))
        return ACVAmp

    def DownScann(self,amp,acv,freq):
        ACMeter=acv
        ACVAmp=amp
        limit1 = 0.0707
        limit2 = 0.0706

        for i in range (100):
            if ACMeter>limit1:  
                ACVAmp=ACVAmp-0.0005
            elif ACMeter>limit2:  
                ACVAmp=ACVAmp-0.00001
            else:
                if ACVAmp<limit2:
                    ACVAmp=ACVAmp+0.00001
                break
            print('ACVAmp={}'.format(ACVAmp))
            DACB= (ACVAmp-1.72)/1.72
            self.SubFunc.SetDAC('CH2',DACB,DACB)
            ACMeter=self.scpi.gpibRead()
            print('AC Meter={}'.format(ACMeter))
            time.sleep(0.1) 
           
        DACB= (ACVAmp-1.72)/1.72
        self.SubFunc.SetDAC('CH2',DACB,DACB)
        ACMeter=self.scpi.gpibRead()
        print('AC Meter={}'.format(ACMeter))
        return ACMeter
 
    def FindRealVp(self,freq,period):
        ACVAmp=0.08
        self.scpi.gpibConfig('AC')
        self.SubFunc.SetDDS(freq,ACVAmp)

        ACMeter=self.scpi.gpibRead()
        print('AC Meter={}'.format(ACMeter))

        if ACMeter >= 0.0708:
            print('Down Scanning....')
            acvamp=self.DownScann(ACVAmp,ACMeter,freq)
        elif ACMeter <= 0.0706:
            print('Up Scanning....')
            acvamp=self.UpScann(ACVAmp,ACMeter,freq)

        samplecnt=(2500000/freq)*period

        adc1rms=self.ADC.AdcMv(samplecnt,'AC','N')
        print ('ADC[RMS]={}V'.format(adc1rms))
        return acvamp,adc1rms

    def ACVCal(self):
        # ACVAmp=0.1    
        self.SubFunc.SetDr1OutRly('DR1MP','ON')
        self.SubFunc.SelDr1Res('PASS')
        self.SubFunc.SelSrc('SRC')
        self.SubFunc.SetDAC2(0.25)

        self.SubFunc.SetMux1('DR1BUF')
        self.SubFunc.SetMux2('PASS')
        self.SubFunc.SetMux3('PASS')
        self.SubFunc.SetMux4('PASS')
        self.SubFunc.SetMux5('PASS')

        freq=100
        period=2
        print('Search 100HZ AC AMP........')
        RealVp,ADC1Rms=self.FindRealVp(freq,period)
        print ('RealVp={}'.format(RealVp))
        print ('ADC1Rms={}'.format(ADC1Rms))
        gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.SrcAcAmp100HZ,RealVp))
        gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.AdcAcAmp100HZ,ADC1Rms))
        print('Read From EEPROM : RealVp  = {}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.SrcAcAmp100HZ))))
        print('Read From EEPROM : ADC1Rms = {}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.AdcAcAmp100HZ))))


        freq=1000
        period=10
        print('Search 1KHZ AC AMP........')
        RealVp,ADC1Rms=self.FindRealVp(freq,period)
        print ('RealVp={}'.format(RealVp))
        print ('ADC1Rms={}'.format(ADC1Rms))
        gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.SrcAcAmp1KHZ,RealVp))
        gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.AdcAcAmp1KHZ,ADC1Rms))
        print('Read From EEPROM : RealVp  = {}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.SrcAcAmp1KHZ))))
        print('Read From EEPROM : ADC1Rms = {}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.AdcAcAmp1KHZ))))

        freq=10000
        period=100
        print('Search 10KHZ AC AMP........')
        RealVp,ADC1Rms=self.FindRealVp(freq,period)
        print ('RealVp={}'.format(RealVp))
        print ('ADC1Rms={}'.format(ADC1Rms))
        gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.SrcAcAmp10KHZ,RealVp))
        gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.AdcAcAmp10KHZ,ADC1Rms))
        print('Read From EEPROM : RealVp  = {}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.SrcAcAmp10KHZ))))
        print('Read From EEPROM : ADC1Rms = {}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.AdcAcAmp10KHZ))))

        freq=100000
        period=100
        print('Search 100KHZ AC AMP........')
        RealVp,ADC1Rms=self.FindRealVp(freq,period)
        print ('RealVp={}'.format(RealVp))
        print ('ADC1Rms={}'.format(ADC1Rms))
        gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.SrcAcAmp100KHZ,RealVp))
        gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.AdcAcAmp100KHZ,ADC1Rms))
        print('Read From EEPROM : RealVp  = {}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.SrcAcAmp100KHZ))))
        print('Read From EEPROM : ADC1Rms = {}'.format(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.AdcAcAmp100KHZ))))


    def ATTPathCal(self):
        # ATT路徑分段gain/offset校正: 2460當源打進MS/SS, 經ATT(D5/D10)+MUX5(-0.5X)由ADC讀
        # ADC讀值先乘標稱倍率回到輸入電壓尺度, 與2460回讀真值做SlopeOffset
        PathList=[
            ('D5',  gvar.ATT_HP_D5,  gvar.ATT_LP_D5,  gvar.ATTD5Nom,
             gvar.ATTD5PGainAddr,  gvar.ATTD5POffAddr),
            ('D10', gvar.ATT_HP_D10, gvar.ATT_LP_D10, gvar.ATTD10Nom,
             gvar.ATTD10PGainAddr, gvar.ATTD10POffAddr),
            ('PASS', gvar.ATT_HP_1X, gvar.ATT_LP_1X, gvar.ATTPassNom,
             gvar.ATTPassPGainAddr, gvar.ATTPassPOffAddr),
        ]
        for name,hp,lp,nom,addrG,addrO in PathList:
            print('ATT {} Path Calibration Start.....\r\n'.format(name))
            self.SubFunc.SetExPortRly('MS','ON')
            self.SubFunc.SetExPortRly('SS','ON')
            self.SubFunc.SetExPortRly('ADC1CAL','OFF')
            self.SubFunc.SetAtt1Rly('ALL','OFF')
            ATTPATH = gvar.ATT_HP_MS | hp | gvar.ATT_LP_SS | lp
            self.SubFunc.SetATT(ATTPATH)
            MUXPATH = gvar.MUX1_ATT | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_NG05
            self.SubFunc.SetMUX(MUXPATH)

            self.scpi.gpibDmm()
            self.scpi.gpibOn()
            volt_array=[]
            adc_array=[]
            for v in gvar.ATTCalPoint:
                print('SetV     = {}'.format(v))
                self.scpi.gpibSetV(v)
                time.sleep(0.2)
                meter=float(self.scpi.gpibRead('volt'))
                print('Meter MV = {}'.format(meter))
                volt_array.append(meter)
                adcv=self.ADC.AdcMv(cnt=2500,type='DC',cal='Y')*nom
                adc_array.append(adcv)
                print('ADC MV   = {}\r\n'.format(adcv))
            cal_slope,cal_offset=self.SubFunc.SlopeOffset(volt_array,adc_array,1,0)
            self.SubFunc.WriteRom(addrG,addrO,gvar.ATTCalPoint,cal_slope,cal_offset)
            print('ATT {} Path Calibration Check.....\r\n'.format(name))
            for v in gvar.ATTChkPoint:
                print('SetV     = {}'.format(v))
                self.scpi.gpibSetV(v)
                time.sleep(0.2)
                meter=float(self.scpi.gpibRead('volt'))
                print('Meter MV = {}'.format(meter))
                adcv=self.ADC.AdcMv(cnt=2500,type='DC',cal='Y')*nom
                CalV=self.SubFunc.FindGainOffset(adcv,gvar.ATTCalPoint,cal_slope,cal_offset)
                mvH=meter+abs(meter)*0.005+0.02
                mvL=meter-abs(meter)*0.005-0.02
                if (mvL<CalV<mvH):
                    print('ADC MV   = {} (PASS)\r\n'.format(CalV))
                else:
                    print('ADC MV   = {} (FAIL)\r\n'.format(CalV))
            self.scpi.gpibOff()
            print('ATT {} Path Calibration End.....\r\n'.format(name))
        self.SubFunc.SysARST()

    def ATTGainCal(self):
        self.scpi.gpibMv()
        self.scpi.gpibOn()
        self.SubFunc.SelSrc('GND')
        self.SRC.SetDraDcSrc(5)
        self.SubFunc.SelDr1Res('PASS')
        self.SubFunc.SelSrc('DCVx5')
        self.SubFunc.SetDr1OutRly('DR1MP','ON')
        self.SubFunc.SetDr1OutRly('GNDSP','ON')
        self.SubFunc.SetExPortRly('MP','ON')

        src=float(self.scpi.gpibRead('volt'))
        print('DMM1= {}\r'.format(src))

        MUXPATH = gvar.MUX1_BUF | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_NG05
        self.SubFunc.SetMUX(MUXPATH)
        src=self.ADC.AdcMv(cnt=2500,type='DC',cal='Y')
        # print(self.ADC.AdcMv(cnt=2500,type='DC',cal='Y'))
        src=src/gvar.MUXG05
        # print('MUXG05=',gvar.MUXG05)
        # print('src=',src,'\r\n')



        self.SRC.SetDraDcSrc(0)
        # self.SubFunc.SetExPortRly('MP','OFF')
        self.SubFunc.SetExPortRly('MS','ON')
        self.SubFunc.SetExPortRly('SS','ON')
        self.SubFunc.SetExPortRly('ADC1CAL','OFF')



        ATTPATH = gvar.ATT_HP_MS | gvar.ATT_HP_D5 | gvar.ATT_LP_SS | gvar.ATT_LP_D5
        self.SubFunc.SetATT(ATTPATH)
        MUXPATH = gvar.MUX1_ATT | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_NG05
        self.SubFunc.SetMUX(MUXPATH)
        self.SRC.SetDraDcSrc(5)

        att_v=self.ADC.AdcMv(cnt=2500,type='DC',cal='Y')
        # print(self.ADC.AdcMv(cnt=2500,type='DC',cal='Y'))
        att_v=att_v/gvar.MUXG05
        # print('MUXG05=',gvar.MUXG05)
        # print('att_v=',att_v)

        time.sleep(0.1)

        print('DMM2= {}\r\n'.format(att_v))
        

        ATTD05Gain = abs(att_v/src)

        print ('ATTD05Gain={}'.format(ATTD05Gain))

        self.SRC.SetDraDcSrc(0)

        self.SubFunc.SetAtt1Rly('ALL','OFF')

        ATTPATH = gvar.ATT_HP_MS | gvar.ATT_HP_D10 | gvar.ATT_LP_SS | gvar.ATT_LP_D10
        self.SubFunc.SetATT(ATTPATH)

        self.SRC.SetDraDcSrc(5)

        att_v=self.ADC.AdcMv(cnt=2500,type='DC',cal='Y')
        att_v=att_v/gvar.MUXG05


        ATTD10Gain = abs(att_v / src)

        print ('ATTD10Gain={}'.format(ATTD10Gain))

        # ExtMv路徑offset校正: 輸入接GND, 量ATT D10+MUX5(-0.5X)路徑的殘餘值(ADC端)
        self.SRC.SetDraDcSrc(0)
        self.SubFunc.SelSrc('GND')
        time.sleep(0.2)
        att_off=self.ADC.AdcMv(cnt=2500,type='DC',cal='Y')
        print ('ATTPathOff={}'.format(att_off))
        if -0.01 < att_off < 0.01 :
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.ATTPathOffAddr,att_off))
        else:
            print('Fail, ATT Path Offset Out of Range')

        if 0.198 < ATTD05Gain < 0.202 :
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.ATTD5Addr,ATTD05Gain))
        else:
            print('Fail,ATT Gain 1/5 Out of Range')

        if 0.098 < ATTD10Gain < 0.102 :
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.ATTD10Addr,ATTD10Gain))
        else:
            print('Fail, ATT Gain 1/10 Out of Range')

        self.scpi.gpibOff()
        self.SubFunc.SysARST()