# -*- coding: utf-8 -*-
# Run_All_Cal.py
# 一鍵執行 SMU_Test.py 中 #1~#6 全部校正步驟
# 用法:
#   python Run_All_Cal.py            # 從步驟1跑到步驟6
#   python Run_All_Cal.py 3          # 從步驟3開始跑到步驟6
#   python Run_All_Cal.py 2 4        # 只跑步驟2~4
#
# 硬體需求:
#   1. Keithley 2460 SMU 接 TCPIP 169.254.10.222 (標準儀器)
#   2. T1000 SMU 板接乙太網路 169.254.10.101:7600 (gvar.py 內設定)
#   3. MCU 治具串口名稱 SMU_CALB (gvar.py 自動偵測)
#   4. 校正治具線材依 SetCalSmuRly 路徑接妥

import os
import sys
if getattr(sys, 'frozen', False):
    current_script_directory = os.path.dirname(sys.executable)  # exe模式: log跟著exe放
else:
    current_script_directory = os.path.dirname(__file__)
sys.path.append(current_script_directory)
import re
import time
from datetime import datetime
# import pyvisa
from K2460 import GPIB
from LCR_CAL import CalFunc
from LCR_FUN import Func
from LCR_ADC import ADCFunc
import gvar


SMU = 'TCPIP0::169.254.10.222::inst0::INSTR'
# SMU = 'GPIB0::5::INSTR'
# SMU = 'USB0::0x05E6::0x2460::04590124::INSTR'


def ReloadCalData(ATKCal):
    # 步驟1~3把新的校正值寫進EEPROM後, 重新讀回來給步驟4~6使用
    # (等效於原本手動改 gvar.py CalEn=0 -> CalEn=1 再重跑一次)
    print('Reload calibration data from EEPROM.....\r\n')
    gvar.MUXG2  = float(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.MUXGain2Addr)))
    gvar.MUXG4  = float(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.MUXGain4Addr)))
    gvar.MUXG12 = float(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.MUXGain12Addr)))
    gvar.MUXG36 = float(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.MUXGain36Addr)))
    gvar.MUXG02 = float(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.MUXGainN0P2Addr)))
    gvar.MUXG05 = float(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.MUXGainN0P5Addr)))

    gvar.ADCGain      = gvar.ReadCalData(len(gvar.AdcCalPoint)-1, gvar.AdcGainAddr)
    gvar.ADCOffset    = gvar.ReadCalData(len(gvar.AdcCalPoint)-1, gvar.AdcOffAddr)
    gvar.DraDcLGain   = gvar.ReadCalData(len(gvar.DraDcLCalPoint)-1, gvar.DraDcLGainAddr)
    gvar.DraDcLOffset = gvar.ReadCalData(len(gvar.DraDcLCalPoint)-1, gvar.DraDcLOffAddr)
    gvar.DraDcHGain   = gvar.ReadCalData(len(gvar.DraDcHCalPoint)-1, gvar.DraDcHGainAddr)
    gvar.DraDcHOffset = gvar.ReadCalData(len(gvar.DraDcHCalPoint)-1, gvar.DraDcHOffAddr)
    gvar.DrbGain      = gvar.ReadCalData(len(gvar.DrbCalPoint)-1, gvar.DrbGainAddr)
    gvar.DrbOffset    = gvar.ReadCalData(len(gvar.DrbCalPoint)-1, gvar.DrbOffAddr)
    gvar.CCSCvGain    = gvar.ReadCalData(len(gvar.CCSCvCalPoint)-1, gvar.CCSCvGainAddr)
    gvar.CCSCvOffset  = gvar.ReadCalData(len(gvar.CCSCvCalPoint)-1, gvar.CCSCvOffAddr)

    # ADCFunc 在建構時才讀 ADC gain/offset, 重讀一次讓後續 AdcMv 用新校正值
    ATKCal.ADC.AdcGain, ATKCal.ADC.AdcOffset = ATKCal.ADC.SubFunc.ReadCalData(
        gvar.AdcCalPoint, gvar.AdcGainAddr, gvar.AdcOffAddr)


