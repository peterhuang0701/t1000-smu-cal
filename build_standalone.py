# -*- coding: utf-8 -*-
# 把 Run_All_Cal.py 及其依賴模組打包成單一檔案 Run_All_Cal_Standalone.py
# 有改任何模組後重跑本腳本即可重新產生
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# 依相依順序: gvar 最先 (其他模組 import 它)
MODULES = ['gvar', 'K2460', 'LCR_FUN', 'LCR_ADC', 'LCR_SRC', 'LCR_CAL']
OUT = os.path.join(HERE, 'Run_All_Cal_Standalone.py')

HEADER = '''# -*- coding: utf-8 -*-
# Run_All_Cal_Standalone.py  (自動產生, 請勿手改; 改原始模組後重跑 build_standalone.py)
# 單一檔案版本的 Run_All_Cal: 內嵌 gvar / K2460 / LCR_FUN / LCR_ADC / LCR_SRC / LCR_CAL
# 需要的套件: pyvisa(+VISA backend), pyserial, numpy, matplotlib
import sys
import types
import base64
import zlib

def _load(name, b64src):
    src = zlib.decompress(base64.b64decode(b64src)).decode('utf-8')
    mod = types.ModuleType(name)
    mod.__file__ = '<embedded:{}>'.format(name)
    sys.modules[name] = mod
    exec(compile(src, mod.__file__, 'exec'), mod.__dict__)
    return mod

'''

import base64
import zlib

def embed(name):
    with open(os.path.join(HERE, name + '.py'), encoding='utf-8') as f:
        src = f.read()
    b64 = base64.b64encode(zlib.compress(src.encode('utf-8'), 9)).decode('ascii')
    lines = [b64[i:i+100] for i in range(0, len(b64), 100)]
    blob = "'\n    b'".join(lines)
    return "# ---- {n}.py ({ln} lines) ----\n_load({n!r},\n    b'{b}'\n)\n\n".format(
        n=name, ln=src.count('\n') + 1, b=blob)


def main():
    parts = [HEADER]
    for m in MODULES:
        parts.append(embed(m))

    with open(os.path.join(HERE, 'Run_All_Cal.py'), encoding='utf-8') as f:
        main_src = f.read()
    parts.append('# ================= Run_All_Cal 主流程 =================\n')
    parts.append(main_src)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(''.join(parts))
    print('written:', OUT)


if __name__ == '__main__':
    main()
