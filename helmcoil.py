# -*- coding: utf-8 -*-
import visa
import time
import os
import sys
import csv
import datetime

UNSAFE = False
DEVENV = True
if not DEVENV:
    rm = visa.ResourceManager()
    gauss = rm.open_resource("ASRL3::INSTR")
    power = rm.open_resource("GPIB0::4::INSTR")


def get_time_str() -> str:
    """
    現時刻を日本語に整形した文字列を返す
    :rtype: str
    :return: '2018年9月5日\u300012時47分41秒'
    """
    now = datetime.datetime.now()
    return str(("%s年%s月%s日　%s時%s分%s秒" % (now.year, now.month, now.day, now.hour, now.minute, now.second)))


def FetchIout() -> float:  # 出力電流の関数
    """
    出力電流を返す
    単位:A
    :rtype: float
    :return: 3.210
    """
    iout = power.query("IOUT?")
    return float(iout.translate(str.maketrans('', '', 'IOUT A\r\n')))


def FetchVout() -> float:
    """
    出力電圧を返す
    単位:V
    :rtype: float
    :return: 3.210
    """
    vout = power.query("VOUT?")
    return float(vout.translate(str.maketrans('', '', 'VOUT V\r\n')))  # 指定文字を文字列から削除


def FetchIset():  # 出力電流の関数
    vout = power.query("ISET?")
    return float(vout.translate(str.maketrans('', '', 'ISET A\r\n')))  # 指定文字を文字列から削除


def FetchVset():  # 出力電流の関数
    vout = power.query("VSET?")
    return float(vout.translate(str.maketrans('', '', 'VSET V\r\n')))  # 指定文字を文字列から削除


def SetIset(i):
    power.write("ISET " + "%.3f" % (float(i)))


def SetIsetMA(mA):
    A = "%.3f" % (mA / 1000)
    SetIset(A)


def FetchField():  # 測定磁界の関数
    value = gauss.query("FIELD?")
    return value.translate(str.maketrans('', '', ' \r\n'))


def ReadField():  # 測定磁界の関数
    readfield = gauss.query("FIELD?") + gauss.query("FIELDM?") + gauss.query("UNIT?")
    return readfield.translate(str.maketrans('', '', ' \r\n'))


def loadStatus():
    iout = FetchIout()
    iset = FetchIset()
    vout = FetchVout()
    H = FetchField()
    return iset, iout, H, vout


def addSaveStatus(filename, status):
    with open(filename, 'a')as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(status)


def usWriteGauss(s):
    gauss.write(s)


def usWritePower(s):
    power.write(s)


def CanOutput():
    if power.query("OUT?") == 'OUT 001\r\n':
        return True
    return False


def CtlIoutMA(target, step=100):
    if target == FetchIset():
        return
    mAcurrent = int(FetchIout() * 1000)
    if mAcurrent < target:
        ctlPoint = list(range(mAcurrent, int(target), abs(int(step))))
    else:
        ctlPoint = list(range(mAcurrent, int(target), abs(int(step)) * -1))
    for mA in ctlPoint:
        SetIsetMA(mA)
        time.sleep(0.2)
    SetIsetMA(target)
    time.sleep(0.1)
    if abs(FetchIout() - target) < 0.01:
        return
    SetIsetMA(target)
    time.sleep(0.3)
    if abs(FetchIout() - target) < 0.01:
        return
    print("[Warn]:電流が指定値に合わせられませんでした")


def gen_csv_header(filename, time_str):
    print("測定条件等メモ記入欄")
    memo = input("memo :")
    with open(filename, 'a')as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(["開始時刻", time_str])
        writer.writerow(["memo", memo])
        writer.writerow(["#####"])
        writer.writerow(["設定電流:ISET[A]", "出力電流:IOUT[A]", "磁界:H[Gauss]", "出力電圧:VOUT[V]"])


def measure():
    if not CanOutput():
        power.write("OUT 1")
        time.sleep(0.8)
        if not CanOutput():
            print("出力をONにできません")
            return
        print("出力をONに変更しました")
    print("出力が許可されています。")

    gauss.write("RANGE 2")
    time.sleep(0.1)
    gaussrange = gauss.query("RANGE?")  # 現在の設定レンジの問い合わせ
    if gaussrange == '2\r\n':
        print('ガウスメーターのレンジが +-300G に変更されました')

    else:
        print('ガウスメーターのレンジを確認してください')
        return

    """
    0A=>+5A=>0A=>-5A=>0A
    mA
    """
    checkPoint = [0, 5000, 0, -5000, 0]
    mesh = 500
    step = 100
    count = 0

    now = datetime.datetime.now()
    startTime = "%s-%s-%s_%s-%s-%s" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
    savefile = startTime + ".csv"
    gen_csv_header(savefile, startTime)

    for i in checkPoint:
        if count==0:
            CtlIoutMA(i,step)
            count += 1
            continue
        isetmA = int(FetchIset() * 1000)
        if i >= isetmA:
            recodePoint = range(isetmA, i, abs(mesh))
        else:
            recodePoint = range(isetmA, i, abs(mesh) * -1)
        for j in recodePoint:
            CtlIoutMA(j, step)
            time.sleep(0.5)
            iset, iout, h, vout = loadStatus()
            print("ISET= " + str(iset), "IOUT= " + str(iout), "Field= " + str(h), "VOUT= " + str(vout))
            addSaveStatus(savefile, (iset, iout, h, vout))
        CtlIoutMA(i, step)
        time.sleep(0.5)
        iset, iout, h, vout = loadStatus()
        print("ISET= " + str(iset), "IOUT= " + str(iout), "Field= " + str(h), "VOUT= " + str(vout))
        addSaveStatus(savefile, (iset, iout, h, vout))
        continue

    now = datetime.datetime.now()
    endTime = "%s-%s-%s_%s-%s-%s" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
    with open(savefile, 'a')as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(["終了時刻", endTime])
    print("Done")





