# -*- coding: utf-8 -*-
# Dump_Cal.py
# 把板子EEPROM內所有校正資料讀出, 印到螢幕並存 log/caldump_時間戳.csv
# 用法: python Dump_Cal.py

import os
import sys
if getattr(sys, 'frozen', False):
    current_script_directory = os.path.dirname(sys.executable)
else:
    current_script_directory = os.path.dirname(__file__)
sys.path.append(current_script_directory)
import csv
from datetime import datetime
import gvar


def RF(addr):
    return float(gvar.EthCmd('atk_eep_r_f_{}'.format(addr)))


def ReadArr(addrBase, length):
    vals = []
    a = int(addrBase, 16)
    for i in range(length):
        vals.append(RF(format(a, 'x')))
        a += 4
    return vals


def SegLabels(calPoint):
    return ['{}~{}'.format(calPoint[i], calPoint[i+1])
            for i in range(len(calPoint)-1)]


def main():
    rows = []   # (group, name, addr, value)

    def one(group, name, addr):
        rows.append((group, name, addr.upper(), RF(addr)))

    def arr(group, name, addrBase, labels):
        a = int(addrBase, 16)
        for lb in labels:
            rows.append((group, '{}[{}]'.format(name, lb), format(a, 'X'), RF(format(a, 'x'))))
            a += 4

    # ---- 單值 ----
    one('REF',  'PP2V5',  gvar.PP2V5RefAddr)
    one('REF',  'PN2V5',  gvar.PN2V5RefAddr)
    one('MUX',  'MUXG2',  gvar.MUXGain2Addr)
    one('MUX',  'MUXG4',  gvar.MUXGain4Addr)
    one('MUX',  'MUXG12', gvar.MUXGain12Addr)
    one('MUX',  'MUXG36', gvar.MUXGain36Addr)
    one('MUX',  'MUXG02', gvar.MUXGainN0P2Addr)
    one('MUX',  'MUXG05', gvar.MUXGainN0P5Addr)
    one('MUXOFF', 'MuxOffPass', gvar.MuxOffPassAddr)
    one('MUXOFF', 'MuxOff2X',   gvar.MuxOff2XAddr)
    one('MUXOFF', 'MuxOff4X',   gvar.MuxOff4XAddr)
    one('MUXOFF', 'MuxOff12X',  gvar.MuxOff12XAddr)
    one('MUXOFF', 'MuxOff36X',  gvar.MuxOff36XAddr)
    one('MUXOFF', 'MuxOff02X',  gvar.MuxOff02XAddr)
    one('MUXOFF', 'MuxOff05X',  gvar.MuxOff05XAddr)
    one('ACAMP', 'SrcAc100HZ',  gvar.SrcAcAmp100HZ)
    one('ACAMP', 'AdcAc100HZ',  gvar.AdcAcAmp100HZ)
    one('ACAMP', 'SrcAc1KHZ',   gvar.SrcAcAmp1KHZ)
    one('ACAMP', 'AdcAc1KHZ',   gvar.AdcAcAmp1KHZ)
    one('ACAMP', 'SrcAc10KHZ',  gvar.SrcAcAmp10KHZ)
    one('ACAMP', 'AdcAc10KHZ',  gvar.AdcAcAmp10KHZ)
    one('ACAMP', 'SrcAc100KHZ', gvar.SrcAcAmp100KHZ)
    one('ACAMP', 'AdcAc100KHZ', gvar.AdcAcAmp100KHZ)
    one('ATT',  'ATTD5Gain',  gvar.ATTD5Addr)
    one('ATT',  'ATTD10Gain', gvar.ATTD10Addr)
    one('ATT',  'ATTPathOff', gvar.ATTPathOffAddr)

    # ---- 分段陣列 (gain/offset) ----
    arr('ADC',   'Gain',   gvar.AdcGainAddr,   SegLabels(gvar.AdcCalPoint))
    arr('ADC',   'Offset', gvar.AdcOffAddr,    SegLabels(gvar.AdcCalPoint))
    arr('DRA_L', 'Gain',   gvar.DraDcLGainAddr, SegLabels(gvar.DraDcLCalPoint))
    arr('DRA_L', 'Offset', gvar.DraDcLOffAddr,  SegLabels(gvar.DraDcLCalPoint))
    arr('DRA_H', 'Gain',   gvar.DraDcHGainAddr, SegLabels(gvar.DraDcHCalPoint))
    arr('DRA_H', 'Offset', gvar.DraDcHOffAddr,  SegLabels(gvar.DraDcHCalPoint))
    arr('DRB',   'Gain',   gvar.DrbGainAddr,   SegLabels(gvar.DrbCalPoint))
    arr('DRB',   'Offset', gvar.DrbOffAddr,    SegLabels(gvar.DrbCalPoint))
    arr('CCSCV', 'Gain',   gvar.CCSCvGainAddr, SegLabels(gvar.CCSCvCalPoint))
    arr('CCSCV', 'Offset', gvar.CCSCvOffAddr,  SegLabels(gvar.CCSCvCalPoint))

    # ---- CCS 2W 各檔實測電流 (mA) ----
    ccsRange = ['100mA', '20mA', '10mA', '5mA', '2.5mA', '1mA', '0.5mA',
                '0.25mA', '0.1mA', '50uA', '25uA', '10uA', '5uA', '2.5uA',
                '1uA', '0.1uA']
    arr('CCS2W', 'Curr', gvar.CCSCurr2WAddr, ccsRange)

    # ---- 狀態byte ----
    calInfo = gvar.EthCmd('atk_eep_r_b_{}'.format(gvar.CalInfor)).strip()
    rows.append(('INFO', 'CalInfor(byte)', gvar.CalInfor, calInfo))

    # ---- 輸出 ----
    print('{:8s} {:20s} {:6s} {}'.format('Group', 'Name', 'Addr', 'Value'))
    print('-' * 55)
    lastGroup = ''
    for g, n, a, v in rows:
        if g != lastGroup and lastGroup:
            print('-' * 55)
        lastGroup = g
        print('{:8s} {:20s} {:6s} {}'.format(g, n, a, v))

    logDir = os.path.join(current_script_directory, 'log')
    os.makedirs(logDir, exist_ok=True)
    outPath = os.path.join(logDir, 'caldump_' +
                           datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv')
    with open(outPath, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Group', 'Name', 'Addr', 'Value'])
        w.writerows(rows)
    print('\r\nDump saved: {}'.format(outPath))


if __name__ == '__main__':
    main()
