import os
import socket
import sys
import time
import serial
import serial.tools.list_ports
#Range CCSCurr2WAddr = 4280 ~ 42BC
#Range CCSCurr4WAddr = 42C0 ~ 42D8

McuSerialName='COM13'
baudrate=230400
tt_timeout=1

McuKeyword = os.environ.get('SMU_MCU_NAME', 'SMU_CALB')   # GUI可覆寫治具串口關鍵字
plist = list(serial.tools.list_ports.comports())
# 依名稱自動尋找治具串口 (device/描述/序號任一含關鍵字即可, Windows COMx 靠描述判斷)
for p in plist:
    if (McuKeyword in (p.description or '') or McuKeyword in (p.device or '')
            or McuKeyword in (p.serial_number or '')):
        McuSerialName = p.device
        break
McuSerialName = os.environ.get('SMU_MCU_PORT', McuSerialName)  # GUI可直接指定串口
# 用到 MCUCmd 才開串口, 避免沒接治具時 import 就失敗
serialFd = None

def _OpenMcu():
    global serialFd
    if serialFd is None:
        serialFd = serial.Serial(McuSerialName,baudrate,timeout=tt_timeout)
    return serialFd


global Dr1LchData
global MoaLchData
global Att1LchData
global DisLchData
global Dr2LchData
global Mux1Lch1Data
global ExtLchData

Dr1LchData=0
MoaLchData=0
Att1LchData=0
DisLchData=0
Dr2LchData=0
Mux1Lch1Data=0
ExtLchData=0

global CalSmuData
global CalDmmData


CalSmuData=0
CalDmmData=0




AdcCalPoint=[-4,-2,-1,-0.1, -0.01, 0.01, 0.1, 1, 3, 4 ]
AdcChkPoint=[-3,-2.5,-1.5,-0.05, 0, 0.05, 2, 4]

DraDcLCalPoint=[-2,-1,-0.5,-0.1,-0.01, 0.01, 0.1, 0.5, 1, 2 ]
DraDcLChkPoint=[-1.5,-0.5,-0.15,-0.015, 0.015, 0.15, 0.55, 1.5, 2 ]

DraDcHCalPoint=[-8, -7, -5, -3, -2.5, 2.5, 3, 5, 7, 8]

DrbCalPoint=[-8,-7, -5, -3, -2.5, -1, -0.2, 0.2, 1, 2.5, 3, 5, 7, 8]

CCSCvCalPoint=[0.1, 1, 2.5, 3, 5, 7, 8]

ATTCalPoint=[-5, -3, 0, 3, 5]     # ATT路徑校正點 (2460當源)
ATTChkPoint=[-4, -1, 1, 4]
ATTD5Nom  = -10.0    # D5路徑標稱倍率 (÷5再×-0.5 → ADC讀值×-10=輸入電壓)
ATTD10Nom = -20.0    # D10路徑標稱倍率

PP2V5RefAddr 	= '3600'
PN2V5RefAddr 	= '3604'
MUXGain2Addr 	= '3608'
MUXGain4Addr 	= '360C'
MUXGain12Addr 	= '3610'
MUXGain36Addr 	= '3614'
MUXGainN0P2Addr = '3618'
MUXGainN0P5Addr = '361C'

# MUX路徑offset (MUX1=AGND時的ADC端殘餘值), 3640區塊已確認無人使用
MuxOffPassAddr	= '3640'
MuxOff2XAddr	= '3644'
MuxOff4XAddr	= '3648'
MuxOff12XAddr	= '364C'
MuxOff36XAddr	= '3650'
MuxOff02XAddr	= '3654'
MuxOff05XAddr	= '3658'

SrcAcAmp100HZ	= '3620'
AdcAcAmp100HZ	= '3624'
SrcAcAmp1KHZ	= '3628'
AdcAcAmp1KHZ	= '362C'
SrcAcAmp10KHZ	= '3630'
AdcAcAmp10KHZ	= '3634'
SrcAcAmp100KHZ	= '3638'
AdcAcAmp100KHZ	= '363C'

