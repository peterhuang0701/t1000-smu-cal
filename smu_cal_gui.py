# -*- coding: utf-8 -*-
"""
T1000 SMU Calibration Tool - GUI Version
----------------------------------------
- 2460 連線: VISA 資源清單(USB/GPIB/LAN, 可Refresh) 或手動填 IP
- MCU 治具串口: 預設自動偵測 SMU_CALB, 可下拉修改
- SMU 板 IP: 預設 169.254.10.101
- 校正步驟 1~6 可選範圍, log 同步寫入 log/時間戳.log
"""

import os
import sys
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

if getattr(sys, 'frozen', False):
    HERE = os.path.dirname(sys.executable)   # pyinstaller onefile
else:
    HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DEFAULT_SMU_IP = '169.254.10.101'
DEFAULT_K2460_IP = '169.254.10.222'
DEFAULT_MCU_NAME = 'SMU_CALB'

SELF_STEP_NAMES = [
    '1 : ADC Self Cal (±2.5VREF)',
    '2 : MUX Offset',
    '3 : MUX Gain',
    '4 : SRC DC (DRA/DRB)',
    '5 : CCS Clamp V',
    '6 : ATT (APC loopback)',
]

STEP_NAMES = [
    '1 : ADC1 Calibration',
    '2 : SRC DC Calibration (DRA/DRB)',
    '3 : CCS Clamp V Calibration',
    '4 : CCS Calibration',
    '5 : MUX Gain + Offset Calibration',
    '6 : ATT Gain Calibration',
]


# ------------------------------------------------------------------
# Calibration Worker (跑在背景 thread)
# ------------------------------------------------------------------
class CalWorker:
    def __init__(self, cfg, log_cb, done_cb):
        self.cfg = cfg          # dict: smu_res, board_ip, mcu_port, start, end
        self.log = log_cb
        self.done = done_cb

    def run(self):
        old_out, old_err = sys.stdout, sys.stderr
        writer = _LogWriter(self.log)
        sys.stdout = writer
        sys.stderr = writer
        try:
            os.environ['SMU_IP'] = self.cfg['board_ip']
            if self.cfg.get('apc_ip'):
                os.environ['SMU_APC_IP'] = self.cfg['apc_ip']
            if self.cfg.get('mcu_port'):
                os.environ['SMU_MCU_PORT'] = self.cfg['mcu_port']
            else:
                os.environ.pop('SMU_MCU_PORT', None)   # 交給gvar自動偵測SMU_CALB

            # 先關掉上一輪的連線: 板子只接受單一TCP連線, 不關掉重連會被reset
            old_gvar = sys.modules.get('gvar')
            if old_gvar is not None:
                try:
                    old_gvar.op_sock.close()
                except Exception:
                    pass
                try:
                    if old_gvar.serialFd:
                        old_gvar.serialFd.close()
                except Exception:
                    pass

            # 每次執行都重新載入模組: 套用新IP/串口設定, 並重置shadow狀態
            for m in ('Self_Cal', 'Run_All_Cal', 'LCR_CAL', 'LCR_ADC',
                      'LCR_SRC', 'LCR_FUN', 'K2460', 'gvar'):
                sys.modules.pop(m, None)

            if self.cfg.get('selfcal'):
                import Self_Cal as SC
                SC.RunSelfCal(self.cfg['start'], self.cfg['end'],
                              confirmWrite=self.cfg.get('confirm_cb'))
                self.done(True, 'Self Cal Finished (Step {}~{})'.format(
                    self.cfg['start'], self.cfg['end']))
            else:
                import Run_All_Cal as RAC
                RAC.RunCal(self.cfg['start'], self.cfg['end'],
                           smuName=self.cfg['smu_res'],
                           confirmWrite=self.cfg.get('confirm_cb'))
                self.done(True, 'Calibration Finished (Step {}~{})'.format(
                    self.cfg['start'], self.cfg['end']))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.done(False, 'Calibration Failed: {}'.format(e))
        finally:
            sys.stdout, sys.stderr = old_out, old_err


class _LogWriter:
    def __init__(self, log_cb):
        self.log_cb = log_cb
        self.buf = ''

    def write(self, msg):
        self.buf += msg
        while '\n' in self.buf:
            line, self.buf = self.buf.split('\n', 1)
            self.log_cb(line.rstrip('\r'))

    def flush(self):
        pass


