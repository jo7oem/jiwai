# -*- coding: utf-8 -*-
import visa
import time
import sys
import csv
import datetime

DEBUG = True
if not DEBUG:
    rm = visa.ResourceManager()
    gauss = rm.open_resource("ASRL3::INSTR")
    power = rm.open_resource("GPIB0::4::INSTR")


class ControlError(Exception):
    """
    機器制御エラー
    期待に沿った動作を受け付けない時に投げられる
    """

    def __init__(self, message):
        self.message = message


def get_time_str() -> str:
    """
    現時刻を日本語に整形した文字列を返す
    ------------------------------
    :rtype: str
    :return: '2018-09-08 20:55:07'
    """
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def FetchIout() -> float:
    """
    現在の出力電流を取得する
    単位:A

    Notes
    -----
    Query  : "IOUT?"
    Answer : 'IOUT  0.012A\r\n'
    ----------
    :rtype: float
    :return: 0.012
    """
    iout = power.query("IOUT?")
    current = float(iout.translate(str.maketrans('', '', 'IOUT A\r\n')))
    return current


def FetchVout() -> float:
    """
    現在の出力電圧を取得する
    単位:V

    Notes
    -----
    Query  : "VOUT?"
    Answer : 'VOUT  0.015V\r\n'

    ----------
    :rtype: float
    :return: 0.015
    """
    vout = power.query("VOUT?")
    voltage = float(vout.translate(str.maketrans('', '', 'VOUT V\r\n')))
    return voltage


def FetchIset() -> float:
    """
    現在の設定出力電流を取得する
    単位:A

    Notes
    -----
    Query   : "ISET?"
    Answer  : 'ISET  0.010A\r\n'

    --------
    :rtype: float
    :return: 0.010
    """
    vout = power.query("ISET?")
    return float(vout.translate(str.maketrans('', '', 'ISET A\r\n')))


def FetchVset() -> float:
    """
    現在の設定出力電圧を取得する
    単位:V

    Notes
    -----
    Query   : "VSET?"
    Answer  : 'VSET  1.234V\r\n'

    --------
    :rtype: float
    :return: 1.234
    """
    vout = power.query("VSET?")
    return float(vout.translate(str.maketrans('', '', 'VSET V\r\n')))


def SetIset(i: float):
    """
    出力電流を設定する。
    単位: A

    Notes
    -----
    Write   : "ISET 1.234"

    --------
    :param i: 設定電圧[A]
    :return:
    """
    power.write("ISET {0:.3f}".format(i))


def FetchIFine() -> int:
    """
    現在の電流ファイン値を取得する
    単位:int8(-128~+127)

    Notes?not real answer
    -----
    Query   : "IFINE?"
    Answer  : 'IFINE 1V\r\n'

    --------
    :rtype: int
    :return: 1
    """
    ifine = power.query("IFINE?")
    return int(ifine.translate(str.maketrans('', '', 'IFINE\r\n')))


def SetIFine(fine: int):
    """
    電流ファイン値を設定する
    単位:int8(-128~127)

    Notes
    -----
    Write   : "IFINE 3"

    --------
    :param fine:ファイン値
    :return:
    """
    if fine < -128:
        fine = -128
    elif fine > 127:
        fine = 127
    power.write("IFINE " + str(fine))


def allow_power_output(operation: bool) -> None:
    """
    安全にバイポーラ電源の出力をON/OFFにする

    Raise
    -----
    ControlError   : 制御できないとき

    --------
    :param operation: 出力を許可するか？
    :return: None
    """
    now_output = CanOutput()
    if now_output == operation:
        return
    iset = FetchIset()
    if iset != 0:
        if not now_output:
            SetIset(0)
        else:
            CtlIoutMA(0)
    time.sleep(0.1)
    if operation:
        power.write("OUT 1")
    else:
        power.write("OUT 0")
    time.sleep(0.1)
    if CanOutput() == operation:
        return
    raise ControlError("バイポーラ電源出力制御失敗")


def SetIsetMA(current: int) -> None:
    SetIset(mA_to_a(current))


def mA_to_a(current: int) -> float:
    """
    単位を変換する

    --------
    :param current: 電流[mA] 1234
    :return: 電流[A] 1.234
    """
    return float("{0:.3f}".format(current / 1000))


def average(il: list) -> float:
    return sum(il) / len(il)