CAL_LIMIT_PCT = 25.0     # 校正點(未校正的raw值)誤差超過25%判FAIL停止: 抓路徑錯亂
CHECK_LIMIT_PCT = 10.0   # 驗證點(校正後)誤差超過10%判FAIL停止
ERR_FLOOR = 0.001        # 絕對誤差低於0.001(V/mA)不觸發停止:
                         # 避開近零點(相對誤差無意義)與CCS 0.1uA檔(設計值~0.135uA)


class CalLimitError(Exception):
    pass


def _CurrNum(s):
    # '100mA'/'-49.36uA'/'135nA'/'-2'/'0.1' -> (數值, 是否帶電流單位); 電流一律換算成mA
    m = re.match(r'^(-?\d+\.?\d*(?:[eE][+-]?\d+)?)(mA|uA|nA)?$', s.strip())
    if not m:
        return None, False
    v = float(m.group(1))
    u = m.group(2)
    if u == 'uA':
        v /= 1000.0
    elif u == 'nA':
        v /= 1000000.0
    return v, u is not None


class CsvLog:
    # 把校正輸出逐行解析成結構化CSV欄位, 無法解析的行以MSG保留原文
    # Err/Err% 誤差比對: Step1=ADC vs Meter, Step2/3=Meter vs Set, Step4=實測 vs 檔位
    HEADER = ['Time', 'Step', 'Section', 'Item', 'Label',
              'Set', 'Meter', 'ADC', 'Value', 'Err', 'Err%', 'Result', 'Raw']

    def __init__(self, csvPath):
        import csv
        self.fd = open(csvPath, 'w', newline='', encoding='utf-8-sig')  # BOM讓Excel正確顯示
        self.csv = csv.writer(self.fd)
        self.csv.writerow(self.HEADER)
        self.fd.flush()
        self.step = ''
        self.section = ''
        self.pendSet = ''    # SRC=/SetV=/CLAMPV=/Setting Current= 暫存
        self.pendMeter = ''  # ADC1Cal 的 Meter MV 暫存
        self.pendAddr = ''   # CCS Write Addr 暫存

    def row(self, item='', label='', set_='', meter='', adc='',
            value='', result='', raw=''):
        err, errp, refabs = self._error(set_, meter, adc)
        limit = CHECK_LIMIT_PCT if item == 'Check' else CAL_LIMIT_PCT
        # 參考值太小(近零點)時相對誤差無意義, 不觸發停止
        overLimit = (err != '' and refabs >= 0.05
                     and abs(float(errp)) > limit
                     and abs(float(err)) > ERR_FLOOR)
        if overLimit and not result:
            result = 'FAIL'
        # CSV只留重點: Check驗證點(PASS/FAIL)與任何FAIL列; 完整輸出在同名.log
        if item == 'Check' or result == 'FAIL':
            self.csv.writerow([datetime.now().strftime('%H:%M:%S'), self.step,
                               self.section, item, label, set_, meter, adc,
                               value, err, errp, result, raw])
            self.fd.flush()
        if overLimit:
            raise CalLimitError(
                'Error over {}% limit -> Step{} {} Set={} Meter={} ADC={} '
                'Err={} Err%={}'.format(limit, self.step, self.section,
                                        set_, meter, adc, err, errp))

    @staticmethod
    def _error(set_, meter, adc):
        # 挑參考值與量測值算誤差: 有ADC比Meter, 否則Meter比Set
        if adc and meter:
            ref, meas = _CurrNum(meter), _CurrNum(adc)
        elif meter and set_:
            ref, meas = _CurrNum(set_), _CurrNum(meter)
        else:
            return '', '', 0.0
        if ref[0] is None or meas[0] is None or ref[0] == 0:
            return '', '', 0.0
        if ref[1] or meas[1]:
            # 電流(CCS為灌入方向, 量測為負): 比大小不比方向, 誤差單位mA
            diff = abs(meas[0]) - abs(ref[0])
        else:
            diff = meas[0] - ref[0]
        errp = diff / abs(ref[0]) * 100
        return '{:.6g}'.format(diff), '{:.3f}'.format(errp), abs(ref[0])

    def feed(self, line):
        line = line.strip()
        if not line:
            return

        m = re.match(r'=+\s*Step (\d)/6 : (.+?) =+', line)
        if m:
            self.step = m.group(1)
            self.section = m.group(2).strip()
            self.row(item='MSG', raw=line)
            return
        m = re.match(r'(.+?) Calibration (Start|Check)\.*', line)
        if m:
            self.section = m.group(1).strip() + (
                ' Check' if m.group(2) == 'Check' else '')
            self.row(item='MSG', raw=line)
            return

        m = re.match(r'(?:SRC|SetV|CLAMPV|Setting Current)\s*=\s*(\S+)', line)
        if m:
            self.pendSet = m.group(1)
            return
        m = re.match(r'Meter MV\s*=\s*(\S+)', line)
        if m:
            self.pendMeter = m.group(1)
            return
        m = re.match(r'DMM\s*=\s*(\S+)', line)
        if m:
            self.row(item='Cal', set_=self.pendSet, meter=m.group(1))
            self.pendSet = ''
            return
        m = re.match(r'ADC MV\s*=\s*(\S+)(?:\s*\((PASS|FAIL)\))?', line)
        if m:
            self.row(item='Check' if m.group(2) else 'Cal',
                     set_=self.pendSet, meter=self.pendMeter,
                     adc=m.group(1), result=m.group(2) or '')
            self.pendSet = self.pendMeter = ''
            return
        m = re.match(r'Measure Curr(?:ne|en)t\s*=\s*(\S+?(?:mA|uA|nA))', line)
        if m:
            self.row(item='Cal', set_=self.pendSet, meter=m.group(1))
            self.pendSet = ''
            return

        m = re.match(r'(Gain|Offset)\[\s*(.+?)\s*\]\s*=\s*(\S+)', line)
        if m:
            self.row(item=m.group(1), label=m.group(2).replace(' ', ''),
                     value=m.group(3))
            return
        m = re.match(r'(MuxOff\S*?)\s*=\s*(\S+)', line)
        if m:
            self.row(item='MuxOffset', label=m.group(1), value=m.group(2))
            return
        m = re.match(r'(MuxG\S*?)\s*=\s*(\S+)', line)
        if m:
            self.row(item='MuxGain', label=m.group(1), value=m.group(2))
            return
        m = re.match(r'(ATTD\d+Gain)\s*=\s*(\S+)', line)
        if m:
            self.row(item='ATTGain', label=m.group(1), value=m.group(2))
            return
        m = re.match(r'(DMM[12])\s*=\s*(\S+)', line)
        if m:
            self.row(item='Cal', label=m.group(1), meter=m.group(2))
            return

        m = re.match(r'CCS Write Addr\s*=\s*(\S+)', line)
        if m:
            self.pendAddr = m.group(1)
            return
        m = re.match(r'Read From EEPROM\s*=\s*(\S+)', line)
        if m:
            self.row(item='EEPROM', label=self.pendAddr, value=m.group(1))
            self.pendAddr = ''
            return

        result = 'FAIL' if ('Fail' in line or 'Out Of Limit' in line
                            or 'Error' in line or 'Traceback' in line) else ''
        self.row(item='MSG', result=result, raw=line)

    def close(self):
        self.fd.close()