def show_write_confirm(parent, blocks, res, evt):
    # 校正完成後的寫入確認彈窗: 依區塊勾選要寫進EEPROM的項目
    win = tk.Toplevel(parent)
    win.title('寫入K值確認')
    win.grab_set()   # modal
    ttk.Label(win, text='校正完成, 勾選要寫入EEPROM的區塊:',
              font=('', 11, 'bold')).pack(anchor='w', padx=12, pady=(12, 6))
    vars_ = []
    for b in blocks:
        v = tk.BooleanVar(value=True)
        txt = '{} ({}筆)'.format(b['name'], len(b['addrs']))
        if b['exist']:
            txt += '   ⚠ EEPROM已有資料, 將被覆蓋'
        ttk.Checkbutton(win, text=txt, variable=v).pack(anchor='w', padx=24, pady=2)
        vars_.append((b['name'], v))

    def finish(sel):
        res['sel'] = sel
        evt.set()
        win.destroy()

    bar = ttk.Frame(win)
    bar.pack(fill='x', pady=12, padx=12)
    ttk.Button(bar, text='寫入勾選項目',
               command=lambda: finish([n for n, v in vars_ if v.get()]))\
        .pack(side='left', padx=6)
    ttk.Button(bar, text='全部不寫',
               command=lambda: finish([])).pack(side='left', padx=6)
    win.protocol('WM_DELETE_WINDOW', lambda: finish([]))   # 關窗=不寫


def make_confirm_cb(window):
    # 給worker執行緒用的確認callback: 丟給GUI主執行緒開彈窗, Event等答案
    def cb(blocks):
        evt = threading.Event()
        res = {}
        window.log_q.put(('__CONFIRM__', blocks, res, evt))
        evt.wait()
        return res.get('sel', [])
    return cb


# ------------------------------------------------------------------
# Self Cal 視窗: 只需SMU板IP, 不需2460 (基準為板上±2.5VREF)
# ------------------------------------------------------------------
class SelfCalWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title('Self Calibration (不需2460)')
        self.geometry('640x520')
        self.log_q = queue.Queue()
        pad = {'padx': 6, 'pady': 4}

        f1 = ttk.LabelFrame(self, text='連線')
        f1.pack(fill='x', **pad)
        ttk.Label(f1, text='SMU 板 IP:').grid(row=0, column=0, sticky='e', **pad)
        self.board_ip = tk.StringVar(value=app.board_ip.get() or DEFAULT_SMU_IP)
        ttk.Entry(f1, textvariable=self.board_ip, width=20)\
            .grid(row=0, column=1, sticky='w', **pad)
        ttk.Label(f1, text='(基準: 板上±2.5VREF, 不需2460)')\
            .grid(row=0, column=2, sticky='w', **pad)
        ttk.Label(f1, text='APC IP:').grid(row=1, column=0, sticky='e', **pad)
        self.apc_ip = tk.StringVar(value='169.254.10.102')
        ttk.Entry(f1, textvariable=self.apc_ip, width=20)\
            .grid(row=1, column=1, sticky='w', **pad)
        ttk.Label(f1, text='(步驟6 loopback用, 只跑1~5可不填)')\
            .grid(row=1, column=2, sticky='w', **pad)

        f2 = ttk.LabelFrame(self, text='步驟')
        f2.pack(fill='x', **pad)
        ttk.Label(f2, text='從').grid(row=0, column=0, **pad)
        self.step_start = ttk.Combobox(f2, values=SELF_STEP_NAMES, width=28,
                                       state='readonly')
        self.step_start.current(0)
        self.step_start.grid(row=0, column=1, **pad)
        ttk.Label(f2, text='到').grid(row=0, column=2, **pad)
        self.step_end = ttk.Combobox(f2, values=SELF_STEP_NAMES, width=28,
                                     state='readonly')
        self.step_end.current(5)
        self.step_end.grid(row=0, column=3, **pad)

        f3 = ttk.Frame(self)
        f3.pack(fill='x', **pad)
        self.run_btn = ttk.Button(f3, text='Start Self Cal',
                                  command=self.start_selfcal)
        self.run_btn.pack(side='left', padx=6)
        self.status_var = tk.StringVar(value='Idle')
        ttk.Label(f3, textvariable=self.status_var).pack(side='left', padx=12)

        self.log_box = scrolledtext.ScrolledText(self, height=18,
                                                 state='disabled',
                                                 font=('Consolas', 10))
        self.log_box.pack(fill='both', expand=True, **pad)
        self.after(100, self._poll_log)

    def start_selfcal(self):
        if self.app.running:
            messagebox.showwarning('Busy', '已有校正在執行中', parent=self)
            return
        ip = self.board_ip.get().strip()
        if not ip:
            messagebox.showwarning('SMU', '請填 SMU 板 IP', parent=self)
            return
        start = self.step_start.current() + 1
        end = self.step_end.current() + 1
        if start > end:
            messagebox.showwarning('步驟', '起始步驟不能大於結束步驟', parent=self)
            return

        cfg = {'selfcal': True, 'board_ip': ip, 'mcu_port': '',
               'apc_ip': self.apc_ip.get().strip(),
               'start': start, 'end': end, 'smu_res': '',
               'confirm_cb': make_confirm_cb(self)}
        self.app.running = True
        self.run_btn.configure(state='disabled')
        self.status_var.set('Running... (Step {}~{})'.format(start, end))
        self.log_line('=' * 60)
        self.log_line('[CFG] Self Cal  Board={}  Step {}~{}'.format(ip, start, end))
        worker = CalWorker(cfg, self.log_line,
                           lambda ok, msg: self.log_q.put(('__DONE__', ok, msg)))
        threading.Thread(target=worker.run, daemon=True).start()

    def log_line(self, msg):
        self.log_q.put(('__LOG__', msg))

    def _poll_log(self):
        try:
            while True:
                item = self.log_q.get_nowait()
                if item[0] == '__CONFIRM__':
                    _, blocks, res, evt = item
                    show_write_confirm(self, blocks, res, evt)
                elif item[0] == '__DONE__':
                    _, ok, msg = item
                    self.app.running = False
                    self.run_btn.configure(state='normal')
                    self.status_var.set(msg)
                    self._append(('[OK] ' if ok else '[FAIL] ') + msg)
                else:
                    self._append(item[1])
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._poll_log)

    def _append(self, line):
        self.log_box.configure(state='normal')
        self.log_box.insert('end', line + '\n')
        self.log_box.see('end')
        self.log_box.configure(state='disabled')