def A_to_mA(current: float) -> int:
    """
    単位を変換する

    --------
    :param current: 電流[A] 1.234
    :return: 電流[A] 1234
    """
    return int(current * 1000)


def FetchField() -> float:
    """
    磁束密度を取得する
    単位は取得できない

    Notes
    -----
    Query   : "FIELD?"
    Answer  : "102.3"

    --------
    :return: 102.3
    """
    value = gauss.query("FIELD?")
    return float(value.translate(str.maketrans('', '', ' \r\n')))


def ReadField() -> str:
    field_str = gauss.query("FIELD?") + gauss.query("FIELDM?") + gauss.query("UNIT?")
    return field_str.translate(str.maketrans('', '', ' \r\n'))


def loadStatus() -> [float, float, float, float]:
    """
    各ステータスをまとめて取得する

    --------
    :return: 5.000,5.003,102.3,2.432
    """
    iout = FetchIout()
    iset = FetchIset()
    vout = FetchVout()
    field = FetchField()
    return iset, iout, field, vout


def addSaveStatus(filename: str, status: tuple) -> None:
    """
    ファイルにステータスを追記する

    --------
    :param filename: 書き込むファイル名
    :param status: 書き込むデータ
    :return:
    """
    with open(filename, mode='a', encoding="utf-8")as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(status)


def usWriteGauss(command: str) -> None:
    gauss.write(command)


def usWritePower(command: str) -> None:
    power.write(command)


def CanOutput() -> bool:
    """
    電源出力が可能かを返す
    --------
    :return:
    """
    if power.query("OUT?") == 'OUT 001\r\n':
        return True
    return False


def auto_IFine_step(target, fine=0) -> int:
    """
    Auto IFINEの単純な実装
    与えられたFINE値から1ずつ変えて試す
    調整幅が5以下ならばこちらのほうが早い

    --------
    :param target: 目標電流[mA]
    :param fine: 初期FINE値
    :return: 設定されたFINE値
    """
    SetIFine(fine)
    time.sleep(0.05)
    fineadd = None
    while True:
        current = A_to_mA(FetchIout())
        diff = target - current
        if abs(diff) <= 1:
            return fine
        elif diff > 0 and (fine == 127 or not fineadd):
            return fine
        elif diff < 0 and (fine == -128 or fineadd):
            return fine
        elif diff > 0:
            fine = fine + 1
            fineadd = True
        else:  # target<current
            fine = fine - 1
            fineadd = False
        SetIFine(fine)
        time.sleep(0.04)


def auto_IFine_binary(target: int, fine: int, ttl: int) -> int:
    """
    auto IFINEの2分探索実装
    期待値6ステップ,最悪-128のみ8,大半は7ステップで完了する

    --------
    :param target: 目標電流[mA]
    :param fine: 測定するFINE値
    :param ttl: 残りステップ数
    :return:    最終FINE値
    """
    SetIFine(fine)
    time.sleep(0.05)
    current = A_to_mA(FetchIout())
    if abs(current - target) <= 1:
        return fine
    if ttl == 0 and fine == -127:
        auto_IFine_binary(target, -128, 0)
        return auto_IFine_binary(target, -128, 0)
    if ttl == 0:
        return fine
    ttl = ttl - 1
    if target > current:
        return auto_IFine_binary(target, fine + 2 ** ttl, ttl)
    else:
        return auto_IFine_binary(target, fine - 2 ** ttl, ttl)


FINECONST = list()  # diff/fine の値を蓄積していく


def CtlIoutMA(target, step=100, auto_fine=False) -> None:
    """
    安全に電流を設定値にあわせる
    limitに引っかからないようにstep ごとに徐々に電流を変化させる
    --------
    :param target:  目標電流[mA]
    :param step:    変化させる電流幅[mA]
    :param auto_fine: autoFINEを使用するか
    """
    current = A_to_mA(FetchIout())
    if target == A_to_mA(FetchIset()):
        return

    if current < target:
        transit_current = list(range(current, int(target), abs(int(step))))  # 経由電流値
    else:
        transit_current = list(range(current, int(target), abs(int(step)) * -1))

    for mA in transit_current:
        SetIsetMA(mA)
        time.sleep(0.1)

    SetIsetMA(target)
    time.sleep(0.1)
    diff_iout = A_to_mA(FetchIout()) - target

    if not auto_fine or abs(diff_iout) <= 1:
        return

    global FINECONST
    if len(FINECONST) < 10:
        fine = (auto_IFine_binary(target, 0, 7))
    else:
        sfine = int(diff_iout * average(FINECONST))
        fine = auto_IFine_step(sfine)

    if fine == 127 or fine == 0 or fine == -128:
        return
    FINECONST.append(diff_iout / fine)