AdcGainAddr 	= '4000'
AdcOffAddr 		= '4040'
DraDcLGainAddr	= '4080'
DraDcLOffAddr	= '40c0'
DraDcHGainAddr	= '4100'
DraDcHOffAddr	= '4140'
DrbGainAddr		= '4180'
DrbOffAddr		= '41C0'
CCSCvGainAddr	= '4200'
CCSCvOffAddr	= '4240'
CCSCurr2WAddr	= '4280'
CCSCurr4WAddr	= '42C0'

CalInfor		= '4300'
ATTD5Addr		= '4304'
ATTD10Addr		= '4308'    # 原本誤植4304會蓋掉D5, 改用4308(已確認為空位)
ATTPathOffAddr	= '430C'    # (舊)單點offset, 保留相容; 新版改用下面的分段表
# ATT路徑分段校正表 (含MUX5 -0.5X整條路徑, 2460當源, 5點: -5,-3,0,3,5)
ATTD5PGainAddr	= '4310'    # D5路徑 gain x4
ATTD5POffAddr	= '4330'    # D5路徑 offset x4
ATTD10PGainAddr	= '4350'    # D10路徑 gain x4
ATTD10POffAddr	= '4370'    # D10路徑 offset x4

DRA0R	= 	0
DRA10R	=	1
DRA100R =	2
DRA1K	=	3
DRA10K	=	4
DRA100K =	5
DRA1M	=	6
DRAOFF  =   7

DRAGND 		=  	0x0000
DRADCV		= 	0x2000
DRAACV		=	0x4000
DRASRC		=	0x6000
DRADCVx5	=	0x8000
DRAACGx5	=	0xA000

DRAMP	=	0x0010
DRASP 	=   0X0020
CCSMP	=	0x0100
CCSSP	=   0x0200
CCSEN	=	0x0400
GNDSP	=	0x0800
GNDGP	=	0x1000

DRBGND  =   0x00
DRBDCV  =   0x10
DRBSP	=	0x08
DRBOFF	=	0x00

DRB0R	=	0
DRB20R	=	1
DRB200R	=	2
DRB1K	=	3
DRBOFF  =   7

MUX1_AGND	= 0x0000
MUX1_DR1C	= 0x0001
MUX1_BUF	= 0x0002
MUX1_CLAMPV = 0x0003
MUX1_DR1IN	= 0x0004
MUX1_DR2C	= 0x0005
MUX1_DR2BUF	= 0x0006
MUX1_ATT	= 0x0007


MUX1_MOAC	= 0x2000
MUX1_DR1OUT = 0x2001
MUX1_DR2OUT = 0x2002
MUX1_TCC32	= 0x2003
MUX1_MOAO	= 0x2004

MUX1_P2V5 	= 0x4000
MUX1_N2V5	= 0x4001
MUX1_VREF	= 0x4002
MUX1_AC		= 0x4003
MUX1_DC		= 0x4004
MUX1_SRC2	= 0x4005
MUX1_CAP    = 0x4006
MUX1_DDSREF = 0x4007

MUX2_PASS	= 0x00
MUX2_BUFF	= 0x08
MUX2_NG02	= 0x10
MUX2_G2  	= 0x18
MUX2_G4		= 0x20
MUX2_G12	= 0x28
MUX2_G36	= 0x30
MUX2_LPF	= 0x38

MUX3_PASS	= 0x00
MUX3_FIR100K= 0x40
MUX3_FIR10K = 0x80
MUX3_FIR1K  = 0xC0

MUX4_GND	= 0x000
MUX4_PASS	= 0x100
MUX4_PHASE	= 0x200
MUX4_PHASEC = 0x300