class Tee:
    # 螢幕照常輸出, 完整原始輸出寫 .log, 重點(Check/FAIL)解析後寫 CSV
    def __init__(self, csvPath):
        self.term = sys.stdout
        self.csvlog = CsvLog(csvPath)
        self.rawfd = open(os.path.splitext(csvPath)[0] + '.log',
                          'w', encoding='utf-8')
        self.buf = ''

    def write(self, msg):
        self.term.write(msg)
        self.rawfd.write(msg)
        self.buf += msg
        while '\n' in self.buf:
            line, self.buf = self.buf.split('\n', 1)
            self.csvlog.feed(line)

    def flush(self):
        self.term.flush()
        self.rawfd.flush()

    def close(self):
        if self.buf.strip():
            self.csvlog.feed(self.buf)
            self.buf = ''
        sys.stdout = self.term
        sys.stderr = self.term
        self.csvlog.close()
        self.rawfd.close()


def StartLog():
    logDir = os.path.join(current_script_directory, 'log')
    os.makedirs(logDir, exist_ok=True)
    logPath = os.path.join(logDir, datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv')
    tee = Tee(logPath)
    sys.stdout = tee
    sys.stderr = tee
    try:
        from version import __version__
        print('Tool Ver: {}'.format(__version__))
    except ImportError:
        pass
    print('Log file: {}'.format(logPath))
    print('Start   : {}\r\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    return tee


def Rearm(ATKRly):
    # 每個校正函式結尾的 SysARST 會把 FPGA 繼電器全部復位,
    # 但 gvar 的 shadow 變數不會歸零 → 下一步會 OR 進舊 bits, 路徑錯位;
    # always-on 的 GNDSP/GNDGP 接地回路也會被關掉 (fail.log DrbCal 亂掉的原因)。
    # 所以每個校正步驟前: shadow 歸零 + 重開 always-on 繼電器。
    gvar.Dr1LchData = 0
    gvar.MoaLchData = 0
    gvar.Att1LchData = 0
    gvar.DisLchData = 0
    gvar.Dr2LchData = 0
    gvar.Mux1Lch1Data = 0
    gvar.ExtLchData = 0
    ATKRly.SetDr1OutRly('GNDSP', 'ON')
    ATKRly.SetDr1OutRly('GNDGP', 'ON')


def CalRlyOn(ATKRly):
    # ----------For System Calibration----------------(always on)
    gvar.MCUCmd('atk_frst_high')   # 治具 enable, 沒送這條繼電器不會動作
    ATKRly.SetCalSmuRly('SMU_P_MP', 'ON')
    ATKRly.SetCalSmuRly('SMU_N_SP', 'ON')
    ATKRly.SetCalSmuRly('SMU_N_GP', 'ON')
    ATKRly.SetDr1OutRly('GNDSP', 'ON')
    ATKRly.SetDr1OutRly('GNDGP', 'ON')


def CalRlyAllOff(ATKRly):
    offList = [
        (ATKRly.SetCalSmuRly, 'SMU_P_MP'),
        (ATKRly.SetCalSmuRly, 'SMU_N_SP'),
        (ATKRly.SetCalSmuRly, 'SMU_N_GP'),
        (ATKRly.SetDr1OutRly, 'GNDSP'),
        (ATKRly.SetDr1OutRly, 'GNDGP'),
        (ATKRly.SetCalSmuRly, 'SMU_P_MS'),
        (ATKRly.SetCalSmuRly, 'SMU_N_SS'),
    ]
    for fn, rly in offList:
        try:
            fn(rly, 'OFF')
        except Exception as e:
            print('Relay OFF fail: {} ({})'.format(rly, e))


def RunCal(startStep=1, endStep=6, smuName=None):
    if smuName is None:
        smuName = SMU

    tee = StartLog()   # log/時間戳.log, 全程輸出(含錯誤)都會記錄
    print('2460 resource : {}'.format(smuName))
    print('SMU board IP  : {}:{}'.format(gvar.IP, gvar.PORT))
    print('MCU port      : {}\r\n'.format(gvar.McuSerialName))

    scpi = GPIB(smuName)
    ATKFunc = Func()
    ATKRly = Func()
    ATKCal = CalFunc(scpi)

    ATKFunc.SysARST()
    ATKFunc.Version()

    CalRlyOn(ATKRly)

    t0 = time.time()
    try:
        # =========1. ADC Calibration===========
        if startStep <= 1 <= endStep:
            print('\r\n========== Step 1/6 : ADC1 Calibration ==========\r\n')
            Rearm(ATKRly)
            ATKCal.ADC1Cal()

        # =========2. DRA/DRB DC Calibration===========
        if startStep <= 2 <= endStep:
            print('\r\n========== Step 2/6 : SRC DC Calibration ==========\r\n')
            Rearm(ATKRly)
            ATKCal.DraLDcCal()
            Rearm(ATKRly)
            ATKCal.DraHDcCal()
            Rearm(ATKRly)
            ATKCal.DrbCal()

        # =========3. CCS Clamp V===========
        if startStep <= 3 <= endStep:
            print('\r\n========== Step 3/6 : CCS Clamp V Calibration ==========\r\n')
            Rearm(ATKRly)
            ATKCal.CCSClampVCal()

        # =======原手動步驟: gvar.py CalEn=0 -> CalEn=1, 改為重新載入=======
        ReloadCalData(ATKCal)

        # =========4. CCS Calibration===========
        if startStep <= 4 <= endStep:
            print('\r\n========== Step 4/6 : CCS Calibration ==========\r\n')
            Rearm(ATKRly)
            ATKCal.CCSCal()
            # CCSCal 結尾會 gpibClose() 關掉 2460 連線, 重開避免下一步 InvalidSession
            scpi = GPIB(smuName)
            ATKCal.scpi = scpi

        # =========5. Write MUX Calibration===========
        if startStep <= 5 <= endStep:
            print('\r\n========== Step 5/6 : MUX Gain Calibration ==========\r\n')
            Rearm(ATKRly)
            ATKCal.CalMuxGain()
            # ATTGainCal 會用到剛寫入的 MUXG05, 重讀一次
            gvar.MUXG05 = float(gvar.EthCmd('atk_eep_r_f_{}'.format(gvar.MUXGainN0P5Addr)))
            # MUX路徑offset校正 (MUX1=AGND, 不需2460/治具)
            Rearm(ATKRly)
            ATKCal.MuxOffsetCal()

        # =========6. Cal Att Gain===========
        if startStep <= 6 <= endStep:
            print('\r\n========== Step 6/6 : ATT Gain Calibration ==========\r\n')
            Rearm(ATKRly)
            ATKRly.SetCalSmuRly('SMU_P_MS', 'ON')
            ATKRly.SetCalSmuRly('SMU_N_SS', 'ON')
            ATKCal.ATTGainCal()
            # ATT路徑分段表 (2460當源, 5點含0V, gain+offset一次校齊)
            Rearm(ATKRly)
            ATKCal.ATTPathCal()

        print('\r\n========== All Calibration Done ({}~{}), {:.1f}s =========='.format(
            startStep, endStep, time.time() - t0))
        print('End     : {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    except CalLimitError as e:
        print('\r\n!!!!! CALIBRATION STOPPED (Error Over Limit) !!!!!')
        print('{}'.format(e))
        print('End     : {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        raise
    finally:
        # 不論成功或中途出錯, 都關掉輸出與所有校正繼電器, 並收尾log
        try:
            scpi.gpibOff()
        except Exception:
            pass
        CalRlyAllOff(ATKRly)
        ATKFunc.SysARST()
        tee.close()


def main():
    startStep = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    endStep   = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    RunCal(startStep, endStep)


if __name__ == '__main__':
    import traceback
    try:
        main()
    except Exception:
        traceback.print_exc()   # sys.stderr 已導向 Tee, 錯誤也會進 log
        sys.exit(1)
