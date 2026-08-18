# -*- coding: utf-8 -*-
# Self_Cal.py — 不依賴 Keithley 2460 的自校正腳本
# 基準: 板上 +2.5VREF / -2.5VREF / GND (MUX5 0x1400 / 0x1800 / 0x0000)
#
# 用法:
#   python Self_Cal.py            # 跑全部步驟 1~6
#   python Self_Cal.py 3          # 從步驟3跑到6
#   python Self_Cal.py 2 4       # 只跑步驟2~4
#
# 步驟:
#   1 ADC self-cal      (GND/±2.5VREF 三點, 寫滿9段, ±2.5外為線性外插)
#   2 MUX offset        (MUX1=AGND, 7組合)
#   3 MUX gain          (DRA raw源+ADC比值法, 取代2460)
#   4 SRC DC            (DRA-L直讀 / DRA-H與DRB經MUX5 -0.5X摺回ADC範圍)
#   5 CCS Clamp V       (經MUX1=DR1OUT讀鉗位輸出)
#   6 ATT gain + offset (治具loopback MP<->MS, 只需MCU不需2460)
#
# 不包含: CCS電流(需外部電流表), ATT五點分段表(需外部精準源), AC校正, ±2.5VREF本身
#
# 注意: 所有精度追溯到板上±2.5VREF的實際準度, 適合修正漂移(如ADC溫漂),
#       正式出廠校正仍應使用 Run_All_Cal.py + 2460。

import os
import sys
if getattr(sys, 'frozen', False):
    current_script_directory = os.path.dirname(sys.executable)
else:
    current_script_directory = os.path.dirname(__file__)
sys.path.append(current_script_directory)
import time
from LCR_FUN import Func
from LCR_ADC import ADCFunc
from LCR_CAL import CalFunc
import gvar
from Run_All_Cal import StartLog, Rearm, CalLimitError


def RefVolt():
    # 取基準電壓: EEPROM有CalRefV量過的值就用, 否則用標稱±2.5
    refP, refN = 2.5, -2.5
    try:
        p = float(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.PP2V5RefAddr)))
        n = float(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.PN2V5RefAddr)))
        if 2.49 < p < 2.51:
            refP = p
        if -2.51 < n < -2.49:
            refN = n
    except Exception:
        pass
    return refP, refN