MUX5_GND	= 0x0000
MUX5_PASS	= 0x0400
MUX5_BUFF	= 0x0800
MUX5_NG05	= 0x0C00
MUX5_LPF	= 0x1000
MUX5_P2V5	= 0x1400
MUX5_N2V5	= 0x1800


ATT_LP_MS	= 0x0001
ATT_LP_SS	= 0x0002
ATT_LP_GS   = 0x0004
ATT_LP_1X   = 0x0020
ATT_LP_D10  = 0x0088
ATT_LP_D5 	= 0x0050
ATT_LP_1M	= 0x0008
ATT_HP_MS   = 0x0100
ATT_HP_SS   = 0x0200
ATT_HP_GS   = 0x0400
ATT_HP_1X   = 0x2000
ATT_HP_D10  = 0x8800
ATT_HP_D5   = 0x5000
ATT_HP_1M   = 0x0800


AC50HZ = 0
AC60HZ = 1



def MCUCmd(lb1_str):
    # print('[MCU_Command]{}'.format(lb1_str))
    _OpenMcu()
    serialFd.reset_input_buffer()
    serialFd.reset_output_buffer()
    fw_reply=[]
    buf_ack=[]
    lb1_str = lb1_str+ "\r\n"
    serialFd.write(lb1_str.encode('utf-8'))
    adc_v=''
    #fw_reply=serialFd.readline().decode()
    for i in range(7):
        sti1 = serialFd.readline()
        # print(sti1)
        encoding = 'utf-8'
        sti1 = sti1.decode(encoding)
        # print(sti1)
        buf_ack.append(sti1)
        # buf_ack.append(serialFd.readline())
        if buf_ack[i][-2:] == '\r\n':
             fw_reply.append(buf_ack[i])
        if (buf_ack[i][-14:]=='fixture_done\r\n' or buf_ack[i][-6:]=='done\r\n' ):
             break




IP=os.environ.get('SMU_IP', '169.254.10.101')   # GUI可覆寫SMU板IP
PORT=7600
# print(IP)

host = socket.gethostname()
rcv_len=1024
server_addr=(IP,PORT)
EthTimeout=10

def _EthConnect():
    # 建立連線: 先送換行清掉板端殘留的半截輸入, 再排空殘留回覆, 避免指令黏包/回覆錯位
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(EthTimeout)
    sock.connect(server_addr)
    try:
        sock.send(b'\n')
    except Exception:
        pass
    sock.settimeout(0.3)
    try:
        while True:
            if not sock.recv(rcv_len):
                break
    except socket.timeout:
        pass
    sock.settimeout(EthTimeout)
    return sock

try:
    op_sock = _EthConnect()
except Exception as e:
    print('Error=',str(e))
    raise

def EthCmd(cmd_str):
    global op_sock
    cmd_str += '\n'
    for retry in range(2):
        try:
            # print(cmd_str, end='')
            op_sock.send(cmd_str.encode('utf-8'))
            response = op_sock.recv(rcv_len).decode('utf-8')
            # print(response)
            return response
        except Exception as e:
            print('EthCmd Error={} (retry {})'.format(e,retry))
            try:
                op_sock.close()
            except Exception:
                pass
            op_sock = _EthConnect()   # 重連+排空後重試一次
    raise ConnectionError('EthCmd fail: {}'.format(cmd_str.strip()))

def ReadCalData(length,addr_gain):
    cal=[]
    addrg=addr_gain
    
    for i in range(length):
        # print(time.time())
        read_data=float(EthCmd('atk_eep_r_f_{}'.format(addrg))[:-2])
        #print ('read_data={}'.format(read_data))
        cal.append(read_data)
        addrg=int(addrg,16)
        addrg=addrg+4
        addrg=format(addrg,'x')
        #print ('ADDR={}'.format(addrg))

    # print('Gain Array ={}'.format(gain))
    # print('Offset Array ={}'.format(offset))
    return cal