# ------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        from version import __version__
        self.title('T1000 SMU Calibration Tool  v{}'.format(__version__))
        self.geometry('760x640')
        self.resizable(True, True)

        self.log_q = queue.Queue()
        self.running = False
        self._build_ui()
        self.refresh_visa()
        self.refresh_mcu()
        self.after(100, self._poll_log)
        threading.Thread(target=self._check_update, daemon=True).start()

    def _check_update(self):
        # 啟動時背景檢查GitHub最新Release, 不影響操作; 無網路只在log提示
        try:
            from version import __version__, check_latest, RELEASE_PAGE
            tag, newer = check_latest()
            if newer:
                self.log_line('[UPDATE] 有新版 v{} (目前 v{}), 下載: {}'.format(
                    tag, __version__, RELEASE_PAGE))
                self.log_q.put(('__NEWVER__', tag))
            else:
                self.log_line('[UPDATE] 已是最新版 (v{})'.format(__version__))
        except Exception as e:
            self.log_line('[UPDATE] 版本檢查失敗(離線?): {}'.format(e))

    # --------- UI ---------
    def _build_ui(self):
        pad = {'padx': 6, 'pady': 4}

        # ---- 2460 連線 ----
        f1 = ttk.LabelFrame(self, text='Keithley 2460')
        f1.pack(fill='x', **pad)

        self.k2460_mode = tk.StringVar(value='visa')
        rb1 = ttk.Radiobutton(f1, text='VISA 資源 (USB / GPIB / LAN)',
                              variable=self.k2460_mode, value='visa',
                              command=self._update_mode)
        rb1.grid(row=0, column=0, sticky='w', **pad)
        self.visa_combo = ttk.Combobox(f1, width=48, state='readonly')
        self.visa_combo.grid(row=0, column=1, sticky='we', **pad)
        self.visa_refresh_btn = ttk.Button(f1, text='Refresh',
                                           command=self.refresh_visa)
        self.visa_refresh_btn.grid(row=0, column=2, **pad)

        rb2 = ttk.Radiobutton(f1, text='手動填 IP (LAN)',
                              variable=self.k2460_mode, value='ip',
                              command=self._update_mode)
        rb2.grid(row=1, column=0, sticky='w', **pad)
        self.k2460_ip = tk.StringVar(value=DEFAULT_K2460_IP)
        self.k2460_ip_entry = ttk.Entry(f1, textvariable=self.k2460_ip, width=20)
        self.k2460_ip_entry.grid(row=1, column=1, sticky='w', **pad)
        f1.columnconfigure(1, weight=1)

        # ---- MCU / SMU 板 ----
        f2 = ttk.LabelFrame(self, text='治具 MCU / SMU 板')
        f2.pack(fill='x', **pad)

        ttk.Label(f2, text='Calibration Board:').grid(row=0, column=0, sticky='e', **pad)
        self.mcu_combo = ttk.Combobox(f2, width=48)   # 可下拉可手改
        self.mcu_combo.grid(row=0, column=1, sticky='we', **pad)
        ttk.Button(f2, text='Refresh', command=self.refresh_mcu)\
            .grid(row=0, column=2, **pad)

        ttk.Label(f2, text='SMU 板 IP:').grid(row=1, column=0, sticky='e', **pad)
        self.board_ip = tk.StringVar(value=DEFAULT_SMU_IP)
        ttk.Entry(f2, textvariable=self.board_ip, width=20)\
            .grid(row=1, column=1, sticky='w', **pad)
        f2.columnconfigure(1, weight=1)

        # ---- 步驟 ----
        f3 = ttk.LabelFrame(self, text='校正步驟')
        f3.pack(fill='x', **pad)
        ttk.Label(f3, text='從').grid(row=0, column=0, sticky='e', **pad)
        self.step_start = ttk.Combobox(f3, values=STEP_NAMES, width=34,
                                       state='readonly')
        self.step_start.current(0)
        self.step_start.grid(row=0, column=1, **pad)
        ttk.Label(f3, text='到').grid(row=0, column=2, sticky='e', **pad)
        self.step_end = ttk.Combobox(f3, values=STEP_NAMES, width=34,
                                     state='readonly')
        self.step_end.current(5)
        self.step_end.grid(row=0, column=3, **pad)

        # ---- 執行 ----
        f4 = ttk.Frame(self)
        f4.pack(fill='x', **pad)
        self.run_btn = ttk.Button(f4, text='Start Calibration',
                                  command=self.start_cal)
        self.run_btn.pack(side='left', padx=6)
        ttk.Button(f4, text='Self Cal...', command=self.open_selfcal)\
            .pack(side='left', padx=6)
        self.status_var = tk.StringVar(value='Idle')
        ttk.Label(f4, textvariable=self.status_var).pack(side='left', padx=12)

        # ---- Log ----
        self.log_box = scrolledtext.ScrolledText(self, height=22,
                                                 state='disabled',
                                                 font=('Consolas', 10))
        self.log_box.pack(fill='both', expand=True, **pad)

        self._update_mode()

    def open_selfcal(self):
        SelfCalWindow(self)

    def _update_mode(self):
        visa = self.k2460_mode.get() == 'visa'
        self.visa_combo.configure(state='readonly' if visa else 'disabled')
        self.visa_refresh_btn.configure(state='normal' if visa else 'disabled')
        self.k2460_ip_entry.configure(state='disabled' if visa else 'normal')

    # --------- Refresh ---------
    def refresh_visa(self):
        try:
            import pyvisa
            try:
                rm = pyvisa.ResourceManager()
            except Exception:
                rm = pyvisa.ResourceManager('@py')
            res = [r for r in rm.list_resources()
                   if not r.upper().startswith('ASRL')]   # 串列埠歸MCU選單
            self.visa_combo['values'] = res
            if res:
                self.visa_combo.current(0)
            else:
                self.visa_combo.set('')
            self.log_line('[VISA] Found: {}'.format(res if res else 'None'))
        except Exception as e:
            self.log_line('[VISA] Refresh fail: {}'.format(e))

    def refresh_mcu(self):
        try:
            import serial.tools.list_ports as lp
            ports = list(lp.comports())
            items = ['{} | {}'.format(p.device, p.description) for p in ports]
            self.mcu_combo['values'] = items
            pick = ''
            for it in items:   # 預設抓含 SMU_CALB 的
                if DEFAULT_MCU_NAME in it:
                    pick = it
                    break
            if not pick and items:
                pick = items[0]
            self.mcu_combo.set(pick)
            self.log_line('[MCU] Ports: {}'.format(
                [p.device for p in ports] if ports else 'None'))
        except Exception as e:
            self.log_line('[MCU] Refresh fail: {}'.format(e))

    # --------- Run ---------
    def start_cal(self):
        if self.running:
            return

        if self.k2460_mode.get() == 'visa':
            smu_res = self.visa_combo.get().strip()
            if not smu_res:
                messagebox.showwarning('2460', '請先 Refresh 並選擇 VISA 資源')
                return
        else:
            ip = self.k2460_ip.get().strip()
            if not ip:
                messagebox.showwarning('2460', '請填 2460 IP')
                return
            smu_res = 'TCPIP0::{}::inst0::INSTR'.format(ip)

        mcu = self.mcu_combo.get().split('|')[0].strip()
        if not mcu:
            messagebox.showwarning('MCU', '請選擇或填入 MCU 串口')
            return

        board_ip = self.board_ip.get().strip()
        if not board_ip:
            messagebox.showwarning('SMU', '請填 SMU 板 IP')
            return

        start = self.step_start.current() + 1
        end = self.step_end.current() + 1
        if start > end:
            messagebox.showwarning('步驟', '起始步驟不能大於結束步驟')
            return

        cfg = {'smu_res': smu_res, 'board_ip': board_ip,
               'mcu_port': mcu, 'start': start, 'end': end,
               'confirm_cb': make_confirm_cb(self)}

        self.running = True
        self.run_btn.configure(state='disabled')
        self.status_var.set('Running... (Step {}~{})'.format(start, end))
        self.log_line('=' * 60)
        self.log_line('[CFG] 2460={}'.format(smu_res))
        self.log_line('[CFG] Board={}  MCU={}  Step {}~{}'.format(
            board_ip, mcu, start, end))

        worker = CalWorker(cfg, self.log_line, self._on_done)
        threading.Thread(target=worker.run, daemon=True).start()

    def _on_done(self, ok, msg):
        self.log_q.put(('__DONE__', ok, msg))

    # --------- Log ---------
    def log_line(self, msg):
        self.log_q.put(('__LOG__', msg))

    def _poll_log(self):
        try:
            while True:
                item = self.log_q.get_nowait()
                if item[0] == '__CONFIRM__':
                    _, blocks, res, evt = item
                    show_write_confirm(self, blocks, res, evt)
                elif item[0] == '__NEWVER__':
                    if not self.running:
                        self.status_var.set('有新版 v{} 可下載 (見log連結)'.format(item[1]))
                elif item[0] == '__DONE__':
                    _, ok, msg = item
                    self.running = False
                    self.run_btn.configure(state='normal')
                    self.status_var.set(msg)
                    self._append(('[OK] ' if ok else '[FAIL] ') + msg)
                    if ok:
                        messagebox.showinfo('Done', msg)
                    else:
                        messagebox.showerror('Fail', msg)
                else:
                    self._append(item[1])
        except queue.Empty:
            pass
        self.after(100, self._poll_log)

    def _append(self, line):
        self.log_box.configure(state='normal')
        self.log_box.insert('end', line + '\n')
        self.log_box.see('end')
        self.log_box.configure(state='disabled')