class SelfCal:
    def __init__(self):
        self.F = Func()
        self.ADC = ADCFunc()
        self.CAL = CalFunc(None)   # 只用到不需scpi的方法(MuxOffsetCal)

    # ---------- 共用 ----------
    def _rawAdc(self, n=3):
        vals = [self.ADC.ADC(1000, 'DC') for _ in range(n)]
        return sum(vals) / n

    def _calAdc(self, n=3):
        vals = [self.ADC.AdcMv(cnt=2500, type='DC', cal='Y') for _ in range(n)]
        return sum(vals) / n

    def _reloadAdcCal(self):
        self.ADC.AdcGain, self.ADC.AdcOffset = self.F.ReadCalData(
            gvar.AdcCalPoint, gvar.AdcGainAddr, gvar.AdcOffAddr)

    def _reloadMuxOff(self):
        for k, a in (('PASS', gvar.MuxOffPassAddr), ('2X', gvar.MuxOff2XAddr),
                     ('4X', gvar.MuxOff4XAddr), ('12X', gvar.MuxOff12XAddr),
                     ('36X', gvar.MuxOff36XAddr), ('0.2X', gvar.MuxOff02XAddr),
                     ('-0.5X', gvar.MuxOff05XAddr)):
            v = float(gvar.EthCmd('atk_eep_r_f_{}'.format(a)))
            gvar.MUXOFF[k] = v if -0.01 < v < 0.01 else 0.0

    def _measNeg05(self):
        # 經 MUX5 -0.5X 摺回ADC範圍的讀值還原成輸入電壓
        mv = self._calAdc()
        return (mv - gvar.MUXOFF['-0.5X']) / gvar.MUXG05

    # ---------- 1. ADC self-cal ----------
    def AdcSelfCal(self):
        print('ADC Self Calibration Start.....\r\n')
        refP, refN = RefVolt()
        print('RefP={} RefN={}'.format(refP, refN))

        self.F.SysARST()
        self.F.SetMux1('AGND')   # 前段接地, 只留MUX5選基準
        self.F.SetMux2('PASS')
        self.F.SetMux3('PASS')
        self.F.SetMux4('PASS')

        raws = {}
        for name in ('GND', '+2.5VREF', '-2.5VREF'):
            self.F.SetMux5(name)
            time.sleep(0.2)
            raws[name] = self._rawAdc()
            print('RAW[{}] = {:.6f}'.format(name, raws[name]))

        rawG, rawP, rawN = raws['GND'], raws['+2.5VREF'], raws['-2.5VREF']
        if not (2.3 < rawP < 2.7 and -2.7 < rawN < -2.3 and -0.1 < rawG < 0.1):
            raise CalLimitError('REF raw reading abnormal: {}'.format(raws))

        gP = (refP - 0.0) / (rawP - rawG)
        oP = 0.0 - rawG * gP
        gN = (0.0 - refN) / (rawG - rawN)
        oN = 0.0 - rawG * gN
        print('PosFit gain={:.6f} offset={:.6f}'.format(gP, oP))
        print('NegFit gain={:.6f} offset={:.6f}'.format(gN, oN))

        gains, offs = [], []
        cp = gvar.AdcCalPoint
        for i in range(len(cp) - 1):
            mid = (cp[i] + cp[i+1]) / 2.0
            g, o = (gN, oN) if mid < 0 else (gP, oP)
            gains.append('{:.8f}'.format(g))
            offs.append('{:.8f}'.format(o))
        self.F.WriteRom(gvar.AdcGainAddr, gvar.AdcOffAddr, cp, gains, offs)
        self._reloadAdcCal()

        print('ADC Self Calibration Check.....\r\n')
        ok = True
        for name, expect in (('GND', 0.0), ('+2.5VREF', refP), ('-2.5VREF', refN)):
            self.F.SetMux5(name)
            time.sleep(0.2)
            v = self._calAdc()
            err = v - expect
            res = 'PASS' if abs(err) < 0.003 else 'FAIL'
            ok = ok and res == 'PASS'
            print('CHK[{}] = {:.6f} (err={:+.4f}mV) ({})'.format(
                name, v, err * 1000, res))
        self.F.SysARST()
        if not ok:
            raise CalLimitError('ADC self-cal check fail')
        print('ADC Self Calibration End.....\r\n')

    # ---------- 3. MUX gain (ADC比值法) ----------
    def MuxGainSelfCal(self):
        print('MUX Gain Self Calibration Start.....\r\n')
        self.F.SysARST()
        self.F.SelSrc('DCV')
        self.F.SelDr1Res('PASS')
        self.F.SetMux1('DR1BUF')
        self.F.SetMux2('PASS')
        self.F.SetMux3('PASS')
        self.F.SetMux4('PASS')
        self.F.SetMux5('PASS')

        def meas(key):
            time.sleep(0.2)
            return self._calAdc() - gvar.MUXOFF[key]

        self.F.SetDAC('CH1', 0.2, 0.2)
        base = meas('PASS')

        self.F.SetMux2('2X');  v2 = meas('2X')
        self.F.SetMux2('4X');  v4 = meas('4X')
        self.F.SetMux2('12X'); v12 = meas('12X')

        self.F.SetMux2('PASS')
        self.F.SetDAC('CH1', 0.02, 0.02)
        base002 = meas('PASS')
        self.F.SetMux2('36X'); v36 = meas('36X')

        # 0.2X / -0.5X 用 2V 訊號 (輸出0.4V/1.0V, 兼顧解析度與ADC範圍)
        self.F.SetMux2('PASS')
        self.F.SetDAC('CH1', 2.0, 2.0)
        base2 = meas('PASS')
        self.F.SetMux2('0.2X'); v02 = meas('0.2X')
        self.F.SetMux2('PASS')
        self.F.SetMux5('-0.5X'); v05 = meas('-0.5X')

        results = [
            ('MuxG2',   v2 / base,     1.95, 2.05,     gvar.MUXGain2Addr,    'MUXG2'),
            ('MuxG4',   v4 / base,     3.95, 4.05,     gvar.MUXGain4Addr,    'MUXG4'),
            ('MuxG12',  v12 / base,    11.93, 12.05,   gvar.MUXGain12Addr,   'MUXG12'),
            ('MuxG36',  v36 / base002, 34.5, 36.5,     gvar.MUXGain36Addr,   'MUXG36'),
            ('MuxGn02', v02 / base2,   -0.202, -0.198, gvar.MUXGainN0P2Addr, 'MUXG02'),
            ('MuxGn05', v05 / base2,   -0.502, -0.498, gvar.MUXGainN0P5Addr, 'MUXG05'),
        ]
        for name, g, lo, hi, addr, attr in results:
            print('{}={}'.format(name, g))
            if lo < g < hi:
                gvar.EthCmd('atk_eep_w_f_{}_{}'.format(addr, g))
                setattr(gvar, attr, g)   # 後續步驟立即使用新值
            else:
                print('Fail, {} Out of Range'.format(name))
        self.F.SetDAC('CH1', 0, 0)
        self.F.SysARST()
        print('MUX Gain Self Calibration End.....\r\n')

    # ---------- 4. SRC DC ----------
    def _srcCal(self, title, calPoint, addrG, addrO, setter, measure):
        print('{} Self Calibration Start.....\r\n'.format(title))
        setV, measV = [], []
        for v in calPoint:
            setter(v)
            time.sleep(0.2)
            m = measure()
            setV.append(v)
            measV.append(m)
            print('SRC= {}'.format(v))
            print('MEAS = {:.6f}\r\n'.format(m))
        slope, off = self.F.SlopeOffset(setV, measV, 1, 0)
        for s in slope:   # 合理性: 源增益應接近1
            if not 0.9 < float(s) < 1.1:
                print('Fail, {} slope {} out of range, NOT written'.format(title, s))
                self.F.SysARST()
                raise CalLimitError('{} slope abnormal: {}'.format(title, s))
        self.F.WriteRom(addrG, addrO, calPoint, slope, off)
        self.F.SysARST()
        print('{} Self Calibration End.....\r\n'.format(title))

    def DraLSelfCal(self):
        self.F.SelSrc('DCV')
        self.F.SelDr1Res('PASS')
        self.F.SetMux1('DR1BUF')
        self.F.SetMux2('PASS'); self.F.SetMux3('PASS')
        self.F.SetMux4('PASS'); self.F.SetMux5('PASS')
        self._srcCal('SRC1 1x', gvar.DraDcLCalPoint,
                     gvar.DraDcLGainAddr, gvar.DraDcLOffAddr,
                     lambda v: self.F.SetDAC('CH1', v, v),
                     lambda: self._calAdc() - gvar.MUXOFF['PASS'])

    def DraHSelfCal(self):
        self.F.SelSrc('DCVx5')
        self.F.SelDr1Res('PASS')
        self.F.SetMux1('DR1BUF')
        self.F.SetMux2('PASS'); self.F.SetMux3('PASS')
        self.F.SetMux4('PASS'); self.F.SetMux5('-0.5X')
        self._srcCal('SRC1 5x', gvar.DraDcHCalPoint,
                     gvar.DraDcHGainAddr, gvar.DraDcHOffAddr,
                     lambda v: self.F.SetDAC('CH1', v, v),
                     self._measNeg05)

    def DrbSelfCal(self):
        self.F.SetDr2Rly('DCV', 'ON')
        self.F.SetDr2Res('PASS')
        self.F.SetMux1('DR2BUF')
        self.F.SetMux2('PASS'); self.F.SetMux3('PASS')
        self.F.SetMux4('PASS'); self.F.SetMux5('-0.5X')
        self._srcCal('SRC2', gvar.DrbCalPoint,
                     gvar.DrbGainAddr, gvar.DrbOffAddr,
                     lambda v: self.F.SetDAC('CH3', v, v),
                     self._measNeg05)

    # ---------- 5. CCS Clamp V ----------
    def ClampVSelfCal(self):
        self.F.SelSrc('DCVx5')
        self.F.SelDr1Res('1K')
        self.F.SetDr1OutRly('CCSEN', 'ON')
        self.F.SetDr1OutRly('CCSMP', 'ON')
        self.F.SetMux1('DR1OUT')
        self.F.SetMux2('PASS'); self.F.SetMux3('PASS')
        self.F.SetMux4('PASS'); self.F.SetMux5('-0.5X')

        def setter(v):
            self.F.SetDAC('CH4', v, v)
            self.F.SetDAC('CH1', v + 1, v + 1)
        self._srcCal('CCS ClampV', gvar.CCSCvCalPoint,
                     gvar.CCSCvGainAddr, gvar.CCSCvOffAddr,
                     setter, self._measNeg05)

    # ---------- 6. ATT gain + offset (治具loopback) ----------
    def AttSelfCal(self):
        print('ATT Self Calibration Start.....\r\n')
        gvar.MCUCmd('atk_frst_high')
        # MP<->MS / SP<->SS 經治具母線loopback (不接2460)
        self.F.SetCalSmuRly('SMU_P_MP', 'ON')
        self.F.SetCalSmuRly('SMU_P_MS', 'ON')
        self.F.SetCalSmuRly('SMU_N_SP', 'ON')
        self.F.SetCalSmuRly('SMU_N_SS', 'ON')
        self.F.SetDr1OutRly('GNDSP', 'ON')
        self.F.SetDr1OutRly('GNDGP', 'ON')
        self.F.SetDr1OutRly('DR1MP', 'ON')
        self.F.SetExPortRly('MP', 'ON')
        self.F.SetExPortRly('MS', 'ON')
        self.F.SetExPortRly('SS', 'ON')

        self.F.SelSrc('DCVx5')
        self.F.SelDr1Res('PASS')
        from LCR_SRC import LCRSrc
        SRC = LCRSrc()
        SRC.SetDraDcSrc(5)

        # 源電壓: DR1BUF經-0.5X讀 (5V摺成2.5V)
        self.F.SetMux1('DR1BUF')
        self.F.SetMux2('PASS'); self.F.SetMux3('PASS')
        self.F.SetMux4('PASS'); self.F.SetMux5('-0.5X')
        time.sleep(0.2)
        src = self._measNeg05()
        print('SRC(5V) = {:.6f}'.format(src))

        results = []
        for name, hp, lp, lo, hi, addr in (
                ('ATTD05Gain', gvar.ATT_HP_D5, gvar.ATT_LP_D5, 0.198, 0.202, gvar.ATTD5Addr),
                ('ATTD10Gain', gvar.ATT_HP_D10, gvar.ATT_LP_D10, 0.098, 0.102, gvar.ATTD10Addr)):
            self.F.SetAtt1Rly('ALL', 'OFF')
            ATTPATH = gvar.ATT_HP_MS | hp | gvar.ATT_LP_SS | lp
            self.F.SetATT(ATTPATH)
            MUXPATH = (gvar.MUX1_ATT | gvar.MUX2_PASS | gvar.MUX3_PASS |
                       gvar.MUX4_PASS | gvar.MUX5_NG05)
            self.F.SetMUX(MUXPATH)
            time.sleep(0.2)
            att_v = self._measNeg05()
            gain = abs(att_v / src)
            print('{}={}'.format(name, gain))
            if lo < gain < hi:
                gvar.EthCmd('atk_eep_w_f_{}_{}'.format(addr, gain))
            else:
                print('Fail, {} Out of Range'.format(name))
            results.append(gain)

        # ATT path offset: 源設0V+接GND, D10路徑ADC端殘餘 (與ATTGainCal存法相同)
        SRC.SetDraDcSrc(0)
        self.F.SelSrc('GND')
        time.sleep(0.2)
        att_off = self._calAdc()
        print('ATTPathOff={}'.format(att_off))
        if -0.01 < att_off < 0.01:
            gvar.EthCmd('atk_eep_w_f_{}_{}'.format(gvar.ATTPathOffAddr, att_off))
        else:
            print('Fail, ATT Path Offset Out of Range')

        self.F.SetAtt1Rly('ALL', 'OFF')
        self.F.SysARST()
        self.F.SetCalSmuRly('SMU_P_MP', 'OFF')
        self.F.SetCalSmuRly('SMU_P_MS', 'OFF')
        self.F.SetCalSmuRly('SMU_N_SP', 'OFF')
        self.F.SetCalSmuRly('SMU_N_SS', 'OFF')
        print('ATT Self Calibration End.....\r\n')