def gen_csv_header(filename, time_str) -> None:
    print("測定条件等メモ記入欄")
    memo = input("memo :")
    with open(filename, mode='a', encoding="utf-8")as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(["開始時刻", time_str])
        writer.writerow(["memo", memo])
        writer.writerow(["#####"])
        writer.writerow(["設定電流:ISET[A]", "出力電流:IOUT[A]", "磁界:H[Gauss]", "出力電圧:VOUT[V]"])


def measure() -> None:
    try:
        allow_power_output(True)
    except ControlError:
        print("[FATAL]バイポーラ電源制御エラー!!")
        return

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
    check_point = [0, 5000, 0, -5000, 0]
    mesh = 500
    step = 100
    count = 0

    start_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # ex.'2018-09-08_21-00-29'
    savefile = start_time + ".csv"
    gen_csv_header(savefile, start_time)

    for i in check_point:
        if count == 0:
            CtlIoutMA(i, step)
            count += 1
            continue

        iset_current = int(FetchIset() * 1000)
        if i >= iset_current:
            recode_point = range(iset_current, i, abs(mesh))
        else:
            recode_point = range(iset_current, i, abs(mesh) * -1)

        for j in recode_point:
            CtlIoutMA(j, step, True)  # 測定電流
            time.sleep(0.3)
            iset, iout, h, vout = loadStatus()
            print("ISET= " + str(iset), "IOUT= " + str(iout), "Field= " + str(h), "VOUT= " + str(vout))
            addSaveStatus(savefile, (iset, iout, h, vout))

        CtlIoutMA(i, step, True)  # 測定電流
        time.sleep(0.3)
        iset, iout, h, vout = loadStatus()
        print("ISET= " + str(iset), "IOUT= " + str(iout), "Field= " + str(h), "VOUT= " + str(vout))
        addSaveStatus(savefile, (iset, iout, h, vout))
        continue

    end_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # ex.'2018-09-08_21-00-29'
    with open(savefile, mode='a', encoding="utf-8")as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(["終了時刻", end_time])
    print("Done")


def usQueryGauss(s) -> None:
    print("=>: " + s)
    print("\n")
    print("<=: " + gauss.query(s))


def usQueryPower(s) -> None:
    print("=>: " + s)
    print("\n")
    print("<=: " + power.query(s))


def init() -> None:
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
    try:
        allow_power_output(True)
    except Exception:
        print("バイポーラ電源制御異常")
        raise
    print('\n初期化が完了しました。\nコマンドリストを開くにはcommandと入力してください。\n')


def after_operations() -> None:
    print("終了処理を開始します。")
    try:
        allow_power_output(False)
    except ControlError:
        print("バイポーラ電源制御異常")
        CtlIoutMA(0)
    finally:
        print("終了")


def cmdlist() -> None:
    print("""
help        :コマンド一覧
measure     :測定
ctliout     :出力電流を設定
status      :現時点の測定結果を表示
savestatus  :現時点の測定結果をファイルに保存
exit        :終了
""")


def cmdCtlIout() -> None:
    print("mA unit in target")
    target = int(input(">>>>>"))
    print("mA unit step")
    step = int(input(">>>>>"))
    CtlIoutMA(target, step)


def main() -> None:
    unsafe = False
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
            start_time = "%s-%s-%s_%s-%s-%s" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
            savefile = start_time + ".csv"
            gen_csv_header(savefile, start_time)
            iset, iout, h, vout = loadStatus()
            print("ISET= " + str(iset), "IOUT= " + str(iout), "Field= " + str(h), "VOUT= " + str(vout))
            addSaveStatus(savefile, (iset, iout, h, vout))

        elif cmd == "unsafe":
            unsafe = True
            print("enable unsafemode")
        elif cmd == "safe":
            unsafe = False
            print("disable unsafemode")
        elif unsafe and cmd == "tgw":
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

        elif unsafe and cmd == "tpw":
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
        elif unsafe and cmd == "tgq":
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
        elif unsafe and cmd == "tpq":
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
    after_operations()
    exit(0)
