# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['smu_cal_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # worker 內動態 import, pyinstaller 靜態分析抓不到, 需明列
        'Run_All_Cal',
        'Self_Cal',
        'LCR_CAL',
        'LCR_ADC',
        'LCR_SRC',
        'LCR_FUN',
        'K2460',
        'gvar',
        'pyvisa',
        'pyvisa_py',
        'serial',
        'serial.tools.list_ports',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SMU_Cal_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['ico.ico'],
)
