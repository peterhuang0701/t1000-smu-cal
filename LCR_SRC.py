import socket
import sys
import time
from LCR_FUN import Func
import gvar

class LCRSrc:
    def __init__(self):
        #self.EthCmd=eth.EthCmd
        self.SubFunc=Func()

    def SetDraDcSrc(self,value):
        if -2 < value < 2 :
            SourceV=self.SubFunc.FindGainOffset(value,gvar.DraDcLCalPoint,gvar.DraDcLGain,gvar.DraDcLOffset)
            # self.SubFunc.SelSrc('DCV')
            # print('low range={}'.format(SourceV))
        else:
            SourceV=self.SubFunc.FindGainOffset(value,gvar.DraDcHCalPoint,gvar.DraDcHGain,gvar.DraDcHOffset)
            # self.SubFunc.SelSrc('DCVx5')
            # print('high range={}'.format(SourceV))


        self.SubFunc.SetDAC('CH1',value,SourceV)

    def SetDrbDcSrc(self,value):
        SourceV=self.SubFunc.FindGainOffset(value,gvar.DrbCalPoint,gvar.DrbGain,gvar.DrbOffset)
        self.SubFunc.SetDr2Rly('DCV','ON')
        self.SubFunc.SetDAC('CH3',SourceV,SourceV)

    def SetCCSClampV(self,value):
        SourceV=self.SubFunc.FindGainOffset(value,gvar.CCSCvCalPoint,gvar.CCSCvGain,gvar.CCSCvOffset)
        self.SubFunc.SetDAC('CH4',SourceV,SourceV)

    def SetCCS(self,CURR):

        DictCCS={
            '100mA' : [ 3,    2,    '10R'  , gvar.CCSCal[0]],
            '20mA'  : [ 4,    2,    '100R' , gvar.CCSCal[1]],
            '10mA'  : [ 3,    2,    '100R' , gvar.CCSCal[2]],
            '5mA'   : [ 2.5,  2,    '100R' , gvar.CCSCal[3]],
            '2.5mA' : [ 2.25, 2,    '100R' , gvar.CCSCal[4]],
            '1mA'   : [ 3 ,   2,    '1K'   , gvar.CCSCal[5]],
            '0.5mA' : [ 2.5,  2,    '1K'   , gvar.CCSCal[6]],
            '0.25mA': [ 2.25, 2,    '1K'   , gvar.CCSCal[7]],
            '0.1mA' : [ 3,    2,    '10K'  , gvar.CCSCal[8]],
            '50uA'  : [ 2.5,  2,    '10K'  , gvar.CCSCal[9]],
            '25uA'  : [ 2.25, 2,    '10K'  , gvar.CCSCal[10]],
            '10uA'  : [ 3,    2,    '100K' , gvar.CCSCal[11]],
            '5uA'   : [ 2.5,  2,    '100K' , gvar.CCSCal[12]],
            '2.5uA' : [ 2.25, 2,    '100K' , gvar.CCSCal[13]],
            '1uA'   : [ 3,    2,    '1M'   , gvar.CCSCal[14]],
            '0.1uA' : [ 2.1,  2,    '1M'   , gvar.CCSCal[15]],
            '0mA'   : [ 0,    0,    '1M'   , gvar.CCSCal[15]]
        }
        
        self.SubFunc.SelDr1Res(DictCCS[CURR][2])
        self.SetCCSClampV(DictCCS[CURR][1])
        self.SetDraDcSrc(DictCCS[CURR][0])

        self.SubFunc.SetDr1OutRly('GNDSP','ON')

        if (CURR=='0mA'):
            self.SubFunc.SetDr1OutRly('CCSMP','OFF')   
        else:
            self.SubFunc.SetDr1OutRly('CCSMP','ON')
            self.SubFunc.SetDr1OutRly('CCSEN','ON')


        return DictCCS[CURR][3]



