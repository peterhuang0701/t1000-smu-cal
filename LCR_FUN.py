import socket
import sys
import time
import os
import binascii
import math
import re
import gvar

class Func:

    def Version(self):
        McuVer=gvar.EthCmd('atk_ver')
        Year=gvar.EthCmd('atk_fpga_rd_a')
        Day=gvar.EthCmd('atk_fpga_rd_b')
        FWVer=gvar.EthCmd('atk_fpga_rd_c')
        BDVer=gvar.EthCmd('atk_fpga_rd_d')
        strMcu=str(McuVer)[14:27]
        StrYear=str(Year)[19:23]
        StrMan=str(Day)[19:21]
        StrDay=str(Day)[21:23]
        StrVer=str(FWVer)[19:23]
        StrBDVer=str(BDVer)[19:22]
        StrIDVer=str(BDVer)[22]
        print ('MCU Version = {}'.format(strMcu))
        print ('FPGA Date = {}/{}/{}'.format(StrYear,StrMan,StrDay))
        print ('FPGA Version = {}'.format(StrVer))
        print ('SMU Board ID = {}-0{}\r\n'.format(StrBDVer,StrIDVer))
   
    def SetDAC(self,ch,value,volt):
        DictCH = {
                    'CH1'   :   '37'  ,
                    'CH2'   :   '38'  ,
                    'CH3'   :   '39'  ,
                    'CH4'   :   '3A'  ,  
        }
        #vout= dac-2.048
        if (ch=='CH1'):
            if (value<-2 or value>2):
                volt=volt/5
            volt=volt+2.5
        elif (ch=='CH2'):
            volt=volt*2+2.5
            # print('VG_DAC={}'.format(volt))
        elif (ch=='CH3'):
            volt=volt/4
            volt=volt+2.5
        elif (ch=='CH4'):
            volt=volt/3
        dacV= int(pow(2,16)*volt/5)
        dacV=format(dacV,'x')
        gvar.EthCmd('atk_fpga_wr_{}_{}'.format(DictCH[ch],dacV))


    def SetDAC2(self,volt):
        #vout= dac-2.048
        dacV= int(pow(2,16)*volt/2.5)
        # print(dacV)
        dacV=format(dacV,'x')
        gvar.EthCmd('atk_fpga_wr_62_{}'.format(dacV))
        return dacV
        

    def SelSrc(self,path):
        DictPath = {
            'GND'       :   0  ,
            'DCV'       :   1  ,
            'ACV'       :   2  ,
            'SRC'       :   3  , 
            'DCVx5'     :   4  , 
            'SRCx5'     :   5  ,
        }
        gvar.Dr1LchData = (gvar.Dr1LchData & 0x1fff) | DictPath[path]<<13
        HexMux=format(gvar.Dr1LchData,'x')
        # print (HexMux)
        gvar.EthCmd('atk_fpga_wr_12_{}'.format(HexMux))


    def SelDr1Res(self,res):
        DictRes = {
            'PASS'  :   0,
            '10R'   :   1,
            '100R'  :   2,
            '1K'    :   3,
            '10K'   :   4,
            '100K'  :   5,
            '1M'    :   6,
            'OFF'   :   7,
        }
        gvar.Dr1LchData = (gvar.Dr1LchData & 0xfff0) | DictRes[res]
        HexRes=format(gvar.Dr1LchData,'x')
        gvar.EthCmd('atk_fpga_wr_12_{}'.format(HexRes))

    def SetDr1OutRly(self,rly,act='OFF'):
        DictRlyON = {
            'DR1MP' : 0x0010,
            'DR1SP' : 0x0020,
            'CCSMP' : 0x0100,
            'CCSSP' : 0x0200,
            'CCSEN' : 0x0400,
            'GNDSP' : 0x0800,
            'GNDGP' : 0x1000,
        }
        DictRlyOFF = {
            'DR1MP' : 0xFFEF,
            'DR1SP' : 0xFFDF,
            'CCSMP' : 0xFEFF,
            'CCSSP' : 0xFDFF,
            'CCSEN' : 0xFBFF,
            'GNDSP' : 0xF7FF,
            'GNDGP' : 0xEFFF,
            'OFF'   : 0X0000,
        }

        if act=='ON':
            gvar.Dr1LchData = gvar.Dr1LchData | DictRlyON[rly]
        elif act=='OFF':
            gvar.Dr1LchData = gvar.Dr1LchData & DictRlyOFF[rly]

        HexRly=format(gvar.Dr1LchData,'x')
        gvar.EthCmd('atk_fpga_wr_12_{}'.format(HexRly))

    def SetDrB(self,value):
        gvar.Dr2LchData = gvar.Dr2LchData | value
        HexMux=format(gvar.Dr2LchData,'x')
        # print (HexMux)
        gvar.EthCmd('atk_fpga_wr_13_{}'.format(HexMux))

    def SetDr2Rly(self,rly,act='OFF'):
        DictPathON = {
            'GND'  :   0x00,
            'DCV'   :   0x20,
            'MP'    :   0x08,
            'SP'    :   0x10,
        }

        DictPathOFF = {
            'GND'  :   0xFF,
            'DCV'   :   0xDF,
            'MP'    :   0xF7,
            'SP'    :   0xEF,
            'OFF'   :   0x00,
        }
        if act=='ON':
            gvar.Dr2LchData = gvar.Dr2LchData | DictPathON[rly]
        elif act=='OFF':
            gvar.Dr2LchData = gvar.Dr2LchData & DictPathON[rly]

        HexRly=format(gvar.Dr2LchData,'x')
        gvar.EthCmd('atk_fpga_wr_13_{}'.format(HexRly))

    def SetDr2Res(self,res):
        DictRes = {
            'PASS'  :   0,
            '20R'   :   1,
            '200R'  :   2,
            '1K'    :   3,
            'OFF'   :   7,
        }
        gvar.Dr2LchData = (gvar.Dr2LchData & 0xf8) | DictRes[res]
        HexRes=format(gvar.Dr2LchData,'x')
        gvar.EthCmd('atk_fpga_wr_13_{}'.format(HexRes))
 
    def SetMOARes(self,res):
        DictRes = {
            10      :   1,
            100     :   2,
            1000    :   3,
            10000   :   4,
            100000  :   5,
            1000000 :   6, 
        }
        gvar.MoaLchData = (gvar.MoaLchData & 0xFff0) | DictRes[res]
        HexRes=format(gvar.MoaLchData,'x')
        #print('SetMOARes={}'.format(gvar.MoaLchData,'x'))
        gvar.EthCmd('atk_fpga_wr_15_{}'.format(HexRes))

    def SetMoaOutRly(self,rly,act='ON'):
        DictRlyON = {
            'SP'    : 0x0010,
            'SS'    : 0x0020,
            'SSCAP' : 0x0040,
            'GS'    : 0x0080,
            'GndOFF': 0x0100,
            'EN'    : 0x0200,
            '100P'  : 0x0400,
            '1N'    : 0x0800,
            '10N'   : 0x1000,
        }

        DictRlyOFF = {
            'SP'    : 0xFFEF,
            'SS'    : 0xFFDF,
            'SSCAP' : 0xFFBF,
            'GS'    : 0xFF7F,
            'GndOFF': 0xFEFF,
            'EN'    : 0xFDFF,
            '100P'  : 0xFBFF,
            '1N'    : 0xF7FF,
            '10N'   : 0xEFFF,
            'OFF'   : 0x0000,
        }

        if act=='ON':
            gvar.MoaLchData = gvar.MoaLchData | DictRlyON[rly]
        elif act=='OFF':
            gvar.MoaLchData = gvar.MoaLchData & DictRlyOFF[rly]

        HexRly=format(gvar.MoaLchData,'x')
        #print ('MoaLchData={}'.format(gvar.MoaLchData))
        gvar.EthCmd('atk_fpga_wr_15_{}'.format(HexRly))

    def SetATT(self,value):
        if value == 0:
            gvar.Att1LchData = gvar.Att1LchData & value
        else:   
            gvar.Att1LchData = gvar.Att1LchData | value 
        HexRly=format(gvar.Att1LchData,'x')
        #print ('Att1LchData={}'.format(gvar.Att1LchData))
        gvar.EthCmd('atk_fpga_wr_14_{}'.format(HexRly))   

    def SetAtt1Rly(self,rly,act='OFF'):
        DictRlyON = {
            'LPMS'    :   0x0001,
            'LPSS'    :   0x0002,
            'LPGS'    :   0x0004,
            'LP1X'    :   0x0020,
            'LPD10'   :   0x0088,
            'LPD5'    :   0x0050,
            'LP1M'    :   0x0008,
            'HPMS'    :   0x0100,
            'HPSS'    :   0x0200,
            'HPGS'    :   0x0400,
            'HP1X'    :   0x2000,
            'HPD10'   :   0x8800,
            'HPD5'    :   0x5000,
            'HP1M'    :   0x0800,
        }
        DictRlyOFF = {
            'LPMS'    :   0xFFFE,
            'LPSS'    :   0xFFFD,
            'LPGS'    :   0xFFFB,
            'LP1X'    :   0xFFEF,
            'LPD10'   :   0xFF77,
            'LPD5'    :   0xFFAF,
            'LP1M'    :   0xFFF7,
            'HPMS'    :   0xFEFF,
            'HPSS'    :   0xFDFF,
            'HPGS'    :   0xFBFF,
            'HP1X'    :   0xDFFF,
            'HPD10'   :   0x77FF,
            'HPD5'    :   0xAFFF,
            'ALL'     :   0x0000,
            'HP1M'    :   0xF7FF,
        }

        if act=='ON':
            gvar.Att1LchData = gvar.Att1LchData | DictRlyON[rly]
        elif act=='OFF':
            gvar.Att1LchData = gvar.Att1LchData & DictRlyOFF[rly]

        HexRly=format(gvar.Att1LchData,'x')
        #print ('Att1LchData={}'.format(gvar.Att1LchData))
        gvar.EthCmd('atk_fpga_wr_14_{}'.format(HexRly))

    
    def DisResRly(self,rly,act='OFF'):
        DictRlyON ={
            'LMP'   :   0x01, 
            'LGP'   :   0x02,
            'RSP'   :   0x04,
            'RGP'   :   0x08,
            '100K'  :   0x00,
            '200R'  :   0x10,
            '100R'  :   0x20,
            '50R'   :   0x40,
            '10R'   :   0x80,
        }

        DictRlyOFF ={
            'LMP'   :   0xFE, 
            'LGP'   :   0xFD,
            'RSP'   :   0xFB,
            'RGP'   :   0xF7,
            '100K'  :   0xFF,
            '200R'  :   0xEF,
            '100R'  :   0xDF,
            '50R'   :   0xBF,
            '10R'   :   0x7F,
        }

        if act=='ON':
            gvar.DisLchData = gvar.DisLchData | DictRlyON[rly]
        elif act=='OFF':
            gvar.DisLchData = gvar.DisLchData & DictRlyOFF[rly]

        HexRly=format(gvar.DisLchData,'x')
        #print ('DisLchData={}'.format(self.DisLchData))
        gvar.EthCmd('atk_fpga_wr_11_{}'.format(HexRly))

    def SetExPortRly(self,rly,act='ON'):
        DictRlyON = {
            'MP'        :   0x0001,   
            'MS'        :   0x0002,
            'SP'        :   0x0004,
            'SS'        :   0x0008,
            'GP'        :   0x0010,
            'GS'        :   0x0020,
            'PWEN'      :   0x0040,
            'NC'        :   0x0080,
            'ADC1CAL'   :   0x0100,
        }
        DictRlyOFF = {
            'MP'        :   0xfffe,   
            'MS'        :   0xfffd,
            'SP'        :   0xfffb,
            'SS'        :   0xfff7,
            'GP'        :   0xffef,
            'GS'        :   0xffdf,
            'PWEN'      :   0xffbf,
            'NC'        :   0xff7f,
            'ADC1CAL'   :   0xfeff,
            'ALL'       :   0X0000,
        }

        if act=='ON':
            gvar.ExtLchData = gvar.ExtLchData | DictRlyON[rly]
        elif act=='OFF':
            gvar.ExtLchData = gvar.ExtLchData & DictRlyOFF[rly]

        HexRly=format(gvar.ExtLchData,'x')
        gvar.EthCmd('atk_fpga_wr_28_{}'.format(HexRly))


    def SetDDS(self,freq,amp):
        intFreq= int(freq*pow(2,32)/20000000)
        Amplitude = amp
        freqL=intFreq & 0x0000ffff
        freqH=intFreq >> 16
        HexfreqL=format(freqL,'x')
        HexfreqH=format(freqH,'x')

        self.SetDAC('CH1',0,0)
        # (1k/499)*1.72*(VG+1)=2AV
        # 1.72*VG+1.72=AV
        # VG= (AV-1.72)/1.72
        # DACB= (Amplitude/1.3333)
        DACB= (Amplitude-1.72)/1.72
        # print('DACB={}'.format(DACB))

        self.SetDAC('CH2',DACB,DACB)

        gvar.EthCmd('atk_fpga_wr_41_{}'.format(HexfreqL))
        gvar.EthCmd('atk_fpga_wr_42_{}'.format(HexfreqH))
        gvar.EthCmd('atk_fpga_wr_43_1')
    
    def CalGainOffset(self,y_val,x_val):
        cal_slope=[]
        cal_offset=[]
        for i in range(len(x_val)-1):
            try:
                slope = (y_val[i+1]-y_val[i])/((x_val[i+1]-x_val[i]))
            except:
                slope = 0
            cal_slope.append(slope)
            a = (y_val[i]-x_val[i]*slope)
            offset="{:.6f}".format(a)
            cal_offset.append(offset)
            #print('G{}={}'.format(i,slope))
            #print('O{}={}\n'.format(i,offset))
        return cal_slope,cal_offset

    def SysARST(self):
        self.SetDAC('CH1',0,0)
        self.SetDAC('CH2',0,0)
        self.SetDAC('CH3',0,0)
        self.SetDAC('CH4',0,0)
        gvar.EthCmd('atk_fpga_wr_8_1')
        gvar.EthCmd('atk_fpga_wr_8_0')

    def GetPath1Offset(self):
        self.SetDr1OutRly('GNDSP','ON')
        self.SetExPortRly('SPSS','ON')
        self.SetAtt1Rly('LPSS','ON')
        self.SetAtt1Rly('LP1X','ON')
        self.SetAtt1Rly('HPSS','ON')
        self.SetAtt1Rly('HP1X','ON')

        self.SetMux1A('ATT1')
        self.SetMux1B('PASS')
        self.SetMux1C('PASS')
        self.SetMux1D('PASS')
        self.SetMux1E('PASS')

    def SetMOA(self,moar,moac):
        MOARes=moar
        MOACap=moac
        # self.SetMoaOutRly('100P','OFF')
        # self.SetMoaOutRly('1N','OFF')
        # self.SetMoaOutRly('10N','OFF')
        # self.SetMoaOutRly('8.2P','OFF')
        # self.SetMoaOutRly('EN','OFF')

        # time.sleep(0.01)
        # self.SetMoaOutRly('SP','ON')
        self.SetMoaOutRly(MOACap,'ON')
        self.SelMOARes(MOARes)
        time.sleep(0.01)
        self.SetMoaOutRly('EN','ON')

    def WriteEEP(self,addr,data):
        
        gvar.EthCmd('atk_eep_r_f_{}'.format(addr))
 
    def SlopeOffset(self,y_val,x_val,gvalue,ovalue):
        cal_slope=[]
        cal_offset=[]
        for i in range(len(x_val)-1):
            slope = (y_val[i+1]-y_val[i])/((x_val[i+1]-x_val[i]))
            offset = (y_val[i]-x_val[i]*slope)*gvalue + ovalue
            slope = slope * gvalue
            slope = '{:.8f}'.format(slope)
            offset = '{:.8f}'.format(offset)
            # print ('offset={}'.format(offset))
            # print ('gvalue={}'.format(gvalue))
            # print ('slope={}'.format(slope))
            cal_slope.append(slope)
            cal_offset.append(offset)
        return cal_slope,cal_offset

    def WriteRom(self,addr_gain,addr_offset,cal_point,cal_gain,cal_offset):

        gain=[]
        offset=[]
        GainfailCheck=[]
        OffsetfailCheck=[]
        addrg=addr_gain
        addro=addr_offset

        for i in range(len(cal_gain)):
            str_slope=str(cal_gain[i])
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(addrg,str_slope))
            addrg=int(addrg,16)
            addrg=addrg+4
            addrg=format(addrg,'x')
    
        for i in range(len(cal_offset)):
            str_offset=str(cal_offset[i])
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(addro,str_offset))
            addro=int(addro,16)
            addro=addro+4
            addro=format(addro,'x')

        addrg=addr_gain
        addro=addr_offset

        for i in range(len(cal_gain)):
            read_data=gvar.EthCmd('atk_eep_r_f_{}'.format(addrg))
            print('Gain[ {} ~ {} ] = {}'.format(cal_point[i],cal_point[i+1],read_data))
            addrg=int(addrg,16)
            addrg=addrg+4
            addrg=format(addrg,'x')

        for i in range(len(cal_offset)):
            read_data=gvar.EthCmd('atk_eep_r_f_{}'.format(addro)) 
            print('Offset[ {} ~ {} ] = {}'.format(cal_point[i],cal_point[i+1],read_data))
            addro=int(addro,16)
            addro=addro+4
            addro=format(addro,'x')

    def ReadCalData(self,cal_point,addr_gain,addr_offset):
        gain=[]
        offset=[]
        addrg=addr_gain
        addro=addr_offset
        for i in range(len(cal_point)-1):
            read_data=float(gvar.EthCmd('atk_eep_r_f_{}'.format(addrg))[:-2])
            gain.append(read_data)
            addrg=int(addrg,16)
            addrg=addrg+4
            addrg=format(addrg,'x')

        for i in range(len(cal_point)-1):
            read_data=float(gvar.EthCmd('atk_eep_r_f_{}'.format(addro))[:-2])
            offset.append(read_data)
            addro=int(addro,16)
            addro=addro+4
            addro=format(addro,'x')
        # print('Gain Array ={}'.format(gain))
        # print('Offset Array ={}'.format(offset))
        return gain,offset

    def ReadOneCalData(self,addr):
        read_data=float(gvar.EthCmd('atk_eep_r_f_{}'.format(addr)))
        return read_data

    def FindGainOffset(self,value,calp,calg,calo):
        # print(calp)
        # print(calg)
        # print(calo)
        maxv= max(calp)
        minv= min(calp)
        rgain=0
        roffset=0
        # print ('value={}'.format(value))
        #print ('maxv={}'.format(maxv))
        #print ('minv={}'.format(minv))
        for i in range (len(calg)):
            if value >= maxv :
                rgain = calg[len(calg)-1]
                roffset = calo[len(calo)-1]
                break
            elif value<=minv:
                rgain = calg[0]
                roffset = calo[0]
                break
            elif calp[i] <= value <= calp[i+1]:
                # print ('calp[i]={},calp[i+1]={}'.format(calp[i],calp[i+1]))
                rgain = calg[i]
                roffset = calo[i]
                break
        # print ('gain={}'.format(rgain))
        # print ('offset={}'.format(roffset))
        # print('Gain[ {} ~ {} ]'.format(calp[i],calp[i+1]))
        # print('Offset[ {} ~ {} ]'.format(calp[i],calp[i+1]))
        CalV=float(value)*float(rgain)+float(roffset)
        return CalV

    def SetMux1(self,path):
        DictPath = {
            'AGND'      :   0x0000 ,
            'DR1C'      :   0x0001 ,
            'DR1BUF'    :   0x0002 ,
            'CLAMPV'    :   0x0003 ,
            'DR1IN'     :   0x0004 ,
            'DR2C'      :   0x0005 ,
            'DR2BUF'    :   0x0006 ,
            'ATT1'      :   0x0007 ,
        
            'MOAC'      :  0x2000 ,
            'DR1OUT'    :   0x2001 ,
            'DR2OUT'    :   0x2002 ,
            'TESTJET'   :   0x2003 ,
            'MOAV'      :   0x2004,

            '+2.5VREF'  :   0x4000 ,
            '-2.5VREF'  :   0x4001 ,
            '+5VREF'    :   0x4002 ,
            'DACAC'     :   0x4003 ,
            'DACDC'     :   0x4004 ,
            'DR2SRC'    :   0X4005 ,
            'CAL'       :   0x4006 ,
            'DDSREF'    :   0x4007 ,   
        }
        gvar.Mux1Lch1Data = (gvar.Mux1Lch1Data & 0x9FF8) | DictPath[path]
        HexMux=format(gvar.Mux1Lch1Data,'x')
        # print(HexMux)
        gvar.EthCmd('atk_fpga_wr_16_{}'.format(HexMux))

    def SetMux2(self,path):
        DictPath = {
            'PASS'      :   0x00 ,
            'BUFF'      :   0x08 ,
            '0.2X'      :   0x10 ,
            '2X'        :   0x18 ,
            '4X'        :   0x20 ,
            '12X'       :   0x28 ,
            '36X'       :   0x30 ,
            'LPF'       :   0x38 ,
        }
        gvar.Mux1Lch1Data = (gvar.Mux1Lch1Data & 0xFFC7) | DictPath[path]
        HexMux=format(gvar.Mux1Lch1Data,'x')
        # print('HexMux=',HexMux)
        gvar.EthCmd('atk_fpga_wr_16_{}'.format(HexMux))

    def SetMux3(self,path):
        DictPath = {
            'PASS'      :   0x00 ,
            'FIR100K'   :   0x40 ,
            'FIR10K'    :   0x80 ,
            'FIR1K'     :   0xC0 ,
        }
        gvar.Mux1Lch1Data = (gvar.Mux1Lch1Data & 0xFF3F) | DictPath[path]
        HexMux=format(gvar.Mux1Lch1Data,'x')
        #print(HexMux)
        gvar.EthCmd('atk_fpga_wr_16_{}'.format(HexMux))

    def SetMux4(self,path):
        DictPath = {
            'GND'       :   0x000 ,
            'PASS'      :   0x100 ,
            'PHASE'     :   0x200 ,
            'PHASEC'    :   0x300 ,
        }
        gvar.Mux1Lch1Data = (gvar.Mux1Lch1Data & 0xFCFF) | DictPath[path]
        HexMux=format(gvar.Mux1Lch1Data,'x')
        #print(HexMux)
        gvar.EthCmd('atk_fpga_wr_16_{}'.format(HexMux))

    def SetMux5(self,path):
        DictPath = {
            'GND'       :   0x0000 ,
            'PASS'      :   0x0400 , #0x000
            'BUFF'      :   0x0800 , #0x400
            '-0.5X'     :   0x0C00 , #0x800
            'LPF'       :   0x1000 , #0xC00
            '+2.5VREF'  :   0x1400 ,
            '-2.5VREF'  :   0x1800 ,
            'NC'        :   0x1C00 ,
        }
        gvar.Mux1Lch1Data = (gvar.Mux1Lch1Data & 0x63FF) | DictPath[path]
        HexMux=format(gvar.Mux1Lch1Data,'x')
        #print(HexMux)
        gvar.EthCmd('atk_fpga_wr_16_{}'.format(HexMux))


    def SetPhsGRly(self,act='OFF'):
        if act=='ON':
            gvar.Mux1Lch1Data = gvar.Mux1Lch1Data | 0x2000
        elif act=='OFF':
            gvar.Mux1Lch1Data = gvar.Mux1Lch1Data & 0xBFFF

        HexMux=format(gvar.Mux1Lch1Data,'x')
        gvar.EthCmd('atk_fpga_wr_29_{}'.format(HexMux))

    def SetMUX(self,value):
        gvar.Mux1Lch1Data=gvar.Mux1Lch1Data | value 
        HexMux=format(gvar.Mux1Lch1Data,'x')
        gvar.EthCmd('atk_fpga_wr_16_{}'.format(HexMux))

    def SetDrA(self,value):
        gvar.Dr1LchData = gvar.Dr1LchData | value
        HexMux=format(gvar.Dr1LchData,'x')
        # print (HexMux)
        gvar.EthCmd('atk_fpga_wr_12_{}'.format(HexMux))


    def SetCalSmuRly(self,rly,act='OFF'):
        DictRlyON = {
            'SMU_P_MP'    :   0x0001,
            'SMU_P_SP'    :   0x0002,
            'SMU_P_GP'    :   0x0004,
            'SMU_P_MS'    :   0x0008,
            'SMU_P_SS'    :   0x0010,
            'SMU_P_GS'    :   0x0020,
            'SMU_N_MP'    :   0x0040,
            'SMU_N_SP'    :   0x0080,
            'SMU_N_GP'    :   0x0100,
            'SMU_N_MS'    :   0x0200,
            'SMU_N_SS'    :   0x0400,
            'SMU_N_GS'    :   0x0800,
            'DMM_P_MP'    :   0x1000,
            'DMM_P_SP'    :   0x2000,
            'DMM_P_GP'    :   0x4000,
            'DMM_P_MS'    :   0x8000    
        }
        DictRlyOFF = {
            'SMU_P_MP'    :   0xFFFE,
            'SMU_P_SP'    :   0xFFFD,
            'SMU_P_GP'    :   0xFFFB,
            'SMU_P_MS'    :   0xFFF7,
            'SMU_P_SS'    :   0xFFEF,
            'SMU_P_GS'    :   0xFFDF,
            'SMU_N_MP'    :   0xFFBF,
            'SMU_N_SP'    :   0xFF7F,
            'SMU_N_GP'    :   0xFEFF,
            'SMU_N_MS'    :   0xFDFF,
            'SMU_N_SS'    :   0xFBFF,
            'SMU_N_GS'    :   0xF7FF,
            'DMM_P_MP'    :   0xEFFF,
            'DMM_P_SP'    :   0xDFFF,
            'DMM_P_GP'    :   0xBFFF,
            'DMM_P_MS'    :   0x7FFF
        }

        if act=='ON':
            gvar.CalSmuData = gvar.CalSmuData | DictRlyON[rly]
        elif act=='OFF':
            gvar.CalSmuData = gvar.CalSmuData & DictRlyOFF[rly]

        HexRly=format(gvar.CalSmuData,'x')
        gvar.MCUCmd(f'atk_ins1_set_{HexRly}')

    def SetCalDmmRly(self,rly,act='OFF'):
        DictRlyON = {
            'DMM_P_SS'    :   0x0001,
            'DMM_P_GS'    :   0x0002,
            'DMM_N_MP'    :   0x0004,
            'DMM_N_SP'    :   0x0008,
            'DMM_N_GP'    :   0x0010,
            'DMM_N_MS'    :   0x0020,
            'DMM_N_SS'    :   0x0040,
            'DMM_N_GS'    :   0x0080,
            'DMM_I_MP'    :   0x0100,
            'DMM_I_SP'    :   0x0200,
            'DMM_I_GP'    :   0x0400,
            'DMM_I_MS'    :   0x0800,
            'DMM_I_SS'    :   0x1000,
            'DMM_I_GS'    :   0x2000   
        }
        DictRlyOFF = {
            'DMM_P_SS'    :   0xFFFE,
            'DMM_P_GS'    :   0xFFFD,
            'DMM_N_MP'    :   0xFFFB,
            'DMM_N_SP'    :   0xFFF7,
            'DMM_N_GP'    :   0xFFEF,
            'DMM_N_MS'    :   0xFFDF,
            'DMM_N_SS'    :   0xFFBF,
            'DMM_N_GS'    :   0xFF7F,
            'DMM_I_MP'    :   0xFEFF,
            'DMM_I_SP'    :   0xFDFF,
            'DMM_I_GP'    :   0xFBFF,
            'DMM_I_MS'    :   0xF7FF,
            'DMM_I_SS'    :   0xEFFF,
            'DMM_I_GS'    :   0xDFFF,
        }

        if act=='ON':
            gvar.CalDmmData = gvar.CalDmmData | DictRlyON[rly]
        elif act=='OFF':
            gvar.CalDmmData = gvar.CalDmmData & DictRlyOFF[rly]

        HexRly=format(gvar.CalDmmData,'x')
        gvar.MCUCmd(f'atk_ins2_set_{HexRly}')



    