#EthCmd('atk_eep_w_b_{}_55'.format(CalInfor))
'''
CalStatus = int(EthCmd('atk_eep_r_b_{}'.format(CalInfor)),16)

if AC60HZ:
	ADCSampling=41666
else:
	ADCSampling=50000

if CalStatus==0x55 :
	CalEn=1
else:
	CalEn=0
'''
CalEn=1

if CalEn:
	PP2V5  = float(EthCmd('atk_eep_r_f_{}'.format(PP2V5RefAddr)))
	PN2V5  = float(EthCmd('atk_eep_r_f_{}'.format(PP2V5RefAddr)))
	MUXG2  = float(EthCmd('atk_eep_r_f_{}'.format(MUXGain2Addr)))
	MUXG4  = float(EthCmd('atk_eep_r_f_{}'.format(MUXGain4Addr)))
	MUXG12 = float(EthCmd('atk_eep_r_f_{}'.format(MUXGain12Addr)))
	MUXG36 = float(EthCmd('atk_eep_r_f_{}'.format(MUXGain36Addr)))
	MUXG02 = float(EthCmd('atk_eep_r_f_{}'.format(MUXGainN0P2Addr)))
	MUXG05 = float(EthCmd('atk_eep_r_f_{}'.format(MUXGainN0P5Addr)))
	ATTGD5 = float(EthCmd('atk_eep_r_f_{}'.format(ATTD5Addr)))
	ATTGD10 = float(EthCmd('atk_eep_r_f_{}'.format(ATTD10Addr)))
	ATTPOFF = float(EthCmd('atk_eep_r_f_{}'.format(ATTPathOffAddr)))
	if not (-0.01 < ATTPOFF < 0.01):   # 未校過(空值/垃圾)時不套用offset
		ATTPOFF = 0.0

	MUXOFF = {}
	for _k, _a in (('PASS', MuxOffPassAddr), ('2X', MuxOff2XAddr),
	               ('4X', MuxOff4XAddr), ('12X', MuxOff12XAddr),
	               ('36X', MuxOff36XAddr), ('0.2X', MuxOff02XAddr),
	               ('-0.5X', MuxOff05XAddr)):
		_v = float(EthCmd('atk_eep_r_f_{}'.format(_a)))
		MUXOFF[_k] = _v if -0.01 < _v < 0.01 else 0.0   # 未校過不套用

	ATTD5PGain   = ReadCalData(len(ATTCalPoint)-1, ATTD5PGainAddr)
	ATTD5POffset = ReadCalData(len(ATTCalPoint)-1, ATTD5POffAddr)
	ATTD10PGain   = ReadCalData(len(ATTCalPoint)-1, ATTD10PGainAddr)
	ATTD10POffset = ReadCalData(len(ATTCalPoint)-1, ATTD10POffAddr)
	# 表未校過(空值)時退回單位增益, ExtMv等於用標稱倍率
	if not all(0.5 < g < 2.0 for g in ATTD5PGain):
		ATTD5PGain   = [1.0]*(len(ATTCalPoint)-1)
		ATTD5POffset = [0.0]*(len(ATTCalPoint)-1)
	if not all(0.5 < g < 2.0 for g in ATTD10PGain):
		ATTD10PGain   = [1.0]*(len(ATTCalPoint)-1)
		ATTD10POffset = [0.0]*(len(ATTCalPoint)-1)

	SRCAMP100HZ  = float(EthCmd('atk_eep_r_f_{}'.format(SrcAcAmp100HZ)))
	SRCAMP1KHZ   = float(EthCmd('atk_eep_r_f_{}'.format(SrcAcAmp1KHZ)))
	SRCAMP10KHZ  = float(EthCmd('atk_eep_r_f_{}'.format(SrcAcAmp10KHZ)))
	SRCAMP100KHZ = float(EthCmd('atk_eep_r_f_{}'.format(SrcAcAmp100KHZ)))

	ADCMAMP100HZ  = float(EthCmd('atk_eep_r_f_{}'.format(AdcAcAmp100HZ)))
	ADCMAMP1KHZ   = float(EthCmd('atk_eep_r_f_{}'.format(AdcAcAmp1KHZ)))
	ADCMAMP10KHZ  = float(EthCmd('atk_eep_r_f_{}'.format(AdcAcAmp10KHZ)))
	ADCMAMP100KHZ = float(EthCmd('atk_eep_r_f_{}'.format(AdcAcAmp100KHZ)))

	ADCGain      = ReadCalData(len(AdcCalPoint)-1,AdcGainAddr)
	ADCOffset    = ReadCalData(len(AdcCalPoint)-1,AdcOffAddr)
	print(ADCGain)
	print(ADCOffset)
	DraDcLGain   = ReadCalData(len(DraDcLCalPoint)-1,DraDcLGainAddr)
	DraDcLOffset = ReadCalData(len(DraDcLCalPoint)-1,DraDcLOffAddr)
	DraDcHGain   = ReadCalData(len(DraDcHCalPoint)-1,DraDcHGainAddr)
	DraDcHOffset = ReadCalData(len(DraDcHCalPoint)-1,DraDcHOffAddr)
	DrbGain      = ReadCalData(len(DrbCalPoint)-1,DrbGainAddr)
	DrbOffset    = ReadCalData(len(DrbCalPoint)-1,DrbOffAddr)
	CCSCvGain    = ReadCalData(len(CCSCvCalPoint)-1,CCSCvGainAddr)
	CCSCvOffset  = ReadCalData(len(CCSCvCalPoint)-1,CCSCvOffAddr)
	CCSCal = ReadCalData(16,CCSCurr2WAddr)
	
	#print('READ CCS CAL ADDR')
	# print ('CCSCal={}'.format(CCSCal))
	#CCS4W = ReadCalData(6,CCSCurr2WAddr)

