import socket
import sys
import time
import os
import binascii
import math
import re
from LCR_FUN import Func
import gvar

AdcCalPoint=[-4,-2,-1,-0.1, -0.01, 0.01, 0.1, 1, 3, 4 ]
AdcGainAddr='4000'
AdcOffAddr='4040'


class ADCFunc:
    def __init__(self):
        # gvar.EthCmd=eth.EthCmd
        self.SubFunc=Func()
        self.AdcGain,self.AdcOffset=self.SubFunc.ReadCalData(gvar.AdcCalPoint,gvar.AdcGainAddr,gvar.AdcOffAddr)
        # self.ReadBackCheck()

    def ReadBackCheck(self):
        print('ADC Gain  = {}'.format(self.AdcGain))
        print('ADC Offset= {}\r\n'.format(self.AdcOffset))

    def ADC(self,Len,type):
        sdram=[]
        gain=0.8 * 1.27
        adc='AD7760'
        AvgLen = Len
        SampLen = AvgLen + 50
        delay=(1/2500000)*SampLen

        HexAvgLen=hex(int(AvgLen))
        # print('HexAvgLen={}'.format(HexAvgLen))
        if AvgLen<=0xffff:
            HexAvgLen=hex(int(AvgLen))
            L_StrAvgLen=str(HexAvgLen)[2:]
            H_StrAvgLen='0'
        else:
            HexAvgLen=hex(int(AvgLen))
            L_StrAvgLen=str(HexAvgLen)[-4:]
            H_StrAvgLen=str(HexAvgLen)[2:-4]

        # print('L_StrAvgLen={}'.format(L_StrAvgLen))
        # print('H_StrAvgLen={}'.format(H_StrAvgLen))

        # StrAvgLen=str(HexAvgLen)[2:]
        # print('StrAvgLen={}'.format(StrAvgLen))

        HexSampLen=hex(int(SampLen))
        # print('HexSampLen={}'.format(HexSampLen))

        if SampLen<=0xffff:
            HexSampLen=hex(int(SampLen))
            L_StrSampLen=str(HexSampLen)[2:]
            H_StrSampLen='0'
        else:
            HexSampLen=hex(int(SampLen))
            L_StrSampLen=str(HexSampLen)[-4:]
            H_StrSampLen=str(HexSampLen)[2:-4]


        # print('L_HexSampLen={}'.format(L_StrSampLen))
        # print('H_HexSampLen={}'.format(H_StrSampLen))
        
        # print('StrSampLen={}'.format(StrSampLen))

        gvar.EthCmd('atk_fpga_wr_19_1')
        gvar.EthCmd('atk_fpga_wr_1A_{}'.format(L_StrSampLen)) # 150 #SRAM Address [15:0]
        gvar.EthCmd('atk_fpga_wr_1B_{}'.format(H_StrSampLen)) # SRAM Address [18:16]
        gvar.EthCmd('atk_fpga_wr_1C_0')                     # Average Start Address [15:0]
        gvar.EthCmd('atk_fpga_wr_1D_0')                     # Average Start Address [18:6]
        gvar.EthCmd('atk_fpga_wr_1E_{}'.format(L_StrAvgLen))  #100  #Average End Address [15:0]
        gvar.EthCmd('atk_fpga_wr_1F_{}'.format(H_StrAvgLen))  #Average end Address [18:16]
        gvar.EthCmd('atk_fpga_wr_19_2')
        time.sleep(delay)
        gvar.EthCmd('atk_fpga_wr_19_0')

        sumL =gvar.EthCmd('atk_fpga_rd_20') # Read SUM Data[15:0]
        StrSumL=str(sumL)[19:23]
        # print(StrSumL)

        sumM = gvar.EthCmd('atk_fpga_rd_21') # Read SUM Data[31:16]
        StrSumM= str(sumM)[19:23]
        # print(StrSumM)

        sumH = gvar.EthCmd('atk_fpga_rd_22') # Read SUM Data[39:32]
        StrSumH = str(sumH)[19:23]
        # print(StrSumH)

        SUM=StrSumH+StrSumM+StrSumL
        # print(SUM)

        intstr=int(SUM,16)/AvgLen

        intstr=intstr-0x80000

        #print (intstr)

        adcSum = (intstr/pow(2,19))*4.096*gain
        adcSum = '{:.6f}'.format(adcSum)
        # print ('\r\nADC1_SUM_V={}V'.format(adcSum))

        # if (self.Adc1CalEn):
        #     adcSum=self.CalAdc(adcSum,self.Adc1Point,self.Adc1Gain,self.Adc1Offset)
       
        '''
        mpyL=gvar.EthCmd('atk_fpga_rd_48')
        StrMpyL=str(mpyL)[19:23]
        #print(StrMpyL)

        mpyM=gvar.EthCmd('atk_fpga_rd_49')
        StrMpyM = str(mpyM)[19:23]
        #print(StrMpyM)
        
        mpyH=gvar.EthCmd('atk_fpga_rd_4a')
        StrMpyH = str(mpyH)[19:23]
        #print(StrMpyH)

        MPY=StrMpyH+StrMpyM+StrMpyL
        #print(MPY)

        intstr=int(MPY,16)

        intstr=math.sqrt(intstr)

        adcMpy = (intstr/pow(2,19))*4.096*gain

        if (self.Adc1CalEn):
            adcMpyCal=self.CalAdc(adcMpy,self.Adc1Point,self.Adc1Gain,self.Adc1Offset)
        else:
            adcMpyCal=adcMpy

        print ('ADC1_MPY_V={}V'.format(adcMpyCal))
        '''
        mpySumL=gvar.EthCmd('atk_fpga_rd_56')
        StrmpySumL=str(mpySumL)[19:23]
        #print(StrmpySumL)
        mpySumM=gvar.EthCmd('atk_fpga_rd_57')
        StrmpySumM=str(mpySumM)[19:23]
        #print(StrmpySumM)
        mpySumH=gvar.EthCmd('atk_fpga_rd_58')
        StrmpySumH=str(mpySumH)[19:23]
        #print(StrmpySumH)
        mpySumG=gvar.EthCmd('atk_fpga_rd_59')
        StrmpySumG=str(mpySumG)[19:23]
        #print(StrmpySumG)

        MPYSUM=StrmpySumG+StrmpySumH+StrmpySumM+StrmpySumL
        #print(MPYSUM)
        # print(AvgLen)

        intstr=int(MPYSUM,16)/(AvgLen)
        #print ('ADC1_RMS_V={}V'.format(intstr))

        intstr=math.sqrt(intstr)
    
        adcRMS = (intstr/pow(2,19))*4.096*gain
        adcRMS = '{:.6f}'.format(adcRMS)
   
        # if (self.Adc1CalEn):
        #     adcRMS=self.CalAdc(adcRMS,self.Adc1Point,self.Adc1Gain,self.Adc1Offset)

        # print ('ADC1_RMS_V={}V'.format(adcRMS))


        maxl=str(gvar.EthCmd('atk_fpga_rd_23'))[19:23]
        maxh=str(gvar.EthCmd('atk_fpga_rd_24'))[19:23]
        MaxV=maxh+maxl
        minl=str(gvar.EthCmd('atk_fpga_rd_25'))[19:23]
        minh=str(gvar.EthCmd('atk_fpga_rd_26'))[19:23]
        MinV=minh+minl
        MaxV=int(MaxV,16)
        MaxV=MaxV-0x80000

        MaxV = (MaxV/pow(2,19))*4.096*gain
        # if (self.Adc1CalEn):
        #     MaxV=self.CalAdc(MaxV,self.Adc1Point,self.Adc1Gain,self.Adc1Offset)
        
        MaxV = '{:.6f}'.format(MaxV)
        # print ('ADC1_MaxV={}V'.format(MaxV))

        MinV=int(MinV,16)
        MinV=MinV-0x80000
        MinV = (MinV/pow(2,19))*4.096*gain

        MinV = '{:.6f}'.format(MinV)
        # print ('ADC1_MinV={}V'.format(MinV))

        # if (self.Adc1CalEn):
        #     MinV=self.CalAdc(MinV,self.Adc1Point,self.Adc1Gain,self.Adc1Offset)

        # if type=='DC':
        #     return adcSum,(MaxV-MinV)
        # else:
        #     return adcRMS,(MaxV-MinV)
        if type=='DC':
            return float(adcSum)
        elif type == 'AC':
            return float(adcRMS)
        elif type == 'MAX':
            return float(MaxV)
        elif type == 'MIN':
            return float(MinV)
        elif type == 'DELTA':
            return float(MaxV)-float(MinV)

    def DrawLine(self,AvgLen):
        import matplotlib.pyplot as plt   # debug用才載入, 讓exe不用包matplotlib
        gvar.EthCmd('atk_fpga_wr_1_0032')
        gvar.EthCmd('atk_fpga_wr_2_80')
        gvar.EthCmd('atk_fpga_rd_4')
        SramD=[]
        for i in range (AvgLen):
            value=str(gvar.EthCmd('atk_fpga_rd_3'))[19:23]
            #print (value)
            value=int(value,16)
            value=value-0x8000
            adcv = (value/pow(2,15))*4.096*0.8
            # if (self.Adc1CalEn):
            #     adcv=self.CalAdc(adcv,self.Adc1Point,self.Adc1Gain,self.Adc1Offset)
            SramD.append(adcv)
            #print (adcv)
        plt.plot(SramD)
        plt.show()

    def AdcMv(self,cnt,type,cal='Y'):
        n_AdcReadV=self.ADC(cnt,type)
        # print('ADC[NOCAL]={}'.format(n_AdcReadV))
        y_AdcReadV=self.SubFunc.FindGainOffset(n_AdcReadV,gvar.AdcCalPoint,self.AdcGain,self.AdcOffset)
        # print('ADC[CAL]={}'.format(y_AdcReadV))
        if cal=='N':
            return n_AdcReadV
        else:
            return y_AdcReadV
    
    def Discharge(self):
        self.SubFunc.DisResRly('LMP','ON')
        self.SubFunc.DisResRly('RSP','ON')
        # self.SubFunc.SetAtt1Rly('CCS','ON')
        # self.SubFunc.SetMux('DIS')
        ATTPATH = gvar.ATT_HP_MS | gvar.ATT_HP_D5 | gvar.ATT_LP_SS | gvar.ATT_LP_D5
        self.SubFunc.SetATT(ATTPATH)
        MUXPATH = gvar.MUX1_ATT | gvar.MUX2_PASS | gvar.MUX3_PASS | gvar.MUX4_PASS | gvar.MUX5_NG05
        self.SubFunc.SetMUX(MUXPATH)


        adcv=self.AdcMv(1000,'DC',cal='Y')
        adcv=adcv/gvar.MUXG05 /gvar.ATTGD5
        # print(adcv)

        cnt=0
        for i in range(50):
            if adcv>10 :
                self.SubFunc.DisResRly('100K','ON')
            elif 5< adcv <= 10:
                self.SubFunc.DisResRly('200R','ON')
            elif 1< adcv <= 5 :
                self.SubFunc.DisResRly('100R','ON')
            elif 0.5 < adcv <= 1:
                self.SubFunc.DisResRly('50R','ON')
            else:
                self.SubFunc.DisResRly('10R','ON')

            adcv=self.AdcMv(1000,'DC',cal='Y')
            adcv=adcv/gvar.MUXG05 /gvar.ATTGD5
            # print(adcv)
            
            cnt=i
            if adcv<0.01:
                break
        if i==49:
            print('Discharge Fail')
        self.SubFunc.DisResRly('100K','ON')
        self.SubFunc.DisResRly('LMP','OFF')
        self.SubFunc.DisResRly('RSP','OFF')
        # self.SetExPortRly('MPMS','OFF')
        # self.SetExPortRly('SPSS','OFF')
        if cnt<49:
            return 'PASS'
        else:
            return 'FAIL'