def usQueryGauss(s):
    print("=>: " + s)
    print("\n")
    print("<=: " + gauss.query(s))


def usQueryPower(s):
    print("=>: " + s)
    print("\n")
    print("<=: " + power.query(s))


def init():
    print("init....")
    """
    接続確認(始動動作)
    """
    # ガウスメーターの接続確認
    gaussconnection = gauss.query("*IDN?")

    if gaussconnection == 'LSCI,MODEL421,0,010306\r\n':
        print("gauss : connection confirmed")

    else:
        sys.exit("gauss : connection failed")

    # バイポーラ電源の接続確認
    powerconnection = power.query("IDN?")

    if powerconnection == 'IDN PBX 40-10 VER1.13     KIKUSUI    \r\n':
        print("power : connection confirmed")

    else:
        sys.exit("power : connection failed")

    # ガウスメーターのレンジを最低感度に設定
    gauss.write("RANGE 0")
    time.sleep(1.0)
    gaussrange = gauss.query("RANGE?")  # 現在の設定レンジの問い合わせ
    if gaussrange == '0\r\n':
        print('ガウスメーターのレンジが最大に変更されました')

    else:
        print('ガウスメーターのレンジを確認してください')
    # バイポーラ電源の初期化
    current = FetchIout()

    if abs(current) < 0.009:
        print("normal state\n")

    else:
        print("abnormal state!!")
        sys.exit("接続を確認してください")

    # バイポーラのOUTPUTをON
    power.write("OUT 0")
    time.sleep(1.0)
    if FetchIset() != 0.000:
        power.write("ISET 0.000")
        time.sleep(1.0)
        if FetchIset() != 0.000:
            sys.exit("バイポーラ電源が命令を受け付けません")

    power.write("OUT 1")
    time.sleep(1.0)
    powerout = power.query("OUT?")
    if powerout == 'OUT 001\r\n':
        print('バイポーラ電源の出力がONになりました')

    else:
        print('バイポーラ電源の出力がONになっていません')

    print('\n初期化が完了しました。\nコマンドリストを開くにはcommandと入力してください。\n')


def finary():
    if power.query("OUT?") == 'OUT 000\r\n':
        print("終了可能です")
        return
    if FetchIset() != 0.000:
        CtlIoutMA(0, 0.1)
        time.sleep(1.0)
        if FetchIset() != 0.000:
            sys.exit("バイポーラ電源が命令を受け付けません")
    power.write("OUT 0")
    time.sleep(1.0)
    if not CanOutput():
        print('バイポーラ電源の出力がOFFになりました')
    else:
        print('バイポーラ電源が命令を受け付けません!')


def cmdlist():
    print("""
    help        :コマンド一覧
    measure     :測定
    ctliout     :出力電流を設定
    status      :現時点の測定結果を表示
    savestatus  :現時点の測定結果をファイルに保存
    exit        :終了
    """)


def cmdCtlIout():
    print("mA unit in target")
    target = int(input(">>>>>"))
    print("mA unit step")
    step = int(input(">>>>>"))
    CtlIoutMA(target, step)


def main():
    global UNSAFE
    while True:
        cmd = input(">>>")
        if cmd in {"h", "help", "c", "cmd", "command"}:
            cmdlist()
        elif cmd in {"quit", "exit", "end"}:
            break

        elif cmd == "measure":
            measure()

        elif cmd == "ctlIout":
            cmdCtlIout()

        elif cmd == "status":

            iset, iout, h, vout = loadStatus()
            print("ISET= " + str(iset), "IOUT= " + str(iout), "Field= " + str(h), "VOUT= " + str(vout))

        elif cmd == "savestatus":
            now = datetime.datetime.now()
            startTime = "%s-%s-%s_%s-%s-%s" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
            savefile = startTime + ".csv"
            gen_csv_header(savefile, startTime)
            iset, iout, h, vout = loadStatus()
            print("ISET= " + str(iset), "IOUT= " + str(iout), "Field= " + str(h), "VOUT= " + str(vout))
            addSaveStatus(savefile, (iset, iout, h, vout))

        elif cmd == "unsafe":
            UNSAFE = True
            print("enable unsafemode")
        elif cmd == "safe":
            UNSAFE = False
            print("disable unsafemode")
        elif UNSAFE and cmd == "tgw":
            print("Terget: gauss,Method: Write")
            odr = input("###")
            if odr == "":
                continue
            elif odr in {"c", "b", "back", "bk", "q"}:
                continue
            elif len(odr) <= 2:
                continue
            else:
                usWriteGauss(odr)

        elif UNSAFE and cmd == "tpw":
            print("Terget: Power,Method: Write")
            odr = input("###")
            if odr == "":
                continue
            elif odr in {"c", "b", "back", "bk", "q"}:
                continue
            elif len(odr) <= 2:
                continue
            else:
                usWritePower(odr)
        elif UNSAFE and cmd == "tgq":
            print("Terget: Gauss,Method: Query")
            odr = input("###")
            if odr == "":
                continue
            elif odr in {"c", "b", "back", "bk", "q"}:
                continue
            elif len(odr) <= 2:
                continue
            else:
                usQueryGauss(odr)
        elif UNSAFE and cmd == "tpq":
            print("Terget: Power,Method: Query")
            odr = input("###")
            if odr == "":
                continue
            elif odr in {"c", "b", "back", "bk", "q"}:
                continue
            elif len(odr) <= 2:
                continue
            else:
                usQueryPower(odr)
        else:
            print("""invaild command\nPlease type "h" or "help" """)


if __name__ == '__main__':
    init()
    main()
    finary()
    exit(0)
