import socket
import sys
import time
import os
import binascii
import math
from LCR_SRC import LCRSrc
from LCR_FUN import Func
from LCR_ADC import ADCFunc
import gvar

class Parts:
    def __init__(self):
        self.SRC=LCRSrc()
        self.SubFunc=Func()
        self.ADC=ADCFunc()

    def ResCCS2W(self,res,dly=0.1):
        self.SubFunc.SelSrc('GND')
        ATTPATH = gvar.ATT_HP_MS | gvar.ATT_HP_1M |gvar.ATT_HP_1X | gvar.ATT_LP_SS | gvar.ATT_LP_1M |gvar.ATT_LP_1X
        self.SubFunc.SetATT(ATTPATH)
        MUXPATH = gvar.MUX1_ATT | gvar.MUX2_G2 | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        Gain=gvar.MUXG2

        if 0< res <= 50 :
            I=self.SRC.SetCCS('20mA')
        elif 50 < res <= 100 :
            I=self.SRC.SetCCS('10mA')
        elif 100 < res <= 200 :
            I=self.SRC.SetCCS('5mA')
        elif 200 < res <= 500 :
            I=self.SRC.SetCCS('2.5mA')
        elif 500 < res <= 1000 :
            I=self.SRC.SetCCS('1mA')
        elif 1000 < res <= 2000 :
            I=self.SRC.SetCCS('0.5mA')
        elif 2000 < res <= 5000 :
            I=self.SRC.SetCCS('0.25mA')
        elif 5000 < res <= 10000 :
            I=self.SRC.SetCCS('0.1mA')
        elif 10000 < res <= 20000:
            I=self.SRC.SetCCS('0.05mA')
        elif 20000 < res <= 50000:
            I=self.SRC.SetCCS('0.025mA')
        elif 50000 < res <= 100000:
            I=self.SRC.SetCCS('0.01mA')
        elif 100000 < res <= 200000:
            I=self.SRC.SetCCS('0.005mA')
        elif 200000 < res <= 500000:
            I=self.SRC.SetCCS('0.0025mA')
        elif 500000 < res <= 1000000:
            I=self.SRC.SetCCS('0.001mA')
        else:
            I=self.SRC.SetCCS('0.0001mA')

        if res >10000 :
            Sampling = gvar.ADCSampling
        else:
            Sampling = 2500

        #Turn Power
        self.SubFunc.SelSrc('DCVx5')

        time.sleep(dly)
        MV=self.ADC.AdcMv(cnt=Sampling,type='DC',cal='Y')
        MV=MV-gvar.MUXOFF['2X']   # 先扣MUX路徑offset再除gain (範本: 路徑用哪個增益就查哪個key)

        print('MV={}'.format(MV))
        print('Curr={}'.format(I))
        print('Gain={}'.format(Gain))

        RES= abs((MV/I/Gain)*1000)
        # if RES < 50:
        #     RES *= 4
        print('Resistor={}'.format(RES))
        # if RES > 10:
        #     RES = 'PASS'
        # else:
        #     RES = 'FAIL'
        # Turn OFF Power 
        self.SubFunc.SelSrc('GND')
        self.SubFunc.SysARST()

        return RES

    def ExtMv(self):
        self.SubFunc.SetExPortRly('MS','ON')
        self.SubFunc.SetExPortRly('SS','ON')
        self.SubFunc.SetAtt1Rly('ALL','OFF')
        ATTPATH = gvar.ATT_HP_MS | gvar.ATT_HP_D10 | gvar.ATT_LP_SS | gvar.ATT_LP_D10
        self.SubFunc.SetATT(ATTPATH)
        MUXPATH = gvar.MUX1_ATT | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_NG05
        self.SubFunc.SetMUX(MUXPATH)

        time.sleep(0.1)

        #Measure Voltage
        Sampling=2500
        MV=self.ADC.AdcMv(cnt=Sampling,type='DC',cal='Y')

        #Diode Forward Voltage
        # print('MV={}'.format(MV))
        # print('muxg05={}'.format(gvar.MUXG05))
        # print('ATTG10={}'.format(gvar.ATTGD10))
        self.SubFunc.SetExPortRly('MS','OFF')
        self.SubFunc.SetExPortRly('SS','OFF')
        # ADC讀值乘標稱倍率回輸入尺度, 再查D10路徑分段gain/offset表
        RealMv = self.SubFunc.FindGainOffset(MV*gvar.ATTD10Nom,
                    gvar.ATTCalPoint, gvar.ATTD10PGain, gvar.ATTD10POffset)
        print('measure value=', RealMv,'V')
        return RealMv


    '''

    def ResCCS4W(self,res):
        self.SubFunc.SelSrc('GND')
        ATTPATH = gvar.ATT_HP_MS | gvar.ATT_HP_1M | gvar.ATT_LP_SS | gvar.ATT_LP_1M
        self.SubFunc.SetATT(ATTPATH)
        MUXPATH = gvar.MUX1_ATT | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)

        if 0 < res < 1 :
            I=self.SRC.SetCCS('100mA')
            self.SubFunc.SetMux2('36X')
            Gain=gvar.MUXG36
        elif 0< res <= 10 :
            I=self.SRC.SetCCS('20mA')
            self.SubFunc.SetMux2('12X')
            Gain=gvar.MUXG12
        elif 10 < res <= 50 :
            I=self.SRC.SetCCS('10mA')
            self.SubFunc.SetMux2('4X')
            Gain=gvar.MUXG4
        elif 50 < res <= 100 :
            I=self.SRC.SetCCS('5mA')
            self.SubFunc.SetMux2('4X')
            Gain=gvar.MUXG4
        elif 100 < res <= 500 :
            I=self.SRC.SetCCS('2.5mA')
            self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        else 500 < res <= 1000 :
            I=self.SRC.SetCCS('1mA')
            self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2

        Sampling=2500

        #Turn Power
        self.SubFunc.SelSrc('DCVx5')

        time.sleep(0.1)
        MV=self.ADC.AdcMv(cnt=Sampling,type='DC',cal='Y')
        RES= MV/I/Gain
        print('Resistor={}'.format(RES))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')
        self.SubFunc.SetATT(ATT_OFF)

        return RES

    def ResCVS2W(self,res):
        self.SubFunc.SelSrc('GND')
        MUXPATH = gvar.MUX1_MOAC | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SRC.SetDraDcSrc('0.2')

        if 0< res <= 10 :
            self.SubFunc.SelDr1Res('10R')
            MOAC='1N'
            MOAR=['10R',10]
            Sampling = 2500
            self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 10 < res <= 50 :
            self.SubFunc.SelDr1Res('PASS')
            MOAC='1N'
            MOAR=['10R',10]
            Sampling = 2500
            self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 50 < res <= 500 :
            self.SubFunc.SelDr1Res('PASS')
            MOAC='1N'
            MOAR=['100R',100]
            Sampling = 2500
            self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 500 < res <= 5000 :
            self.SubFunc.SelDr1Res('PASS')
            MOAC='1N'
            MOAR=['1K',1000]
            Sampling = 2500
            self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 5000 < res <= 50000 :
            self.SubFunc.SelDr1Res('PASS')
            MOAC='100P'
            MOAR=['10K',10000]
            Sampling = 2500
            self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 50000 < res <= 500000:
            self.SubFunc.SelDr1Res('PASS')
            MOAC='100P'
            MOAR=['100K',100000]
            Sampling = 41666
            self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 500000 < res <= 1000000:
            self.SubFunc.SelDr1Res('PASS')
            MOAC='8.2P'
            MOAR=['1M',1000000]
            Sampling = 41666
            self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 1000000 < res <= 5000000:
            self.SubFunc.SelDr1Res('PASS')
            MOAC='8.2P'
            MOAR=['1M',1000000]
            Sampling = 41666
            self.SubFunc.SetMux2('12X')
            Gain=gvar.MUXG12
        else:
            self.SubFunc.SelDr1Res('PASS')
            MOAC='8.2P'
            MOAR=['1M',1000000]
            Sampling = 41666
            self.SubFunc.SetMux2('36X')
            Gain=gvar.MUXG36

        if res >50000 :
            Sampling = gvar.ADCSampling
        else:
            Sampling = 2500

        #Turn The Power
        self.SubFunc.SelSrc('DCV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        MV=self.ADC.AdcMv(cnt=Sampling,type='DC',cal='Y')
        RES= 0.2/(MV/MOAR[1]/Gain)
        print('Resistor={}'.format(RES))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return resistor

    def ResCVS4W(self,res):
        self.SubFunc.SelSrc('GND')
        ATTPATH = gvar.ATT_HP_MS | gvar.ATT_HP_1M | gvar.ATT_LP_SS | gvar.ATT_LP_1M
        self.SubFunc.SetATT(ATTPATH)
        MUXPATH = gvar.MUX1_MOA | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SRC.SetDraDcSrc('0.2')

        if 0< res <= 10 :
            self.SubFunc.SelDr1Res('10R')
            MOAC='1N'
            MOAR=['10R',10]
            Sampling = 2500
            MUXGain= gvar.MUX2_G2
            # self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 10 < res <= 50 :
            self.SubFunc.SelDr1Res('PASS')
            MOAC='1N'
            MOAR=['10R',10]
            Sampling = 2500
            MUXGain= gvar.MUX2_G2
            # self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 50 < res <= 500 :
            self.SubFunc.SelDr1Res('PASS')
            MOAC='1N'
            MOAR=['100R',100]
            Sampling = 2500
            MUXGain= gvar.MUX2_G2
            # self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 500 < res <= 5000 :
            self.SubFunc.SelDr1Res('PASS')
            MOAC='1N'
            MOAR=['1K',1000]
            Sampling = 2500
            MUXGain= gvar.MUX2_G2
            # self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 5000 < res <= 50000 :
            self.SubFunc.SelDr1Res('PASS')
            MOAC='100P'
            MOAR=['10K',10000]
            Sampling = 2500
            MUXGain= gvar.MUX2_G2
            # self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 50000 < res <= 500000:
            self.SubFunc.SelDr1Res('PASS')
            MOAC='100P'
            MOAR=['100K',100000]
            Sampling = 41666
            MUXGain= gvar.MUX2_G2
            # self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 500000 < res <= 1000000:
            self.SubFunc.SelDr1Res('PASS')
            MOAC='8.2P'
            MOAR=['1M',1000000]
            Sampling = 41666
            MUXGain = gvar.MUX2_G2
            # self.SubFunc.SetMux2('2X')
            Gain=gvar.MUXG2
        elif 1000000 < res <= 5000000:
            self.SubFunc.SelDr1Res('PASS')
            MOAC='8.2P'
            MOAR=['1M',1000000]
            Sampling = 41666
            MUXGain = gvar.MUX2_G12
            # self.SubFunc.SetMux2('12X')
            Gain=gvar.MUXG12
        else:
            self.SubFunc.SelDr1Res('PASS')
            MOAC='8.2P'
            MOAR=['1M',1000000]
            Sampling = 41666
            MUXGain = gvar.MUX2_G36
            # self.SubFunc.SetMux2('36X')
            Gain=gvar.MUXG36

        if res >50000 :
            Sampling = gvar.ADCSampling
        else:
            Sampling = 2500

        #Turn ON Power
        self.SubFunc.SelSrc('DCV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        MOAv=float(self.ADC.AdcMv(cnt=Sampling,type='DC',cal='Y'))
        Curr=(MOAv/MOAR[1])

        MUXPATH = gvar.MUX1_ATT | MUXGain | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        ATTv=float(self.ADC.AdcMv(cnt=Sampling,type='DC',cal='Y'))/Gain

        RES = ATTv / Curr

        print('Resistor={}'.format(RES))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return RES

    def CapAC2W100HZ(self,cap):
        freq=100
        period=4
        #Trun Off Source
        self.SubFunc.SelSrc('GND')
        MUXPATH = gvar.MUX1_MOA | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SubFunc.SetDDS(100,gvar.SRCAMP100HZ)
        self.SubFunc.SelDr1Res('PASS')

        if 20000< cap <=1000000:
            MOAC='10N'
            MOAR=['10R',10]
            Sampling = 2500000*period/freq
        elif 2000< cap <= 20000:
            MOAC='10N'
            MOAR=['100R',100]
            Sampling = 2500000*period/freq
        elif 200 < cap <= 2000:
            MOAC='10N'
            MOAR=['1K',999.98]
            Sampling = 2500000*period/freq
        elif 20 < cap <= 200:
            MOAC='10N'
            MOAR=['10K',9980.34]
            Sampling = 2500000*period/freq
        else :
            period=10
            if gva.AC60HZ==1:
                freq=60
            else:
                freq=50
            MOAC='10N'
            MOAR=['100K',84685.45]
            Sampling = 2500000*period/freq

        #Turn ON Power
        self.SubFunc.SelSrc('ACV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        ADC_V=self.ADC.AdcMv(cnt=Sampling,type='AC',cal='N')

        MOAI=ADC_V/MOAR[1]
        ZC= gvar.ADCMAMP100HZ/MOAI
        CAP= (1/(2*3.14159*100*ZC))*pow(10,9)

        print('CAP={}nF'.format(CAP))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return CAP


    def CapAC2W1KHZ(self,cap):
        freq=1000
        period=10
        self.SubFunc.SelSrc('GND')
        MUXPATH = gvar.MUX1_MOA | gvar.MUX2_PASS | gvar.MUX3_FIR1K | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SubFunc.SetDDS(freq,gvar.SRCAMP1KHZ)
        self.SubFunc.SelDr1Res('PASS')

        if 5000< cap <=50000:
            MOAC='10N'
            MOAR=['10R',10]
            Sampling = 2500000*period/freq
        elif 500< cap <= 5000:
            MOAC='1N'
            MOAR=['100R',100]
            Sampling = 2500000*period/freq
        elif 50 < cap <= 500:
            MOAC='100P'
            MOAR=['1K',999.99]
            Sampling = 2500000*period/freq
        elif 5 < cap <= 50:
            MOAC='10P'
            MOAR=['10K',9999.993]
            Sampling = 2500000*period/freq
        else :
            period=10
            if gva.AC60HZ==1:
                freq=60
            else:
                freq=50
            MOAC='8.2P'
            MOAR=['100K',99998.672]
            Sampling = 2500000*period/freq

        #Turn ON Power
        self.SubFunc.SelSrc('ACV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        ADC_V=self.ADC.AdcMv(cnt=Sampling,type='AC',cal='N')

        MOAI=ADC_V/MOAR[1]
        ZC= gvar.ADCMAMP100HZ/MOAI
        CAP= (1/(2*3.14159*100*ZC))*pow(10,9)

        print('CAP={}nF'.format(CAP))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return CAP

    def CapAC2W10KHZ(self,cap):
        freq=10000
        period=10
        self.SubFunc.SelSrc('GND')
        MUXPATH = gvar.MUX1_MOA | gvar.MUX2_PASS | gvar.MUX3_FIR10K | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SubFunc.SetDDS(freq,gvar.SRCAMP1KHZ)
        self.SubFunc.SelDr1Res('PASS')

        if 500< cap <=5000:
            MOAC='10N'
            MOAR=['10R',10]
            Sampling = 2500000*period/freq
        elif 50< cap <= 500:
            MOAC='1N'
            MOAR=['100R',99.997]
            Sampling = 2500000*period/freq
        elif 5 < cap <= 50:
            MOAC='100P'
            MOAR=['1K',999.976]
            Sampling = 2500000*period/freq
        elif 0.5 < cap <= 5:
            MOAC='10P'
            MOAR=['10K',9999.346]
            Sampling = 2500000*period/freq
        else :
            period=10
            if gva.AC60HZ==1:
                freq=60
            else:
                freq=50
            MOAC='8.2P'
            MOAR=['100K',99867.537]
            Sampling = 2500000*period/freq

        #Turn ON Power
        self.SubFunc.SelSrc('ACV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        ADC_V=self.ADC.AdcMv(cnt=Sampling,type='AC',cal='N')

        MOAI=ADC_V/MOAR[1]
        ZC= gvar.ADCMAMP100HZ/MOAI
        CAP= (1/(2*3.14159*100*ZC))*pow(10,9)

        print('CAP={}nF'.format(CAP))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return CAP

    def CapAC2W100KHZ(self,cap):
        freq=100000
        period=100
        self.SubFunc.SelSrc('GND')
        MUXPATH = gvar.MUX1_MOA | gvar.MUX2_PASS | gvar.MUX3_FIR100K | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SubFunc.SetDDS(freq,gvar.SRCAMP1KHZ)
        self.SubFunc.SelDr1Res('PASS')

        if 50< cap <=100:
            MOAC='100P'
            MOAR=['10R',10]
            Sampling = 2500000*period/freq
        elif 5< cap <= 50:
            MOAC='10P'
            MOAR=['100R',99.997]
            Sampling = 2500000*period/freq
        elif 0.5 < cap <= 5:
            MOAC='10P'
            MOAR=['1K',999.976]
            Sampling = 2500000*period/freq
        elif 0.05 < cap <= 0.5:
            MOAC='8.2P'
            MOAR=['10K',9986.753]
            Sampling = 2500000*period/freq
        else :
            period=10
            if gva.AC60HZ==1:
                freq=60
            else:
                freq=50
            MOAC='8.2P'
            MOAR=['100K',8894.933]
            Sampling = 2500000*period/freq

        #Turn ON Power
        self.SubFunc.SelSrc('ACV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        ADC_V=self.ADC.AdcMv(cnt=Sampling,type='AC',cal='N')

        MOAI=ADC_V/MOAR[1]
        ZC= gvar.ADCMAMP100HZ/MOAI
        CAP= (1/(2*3.14159*100*ZC))*pow(10,9)

        print('CAP={}nF'.format(CAP))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return CAP

    def CCSCapMeasure(self,ccs_i,time_ms):
        # self.SubFunc.SetAtt1Rly('CCS')
        # self.SubFunc.SetMUX('CCS')

        DIS=self.SubFunc.Discharge()
        self.SubFunc.SetMUX('CCS')
        Len= 2500000/(time_ms*1000)
        if DIS=='PASS':
            I=self.SRC.SetCCS(ccs_i)
            DeltaV=self.ADC1(Len,'DELTA')
            self.SRC.SetCCS('0mA')
            self.SubFunc.Discharge()

            print ('DeltaV={}'.format(DeltaV))
            # Equation: C=I*Delta_T/Delta_V
            
            CAP = I*time_ms/DeltaV
            CAP = C * 1000
            print ('CAP={}uF'.format(CAP))
            
        return CAP

    def LAC2W100HZ(self,ind):
        freq=100
        period=4
        #Trun Off Source
        self.SubFunc.SelSrc('GND')
        MUXPATH = gvar.MUX1_MOA | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SubFunc.SetDDS(freq,gvar.SRCAMP100HZ)
        self.SubFunc.SelDr1Res('PASS')

        if 5000< ind <= 50000:
            MOAC='10N'
            MOAR=['10R',10]
            Sampling = 2500000*period/freq
        elif 50000< ind <= 500000:
            MOAC='10N'
            MOAR=['100R',100]
            Sampling = 2500000*period/freq
        elif 500000 < ind <= 5000000:
            MOAC='10N'
            MOAR=['1K',999.98]
            Sampling = 2500000*period/freq
        elif 5000000 < ind <= 50000000:
            MOAC='10N'
            MOAR=['10K',9980.34]
            Sampling = 2500000*period/freq
        else :
            period=10
            if gva.AC60HZ==1:
                freq=60
            else:
                freq=50
            MOAC='10N'
            MOAR=['100K',84685.45]
            Sampling = 2500000*period/freq

        #Turn ON Power
        self.SubFunc.SelSrc('ACV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        ADC_V=self.ADC.AdcMv(cnt=Sampling,type='AC',cal='N')

        MOAI=ADC_V/MOAR[1]
        ZL= gvar.ADCMAMP100HZ/MOAI
        IND= (2*3.14159*freq*ZL)*pow(10,6)

        print('IND={}uH'.format(IND))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return IND

    def LAC2W1KHZ(self,ind):
        freq=1000
        period=10
        #Trun Off Source
        self.SubFunc.SelSrc('GND')
        MUXPATH = gvar.MUX1_MOA | gvar.MUX2_PASS | gvar.MUX3_FIR1K | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SubFunc.SetDDS(freq,gvar.SRCAMP1KHZ)
        self.SubFunc.SelDr1Res('PASS')

        if 500< ind <= 5000:
            MOAC='10N'
            MOAR=['10R',10]
            Sampling = 2500000*period/freq
        elif 5000< ind <= 50000:
            MOAC='10N'
            MOAR=['100R',100]
            Sampling = 2500000*period/freq
        elif 50000 < ind <= 500000:
            MOAC='10N'
            MOAR=['1K',1000]
            Sampling = 2500000*period/freq
        elif 500000 < ind <= 5000000:
            MOAC='10N'
            MOAR=['10K',9999.768]
            Sampling = 2500000*period/freq
        else :
            period=10
            if gva.AC60HZ==1:
                freq=60
            else:
                freq=50
            MOAC='10N'
            MOAR=['100K',99998.672]
            Sampling = 2500000*period/freq

        #Turn ON Power
        self.SubFunc.SelSrc('ACV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        ADC_V=self.ADC.AdcMv(cnt=Sampling,type='AC',cal='N')

        MOAI=ADC_V/MOAR[1]
        ZL= gvar.ADCMAMP1KHZ/MOAI
        IND= (2*3.14159*freq*ZL)*pow(10,6)

        print('IND={}uH'.format(IND))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return IND

    def LAC2W10KHZ(self,ind):
        freq=10000
        period=10
        #Trun Off Source
        self.SubFunc.SelSrc('GND')
        MUXPATH = gvar.MUX1_MOA | gvar.MUX2_PASS | gvar.MUX3_FIR10K | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SubFunc.SetDDS(freq,gvar.SRCAMP10KHZ)
        self.SubFunc.SelDr1Res('PASS')

        if 10< ind <= 500:
            MOAC='10N'
            MOAR=['10R',10]
            Sampling = 2500000*period/freq
        elif 500< ind <= 5000:
            MOAC='1N'
            MOAR=['100R',99.997]
            Sampling = 2500000*period/freq
        elif 5000 < ind <= 50000:
            MOAC='100P'
            MOAR=['1K',999.976]
            Sampling = 2500000*period/freq
        elif 50000 < ind <= 100000:
            MOAC='100P'
            MOAR=['10K',9976.97]
            Sampling = 2500000*period/freq
        elif 100000 < ind <= 500000:
            MOAC='8.2P'
            MOAR=['10K',9999.867]
            Sampling = 2500000*period/freq
        else :
            period=10
            if gva.AC60HZ==1:
                freq=60
            else:
                freq=50
            MOAC='8.2P'
            MOAR=['100K',99867.53]
            Sampling = 2500000*period/freq

        #Turn ON Power
        self.SubFunc.SelSrc('ACV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        ADC_V=self.ADC.AdcMv(cnt=Sampling,type='AC',cal='N')

        MOAI=ADC_V/MOAR[1]
        ZL= gvar.ADCMAMP10KHZ/MOAI
        IND= (2*3.14159*freq*ZL)*pow(10,6)

        print('IND={}uH'.format(IND))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return IND

    def LAC2W100KHZ(self,ind):
        freq=100000
        period=10
        #Trun Off Source
        self.SubFunc.SelSrc('GND')
        MUXPATH = gvar.MUX1_MOA | gvar.MUX2_PASS | gvar.MUX3_FIR100K | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetMUX(MUXPATH)
        self.SubFunc.SetDr1OutRly('DR1MP')
        self.SubFunc.SetMoaOutRly('SP','ON')
        self.SubFunc.SetDDS(freq,gvar.SRCAMP100KHZ)
        self.SubFunc.SelDr1Res('PASS')

        if 1< ind <= 10:
            MOAC='1N'
            MOAR=['10R',10]
            Sampling = 2500000*period/freq
        elif 10< ind <= 50:
            MOAC='100P'
            MOAR=['10R',10]
            Sampling = 2500000*period/freq
        elif 50 < ind <= 500:
            MOAC='100P'
            MOAR=['100',99.997]
            Sampling = 2500000*period/freq
        elif 500 < ind <= 5000:
            MOAC='100P'
            MOAR=['1K',997.697]
            Sampling = 2500000*period/freq
        elif 5000 < ind <= 50000:
            MOAC='8.2P'
            MOAR=['10K',9986.753]
            Sampling = 2500000*period/freq
        else :
            period=10
            if gva.AC60HZ==1:
                freq=60
            else:
                freq=50
            MOAC='8.2P'
            MOAR=['100K',88894.93]
            Sampling = 2500000*period/freq

        #Turn ON Power
        self.SubFunc.SelSrc('ACV')

        #MOA Control
        self.SubFunc.SetMOA(MOAR[0],MOAC)

        time.sleep(0.1)
        ADC_V=self.ADC.AdcMv(cnt=Sampling,type='AC',cal='N')

        MOAI=ADC_V/MOAR[1]
        ZL= gvar.ADCMAMP100KHZ/MOAI
        IND= (2*3.14159*freq*ZL)*pow(10,6)

        print('IND={}uH'.format(IND))

        #Turn OFF Power
        self.SubFunc.SelSrc('GND')

        return IND

    def Diode(self,curr='1mA',clampv=2):
        DictCCS = {
            '20mA'  : [ '100R', clampv+2 ],
            '10mA'  : [ '100R', clampv+1 ],
            '5mA'   : [ '100R', clampv+0.5 ],
            '2.5mA' : [ '100R', clampv+0.25],
            '1mA'   : [ '1K',   clampv+1 ],
            '0.5mA' : [ '1K',   clampv+0.5],
        }

        #Trun Off Source
        self.SubFunc.SelSrc('GND')

        # Setting measure path
        ATTPATH = gvar.ATT_HP_MS | gvar.ATT_HP_1M | gvar.ATT_LP_SS | gvar.ATT_LP_1M
        MUXPATH = gvar.MUX1_ATT | gvar.MUX2_PASS | gvar.MUX3_FIR100K | gvar.MUX4_PASS | gvar.MUX5_NG05
        self.SubFunc.SetATT(ATTPATH)
        self.SubFunc.SetMUX(MUXPATH)

        #Setting Source
        self.SubFunc.SelDr1Res(DictCCS[CURR][0])
        self.SRC.SetCCSClampV(clampv)
        self.SRC.SetDraDcSrc(DictCCS[CURR][1])
        if (CURR=='0mA'):
            self.SubFunc.SetDr1OutRly('CCS','OFF')   
        else:
            self.SubFunc.SetDr1OutRly('CCS','ON')

        #Measure Voltage
        Sampling=2500
        MV=self.ADC.AdcMv(cnt=Sampling,type='DC',cal='Y')

        #Diode Forward Voltage
        diode_v = abs(MV/gvar.MUXG05)

        return diode_v


    def BJTMeasure(self,type='NPN'):

        #Trun Off Source
        self.SubFunc.SelSrc('GND')
        self.SubFunc.SetDr2Rly('GND')

        # Setting measure path
        ATTPATH = gvar.ATT_HP_SS | gvar.ATT_HP_1M | gvar.ATT_LP_GS | gvar.ATT_LP_1M
        MUXPATH = gvar.MUX1_ATT | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_PASS
        self.SubFunc.SetATT(ATTPATH)
        self.SubFunc.SetMUX(MUXPATH)

        #MP #GP
        DRAPATH = gvar.DRA1K | gvar.DRAMP | gvar.GNDGP
        self.SubFunc.SetDrA(DRAPATH)

        #SP
        DRBPATH = gvar.DRBSP | gvar.DRB200R     
        self.SubFunc.SetDrA(DRBPATH)

        #Set SRC
        if type=='NPN':
            self.SRC.SetDraDcSrc(1)
            self.SRC.SetDrbDcSrc(2)
        elif type == 'PNP':
            self.SRC.SetDraDcSrc(0)
            self.SRC.SetDrbDcSrc(-2)

        self.SubFunc.SelSrc('DCVx5')
        self.SubFunc.SetDr2Rly('DCV','ON')

        #Measure V
        Sampling=2500
        MV=self.ADC.AdcMv(cnt=Sampling,type='DC',cal='Y')

        if type=='NPN':
            print('VCE={}V'.format(MV))
        elif type =='PNP':
            print('VCE=-{}V'.format(MV))
             
    #########################################################
        if type=='NPN':
            self.SetAtt1Rly('HPSS','OFF')
            self.SetAtt1Rly('HPMS','ON')
        elif type =='PNP':
            self.SetAtt1Rly('LPGS','OFF')
            self.SetAtt1Rly('LPMS','ON')    

        adcv=self.EthCmd('atk_get_adc')
        StAdc=adcv.index('ADC_V=')+6
        EndAdc=adcv.index(',')
        adcv=float(adcv[StAdc:EndAdc])
        if type=='NPN':
            print('VBE={}V'.format(adcv))
        elif type =='PNP':
            print('VBE=-{}V'.format(adcv)) 

        self.SetMux1A('DR1C')
        self.SetMux1B('PASS')
        self.SetMux1C('PASS')
        self.SetMux1D('PASS')
        self.SetMux1E('PASS')
        # HexRly=format(self.Mux1Lch1Data,'x')
        # print ('Addr=0x16, Data=0x{}'.format(HexRly))
        time.sleep(0.001)
        #Measure ib
        adcv=self.EthCmd('atk_get_adc')
        StAdc=adcv.index('ADC_V=')+6
        EndAdc=adcv.index(',')
        adcv=float(adcv[StAdc:EndAdc])
        ib = adcv*1000 / 499 
        print('IB={}mA'.format(ib))

        self.SetMux1A('DR2C')
        self.SetMux1B('PASS')
        self.SetMux1C('PASS')
        self.SetMux1D('PASS')
        self.SetMux1E('PASS')
        # HexRly=format(self.Mux1Lch1Data,'x')
        # print ('Addr=0x16, Data=0x{}'.format(HexRly))
        time.sleep(0.001)
        #Measure ic
        adcv=self.EthCmd('atk_get_adc')
        StAdc=adcv.index('ADC_V=')+6
        EndAdc=adcv.index(',')
        adcv=float(adcv[StAdc:EndAdc])
        ic = adcv*1000 / 200 
        hfe= ic/ib
        print('IC={}mA'.format(ic))
        print('HFE={}'.format(hfe))

    #def MOSFET():

    '''