def _selftest():
    # build完自檢: 確認所有動態import的模組都有被打包進exe
    # 用法: SMU_Cal_Tool.exe --selftest  (結果寫到exe同層selftest.txt, exit 0=OK)
    result = []
    ok = True
    for m in ('pyvisa', 'serial',
              'serial.tools.list_ports', 'K2460', 'gvar', 'LCR_FUN',
              'LCR_ADC', 'LCR_SRC', 'LCR_CAL', 'Run_All_Cal'):
        try:
            mod = __import__(m)
            if m == 'serial' and not hasattr(mod, 'Serial'):
                # 系統若裝了另一個也叫serial的套件會蓋掉pyserial, import會過但沒有Serial
                result.append('FAIL serial -> not pyserial (no Serial class)')
                ok = False
                continue
            result.append('OK   {}'.format(m))
        except ImportError as e:
            # 模組沒被打包進exe -> 真的FAIL
            result.append('FAIL {} -> {}'.format(m, e))
            ok = False
        except Exception as e:
            # 模組有打包, 但import時連硬體失敗(如gvar連SMU板) -> 打包上算OK
            result.append('OK   {} (no hardware: {})'.format(m, e))
    with open(os.path.join(HERE, 'selftest.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(result) + '\n')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        _selftest()
    App().mainloop()