else:

	PP2V5  = 2.5
	PN2V5  = -2.5
	MUXG2  = 2.0
	MUXG4  = 4.0
	MUXG12 = 12.0
	MUXG36 = 36.0
	MUXG02 = -0.2
	MUXG05 = -0.5
	ATTGD5 = 0.2
	ATTGD10 = 0.1
	ATTPOFF = 0.0
	MUXOFF = {'PASS': 0.0, '2X': 0.0, '4X': 0.0, '12X': 0.0,
	          '36X': 0.0, '0.2X': 0.0, '-0.5X': 0.0}
	ATTD5PGain    = [1.0, 1.0, 1.0, 1.0]
	ATTD5POffset  = [0.0, 0.0, 0.0, 0.0]
	ATTD10PGain   = [1.0, 1.0, 1.0, 1.0]
	ATTD10POffset = [0.0, 0.0, 0.0, 0.0]

	SRCAMP100HZ  = 0.707
	SRCAMP1KHZ   = 0.707
	SRCAMP10KHZ  = 0.707
	SRCAMP100KHZ = 0.707

	ADCMAMP100HZ  = 0.707
	ADCMAMP1KHZ   = 0.707
	ADCMAMP10KHZ  = 0.707
	ADCMAMP100KHZ = 0.707

	ADCGain      = [1, 1, 1, 1, 1, 1, 1, 1, 1]
	ADCOffset    = [0, 0, 0, 0, 0, 0, 0, 0, 0]
	DraDcLGain   = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
	DraDcLOffset = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	DraDcHGain   = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
	DraDcHOffset = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	DrbGain      = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
	DrbOffset    = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	CCSCvGain    = [1, 1, 1, 1, 1, 1, 1]
	CCSCvOffset  = [0, 0, 0, 0, 0, 0, 0]

	CCSCal = [20, 10, 5, 2.5, 1, 0.5, 0.25, 0.1, 0.05, 0.025, 0.01, 0.005, 0.0025, 0.001, 0.0001]
	#CCS4W = [100, 20, 10, 5, 2.5, 1]
