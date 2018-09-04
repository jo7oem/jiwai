#!/bin/python3
# -*- coding: utf-8 -*-
import visa
import time
import os
import sys
import datetime

UNSAFE = False
DEVENV = True
if DEVENV == False:
    rm = visa.ResourceManager()
    gauss = rm.open_resource("ASRL3::INSTR")
    power = rm.open_resource("GPIB0::4::INSTR")


def FetchIout():  # 出力電流の関数
    iout = power.query("IOUT?")
    return float(iout.translate(str.maketrans('', '', 'IOUT A\r\n')))  # 指定文字を文字列から削除


def FetchVout():  # 出力電流の関数
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


def SetIsetMA(i):
    SetIset(float(i) / 1000)


def FetchField():  # 測定磁界の関数
    value = gauss.query("FIELD?")
    return value.translate(str.maketrans('', '', ' \r\n'))


def ReadField():  # 測定磁界の関数
    readfield = gauss.query("FIELD?") + gauss.query("FIELDM?") + gauss.query("UNIT?")
    return readfield.translate(str.maketrans('', '', ' \r\n'))


def usWriteGauss(s):
    gauss.write(s)


def usWritePower(s):
    power.write(s)


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
        power.write("ISET 0.000")
        time.sleep(1.0)
        if FetchIset() != 0.000:
            sys.exit("バイポーラ電源が命令を受け付けません")
    power.write("OUT 0")
    time.sleep(1.0)
    powerout = power.query("OUT?")
    if powerout == 'OUT 000\r\n':
        print('バイポーラ電源の出力がOFFになりました')
    else:
        print('バイポーラ電源が命令を受け付けません!')


def cmdlist():
    print("""
    コマンドリスト
    A
    B
    """)


def main():
    global UNSAFE
    while True:
        cmd = input(">>>")
        if cmd in {"h", "help", "c", "cmd", "command"}:
            cmdlist()
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
    # finary()


if __name__ == '__main__':
    # init()
    main()