def main():
    startStep = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    endStep = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    tee = StartLog()
    print('=== SELF CAL (no 2460) === Ref: on-board +/-2.5VREF & GND\r\n')
    sc = SelfCal()
    ATKRly = sc.F
    t0 = time.time()
    try:
        if startStep <= 1 <= endStep:
            print('\r\n========== Step 1/6 : ADC Self Cal ==========\r\n')
            Rearm(ATKRly)
            sc.AdcSelfCal()

        if startStep <= 2 <= endStep:
            print('\r\n========== Step 2/6 : MUX Offset ==========\r\n')
            Rearm(ATKRly)
            sc.CAL.MuxOffsetCal()
            sc._reloadMuxOff()

        if startStep <= 3 <= endStep:
            print('\r\n========== Step 3/6 : MUX Gain Self Cal ==========\r\n')
            Rearm(ATKRly)
            sc.MuxGainSelfCal()

        if startStep <= 4 <= endStep:
            print('\r\n========== Step 4/6 : SRC DC Self Cal ==========\r\n')
            Rearm(ATKRly)
            sc.DraLSelfCal()
            Rearm(ATKRly)
            sc.DraHSelfCal()
            Rearm(ATKRly)
            sc.DrbSelfCal()

        if startStep <= 5 <= endStep:
            print('\r\n========== Step 5/6 : CCS ClampV Self Cal ==========\r\n')
            Rearm(ATKRly)
            sc.ClampVSelfCal()

        if startStep <= 6 <= endStep:
            print('\r\n========== Step 6/6 : ATT Self Cal ==========\r\n')
            Rearm(ATKRly)
            sc.AttSelfCal()

        print('\r\n========== Self Cal Done ({}~{}), {:.1f}s =========='.format(
            startStep, endStep, time.time() - t0))
    except CalLimitError as e:
        print('\r\n!!!!! SELF CAL STOPPED !!!!!')
        print('{}'.format(e))
        raise
    finally:
        try:
            sc.F.SysARST()
        except Exception:
            pass
        tee.close()


if __name__ == '__main__':
    import traceback
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
