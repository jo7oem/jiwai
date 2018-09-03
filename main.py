"""

磁歪測定用自動測定プログラム
Run > Run Moduleを選択するかF5キーを押してプログラム開始

測定電流値を変更する場合
下に「メイン測定処理」のサブルーチンがあるので、そのはじめにあるリストを書き変える
ただし小数点以下2桁まで

"""
import visa
import time
import os
import sys
import datetime

rm = visa.ResourceManager()
gauss = rm.open_resource("ASRL3::INSTR")
power = rm.open_resource("GPIB0::4::INSTR")


def ioutfunc():  # 出力電流の関数
    global iout
    global current

    iout = power.query("IOUT?")
    current = iout.translate(str.maketrans('', '', 'IOUT A\r\n'))  # 指定文字を文字列から削除


def fieldfunc():  # 測定磁界の関数
    global readfield
    global field
    global fieldvalue

    readfield = gauss.query("FIELD?") + gauss.query("FIELDM?") + gauss.query("UNIT?")
    value = gauss.query("FIELD?")
    field = readfield.translate(str.maketrans('', '', ' \r\n'))
    fieldvalue = value.translate(str.maketrans('', '', ' \r\n'))


"""
現時刻取得
"""


def timeget():  # PCから日付と時刻を読み込む
    now = datetime.datetime.now()
    print("%s年%s月%s日　%s時%s分%s秒" % (now.year, now.month, now.day, now.hour, now.minute, now.second))


"""
関数リスト
"""


def command():  # ユーザーコマンド一覧の表示
    print('init     : バイポーラ電源の初期化')
    print('app      : 磁場を3kGになるように印加する')
    print('meas     : 測定を行う')
    print('iout     : バイポーラ電源の出力電流値を表示する')
    print('field    : ガウスメーターの測定磁界を表示する')
    print('end      : 終了')
    print('Ctrl + C : 強制停止')
    print('\n')


"""
初期化処理(バイポーラ電流値をゼロにする)
"""


def init():
    # バイポーラ電源の読み込み
    ioutfunc()
    global current
    meascurrent = "%.2f" % (float(current))

    if float(current) < 0.009 and float(current) > -0.009:  # 文字列をfloatに変換して比較
        print("initialized\n")

    else:
        setcurrent = int(float(current) * 1000)  # 読込電流を1000倍してint型に変換
        print("initializing...")

        if float(current) > 0.009:  # 電流値が0.009Aより大きいときの処理
            for i in range(setcurrent, 0, -10):  # 電流値を整数でループ
                count = 0
                while 1:
                    value = i / 1000  # 電流値を小数にする
                    iset = "ISET " + "%.2f" % (value)  # 小数点以下2桁
                    power.write(iset)
                    ioutfunc()
                    over = "%.2f" % (value + 0.01)  # 設定電流値より0.01A大きい電流値を格納
                    under = "%.2f" % (value - 0.01)  # 設定電流値より0.01A小さい電流値を格納
                    meascurrent = "%.2f" % (float(current))  # 測定電流値をfloat型に変換し、桁を揃える
                    time.sleep(0.01)

                    count += 1

                    if float(meascurrent) <= float(over) and float(meascurrent) >= float(under):
                        break

                    elif count == 10:  # 10回リトライしたらタイムアウト
                        print("timeout")
                        init()  # 初期化
                        break

                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) < 0.02:  # 測定電流値が0.02A以下のとき
                    power.write("ISET 0")  # 電流値を0Aにする

            time.sleep(1.0)



        elif float(current) < -0.009:  # 電流値が-0.009Aより小さいときの処理
            for i in range(current, 0, 10):
                count = 0
                while 1:
                    value = i / 1000
                    iset = "ISET " + "%.2f" % (value)
                    power.write(iset)
                    ioutfunc()
                    over = "%.2f" % (value + 0.01)
                    under = "%.2f" % (value - 0.01)
                    meascurrent = "%.2f" % (float(current))
                    time.sleep(0.01)

                    count += 1

                    if float(meascurrent) <= float(over) and float(meascurrent) >= float(under):
                        break

                    elif count == 10:  # 10回リトライしたらタイムアウト
                        print("timeout")
                        init()  # 初期化
                        break

                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) > -0.02:
                    power.write("ISET 0")

            time.sleep(1.0)

        print("initialized\n")


"""
磁場印加処理 0kG(または任意)⇒3kG
"""
setup = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]  # この電流値になったとき磁界を読む


def app_plus():  # 磁界を3kGまで印加する処理
    ioutfunc()
    global current
    meascurrent = "%.2f" % (float(current))

    print("field applying...")
    current = int(float(current) * 100)

    for i in range(current, 320, 10):  # 現在値~3.1Aまで0.1Aずつ上昇させる
        count = 0  # カウントリセット
        while 1:
            value = i / 100
            iset = "ISET " + "%.2f" % (value)  # 小数点以下2桁
            power.write(iset)
            ioutfunc()
            over = "%.2f" % (value + 0.01)
            under = "%.2f" % (value - 0.01)
            meascurrent = "%.2f" % (float(current))
            time.sleep(1.0)

            count += 1  # カウント追加

            if float(meascurrent) <= float(over) and float(meascurrent) >= float(under):
                break

            elif count == 10:  # 10回リトライしたらタイムアウト
                print("timeout")
                while 1:
                    print('if you want initialize --> init')
                    print('apply +3kG --> plus')
                    print('apply -3kG --> minus')
                    print('\n')
                    cmd = input('input any commands >>> ')

                    if cmd == 'init':  # 初期化
                        init()
                        break

                    elif cmd == 'plus':  # +3kG印加
                        app_plus()
                        break

                    elif cmd == 'minus':  # -3kG印加
                        app_minus()
                        break

                    elif cmd == 'command':  # コマンドリストの表示
                        command()

                    elif cmd == 'end':  # 終了コマンド
                        init()

                        ioutfunc()
                        meascurrent = "%.2f" % (float(current))

                        if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:  # 測定電流値が0近傍のとき
                            power.write("OUT 0")  # 電流出力をOFF
                            print('turn off state')
                            break

                    elif cmd == 'command':
                        command()

                    else:
                        print('this command is not define or you cannot use now')

        for j in setup:  # setupのリストと比較
            if value == j:  # リスト内の電流値とマッチしていれば測定
                print('measuring...')
                time.sleep(3.0)  # 3sec待機
                ioutfunc()
                print(current + 'A')  # 測定電流値を表示
                fieldfunc()
                print(field + '\n')  # 測定磁界を表示

        if value == 3.1:  # 電流が3.1Aのとき
            count = 0  # カウントリセット
            while 1:
                count += 1  # カウント追加
                power.write("ISET 3.18")  # 電流値を3.18Aに微調整
                time.sleep(3.0)
                fieldfunc()

                if float(fieldvalue) >= 3:  # 測定磁界が3kG以上のとき
                    break

                elif count == 10:  # リトライが10回のとき
                    print('ガウスメーターのプローブを確認してください')
                    break

            ioutfunc()
            print(current + 'A')

            fieldfunc()
            print(field + '\n')


"""
磁場印加処理 0kG(または任意)⇒-3kG
"""


def app_minus():  # 磁界を-3kGまで印加する処理
    ioutfunc()
    global current
    meascurrent = "%.2f" % (float(current))

    print("field applying...")
    current = int(float(current) * 100)

    for i in range(current, -320, -10):  # 現在値~-3.1Aまで0.1Aずつ変化させる
        count = 0
        while 1:
            value = i / 100
            iset = "ISET " + "%.2f" % (value)  # 小数点以下2桁
            power.write(iset)
            ioutfunc()
            over = "%.2f" % (value + 0.01)
            under = "%.2f" % (value - 0.01)
            meascurrent = "%.2f" % (float(current))
            time.sleep(1.0)

            count += 1

            if float(meascurrent) <= float(over) and float(meascurrent) >= float(under):
                break

            elif count == 10:  # 10回リトライしたらタイムアウト
                print("timeout")
                while 1:
                    print('if you want initialize --> init')
                    print('apply +3kG --> plus')
                    print('apply -3kG --> minus')
                    print('\n')
                    cmd = input('input any commands >>> ')

                    if cmd == 'init':  # 初期化
                        init()
                        break

                    elif cmd == 'plus':  # +3kG印加
                        app_plus()
                        break

                    elif cmd == 'minus':  # -3kG印加
                        app_minus()
                        break

                    elif cmd == 'command':  # コマンドリストの表示
                        command()

                    elif cmd == 'end':  # 終了コマンド
                        init()

                        ioutfunc()
                        meascurrent = "%.2f" % (float(current))

                        if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:
                            power.write("OUT 0")
                            print('turn off state')
                            break

                    else:
                        print('this command is not define or you cannot use now')

        for j in setup:  # setupのリストと比較
            if value == j:  # リスト内の電流値とマッチしていれば測定
                print('measuring...')
                time.sleep(3.0)  # 3sec待機
                ioutfunc()
                print(current + 'A')  # 測定電流値を表示
                fieldfunc()
                print(field + '\n')  # 測定磁界を表示

        if value == -3.1:  # 電流が-3.1Aのとき
            count = 0  # カウントリセット
            while 1:
                count += 1  # カウント追加
                power.write("ISET -3.18")  # 電流値を-3.18Aに微調整
                time.sleep(3.0)
                fieldfunc()

                if float(fieldvalue) >= -3:  # 測定磁界が-3kGのとき
                    break

                elif count == 10:  # リトライが10回のとき
                    print('ガウスメーターのプローブを確認してください')
                    break

            ioutfunc()
            print(current + 'A')

            fieldfunc()
            print(field + '\n')


"""
測定準備処理
"""


def app():
    ioutfunc()
    global current
    meascurrent = "%.2f" % (float(current))

    if float(meascurrent) >= 0.009 or float(meascurrent) <= -0.009:  # 電流値が0近傍でなければアラート
        print("field is not initialized!!\n")
        while 1:
            print('initialize --> init ')
            print('apply +3kG --> plus')
            print('apply -3kG --> minus')
            print('command list --> command')
            print('\n')
            cmd = input('input any commands >>> ')
            print('\n')

            if cmd == 'init':  # 初期化
                init()

            elif cmd == 'plus':  # +3kG印加
                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) >= 3:  # 電流値が3A以上のとき
                    print('field is already applied!!')

                elif float(meascurrent) < 3:  # 電流値が3Aより小さいとき
                    app_plus()
                    print('you can start measurement\n')
                    break

            elif cmd == 'minus':  # -3kG印加
                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) <= -3:  # 電流値が-3A以下のとき
                    print('field is already applied!!')

                elif float(meascurrent) > -3:  # 電流値が-3Aより大きいとき
                    app_minus()
                    print('you can start measurement\n')
                    break

            elif cmd == 'command':  # コマンドリストを表示
                command()

            elif cmd == 'end':  # 終了コマンド
                init()

                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:
                    power.write("OUT 0")
                    print('turn off state')
                    break

            else:
                print('this command is not define or you cannot use now')


    elif float(meascurrent) <= 0.009 and float(meascurrent) >= -0.009:  # 文字列をfloatに変換して比較
        while 1:
            print('apply +3kG --> plus')
            print('apply -3kG --> minus')
            print('command list --> command')
            print('\n')
            cmd = input('input any commands >>> ')
            print('\n')

            if cmd == 'init':  # 初期化
                init()

            elif cmd == 'plus':  # +3kG印加
                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) >= 3:
                    print('field is already applied!!')

                elif float(meascurrent) < 3:
                    app_plus()
                    break

            elif cmd == 'minus':  # -3kG印加
                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) <= -3:
                    print('field is already applied!!')

                elif float(meascurrent) > -3:
                    app_minus()
                    break

            elif cmd == 'command':  # コマンドリストの表示
                command()

            elif cmd == 'end':  # 終了コマンド
                init()

                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:
                    power.write("OUT 0")
                    print('turn off state')
                    break

            else:
                print('this command is not define or you cannot use now')


"""
メイン測定処理
"""
# ユーザー設定電流値(この電流値の時に5sec止まる）
# 測定点を増やす場合は、カメラの録画時間を考慮して設定すること。(設定後、録画時間内に収まるか試すのが望ましい)
# 25点測定で約5分30秒
applied_field1 = [3.00, 2.00, 1.00, 0.75, 0.60, 0.50, 0.40, 0.30, 0.20, 0.15, 0.10, 0.05, 0.00]
applied_field2 = [-0.05, -0.10, -0.15, -0.20, -0.30, -0.40, -0.50, -0.60, -0.75, -1.00, -2.00, -3.00]


def meas():
    ioutfunc()
    meascurrent = "%.2f" % (float(current))

    # 電流が3Aもしくは-3A流れていなければアラート
    if float(meascurrent) <= 3 and float(meascurrent) >= -3:
        print('please execute this command after applied a magnetic field!!\n')
        while 1:
            print('initialize --> init ')
            print('apply +3kG --> plus')
            print('apply -3kG --> minus')
            print('command list --> command')
            print('\n')
            cmd = input('input any commands >>> ')
            print('\n')

            if cmd == 'init':  # 初期化
                init()
                break

            elif cmd == 'plus':  # +3kG印加
                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) >= 3:
                    print('field is already applied!!')

                elif float(meascurrent) < 3:
                    app_plus()
                    break

            elif cmd == 'minus':  # -3kG印加
                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) <= -3:
                    print('field is already applied!!')

                elif float(meascurrent) > -3:
                    app_minus()
                    break

            elif cmd == 'command':  # コマンドリストの表示
                command()

            elif cmd == 'end':  # 終了コマンド
                init()

                ioutfunc()
                meascurrent = "%.2f" % (float(current))

                if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:
                    power.write("OUT 0")
                    print('turn off state')
                    break

            else:
                print('this command is not define or you cannot use now')



    # 電流が3A流れていれば+3kG ⇒ -3kGまで測定
    elif float(meascurrent) >= 3:
        print('start measurement +3kG ⇒ -3kG')
        timeget()

        for i in range(3200, -3200, -10):  # 3.2Aから-3.1Aまで0.1Aずつ減少させる
            if i >= 0:  # 設定電流値が正のときの処理
                count = 0
                while 1:
                    value = i / 1000
                    iset = "ISET " + "%.2f" % (value)  # 小数点以下2桁
                    power.write(iset)
                    ioutfunc()
                    over = "%.2f" % (value + 0.01)
                    under = "%.2f" % (value - 0.01)
                    meascurrent = "%.2f" % (float(current))
                    time.sleep(0.1)
                    count += 1

                    if float(meascurrent) <= float(over) and float(meascurrent) >= float(under):
                        break

                    elif count == 10:  # 10回リトライしたらタイムアウト
                        print("timeout")
                        while 1:
                            print('if you want initialize --> init')
                            print('if you want apply to +3kG --> plus')
                            print('if you want apply to -3kG --> minus')
                            print('\n')
                            cmd = input('input any commands >>> ')

                            if cmd == 'init':  # 初期化
                                init()
                                break

                            elif cmd == 'plus':  # +3kG印加
                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) >= 3:
                                    print('field is already applied!!')

                                elif float(meascurrent) < 3:
                                    app_plus()
                                    break

                            elif cmd == 'minus':  # -3kG印加
                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) <= -3:
                                    print('field is already applied!!')

                                elif float(meascurrent) > -3:
                                    app_minus()
                                    break

                            elif cmd == 'command':  # コマンドリストの表示
                                command()

                            elif cmd == 'end':  # 終了コマンド
                                init()

                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:
                                    power.write("OUT 0")
                                    print('turn off state')
                                    break

                            else:
                                print('this command is not define or you cannot use now')

                for j in applied_field1:  # applied_field1のリストと比較
                    if value == j:  # リスト内の電流値とマッチしていれば測定
                        print('measuring...')
                        timeget()
                        time.sleep(5.0)  # 5sec待機
                        timeget()
                        ioutfunc()
                        print(current + 'A')  # 測定電流値を表示
                        fieldfunc()
                        print(field + '\n')  # 測定磁界を表示

            elif i < 0:  # 設定電流値が負のときの処理
                count = 0
                while 1:
                    value = i / 1000
                    iset = "ISET " + "%.2f" % (value)  # 小数点以下2桁
                    power.write(iset)
                    ioutfunc()
                    over = "%.2f" % (value + 0.01)
                    under = "%.2f" % (value - 0.01)
                    meascurrent = "%.2f" % (float(current))
                    time.sleep(0.1)
                    count += 1

                    if float(meascurrent) <= float(over) and float(meascurrent) >= float(under):
                        break

                    elif count == 10:  # 10回リトライしたらタイムアウト
                        print("timeout")
                        while 1:
                            print('if you want initialize --> init')
                            print('if you want apply to +3kG --> plus')
                            print('if you want apply to -3kG --> minus')
                            print('\n')
                            cmd = input('input any commands >>> ')

                            if cmd == 'init':  # 初期化
                                init()
                                break

                            elif cmd == 'plus':  # +3kG印加
                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) >= 3:
                                    print('field is already applied!!')

                                elif float(meascurrent) < 3:
                                    app_plus()
                                    break

                            elif cmd == 'minus':  # -3kG印加
                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) <= -3:
                                    print('field is already applied!!')

                                elif float(meascurrent) > -3:
                                    app_minus()
                                    break

                            elif cmd == 'command':  # コマンドリストの表示
                                command()

                            elif cmd == 'end':  # 終了コマンド
                                init()

                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:
                                    power.write("OUT 0")
                                    print('turn off state')
                                    break

                            else:
                                print('this command is not define or you cannot use now')

                for j in applied_field2:  # applied_field1のリストと比較
                    if value == j:  # リスト内の電流値とマッチしていれば測定
                        print('measuring...')
                        timeget()
                        time.sleep(5.0)  # 5sec待機
                        timeget()
                        ioutfunc()
                        print(current + 'A')  # 測定電流値を表示
                        fieldfunc()
                        print(field + '\n')  # 測定磁界を表示

            elif i == -3100:  # 電流値が-3.1Aのとき
                print('finished\n')


    # 電流が-3A流れていれば-3kG ⇒ +3kGまで測定
    elif float(meascurrent) < -3:
        print('start measurment -3kG ⇒ +3kG')
        timeget()

        for i in range(-3200, 3200, 10):  # -3.2Aから3.1Aまで0.1Aずつ増加させる
            if i >= 0:  # 設定電流値が正のときの処理
                count = 0
                while 1:
                    value = i / 1000
                    iset = "ISET " + "%.2f" % (value)  # 小数点以下2桁
                    power.write(iset)
                    ioutfunc()
                    over = "%.2f" % (value + 0.01)
                    under = "%.2f" % (value - 0.01)
                    meascurrent = "%.2f" % (float(current))
                    time.sleep(0.1)
                    count += 1

                    if float(meascurrent) <= float(over) and float(meascurrent) >= float(under):
                        break

                    elif count == 10:  # 10回リトライしたらタイムアウト
                        print("timeout")
                        while 1:
                            print('if you want initialize --> init')
                            print('apply +3kG --> plus')
                            print('apply -3kG --> minus')
                            print('\n')
                            cmd = input('input any commands >>> ')

                            if cmd == 'init':  # 初期化
                                init()
                                break

                            elif cmd == 'plus':  # +3kG印加
                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) >= 3:
                                    print('field is already applied!!')

                                elif float(meascurrent) < 3:
                                    app_plus()
                                    break

                            elif cmd == 'minus':  # -3kG印加
                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) <= -3:
                                    print('field is already applied!!')

                                elif float(meascurrent) > -3:
                                    app_minus()
                                    break

                            elif cmd == 'command':  # コマンドリストの表示
                                command()

                            elif cmd == 'end':  # 終了コマンド
                                init()

                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:
                                    power.write("OUT 0")
                                    print('turn off state')
                                    break

                            else:
                                print('this command is not define or you cannot use now')

                for j in applied_field1:  # applied_field1のリストと比較
                    if value == j:  # リスト内の電流値とマッチしていれば測定
                        print('measuring...')
                        timeget()
                        time.sleep(5.0)  # 5sec待機
                        timeget()
                        ioutfunc()
                        print(current + 'A')  # 測定電流値を表示
                        fieldfunc()
                        print(field + '\n')  # 測定磁界を表示


            elif i < 0:  # 設定電流値が負のときの処理
                count = 0
                while 1:
                    value = i / 1000
                    iset = "ISET " + "%.2f" % (value)  # 小数点以下2桁
                    power.write(iset)
                    ioutfunc()
                    over = "%.2f" % (value + 0.01)
                    under = "%.2f" % (value - 0.01)
                    meascurrent = "%.2f" % (float(current))
                    time.sleep(0.1)
                    count += 1

                    if float(meascurrent) <= float(over) and float(meascurrent) >= float(under):
                        break

                    elif count == 10:  # 10回リトライしたらタイムアウト
                        print("timeout")
                        while 1:
                            print('if you want initialize --> init')
                            print('apply +3kG --> plus')
                            print('apply -3kG --> minus')
                            print('\n')
                            cmd = input('input any commands >>> ')

                            if cmd == 'init':  # 初期化
                                init()
                                break

                            elif cmd == 'plus':  # +3kG印加
                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) >= 3:
                                    print('field is already applied!!')

                                elif float(meascurrent) < 3:
                                    app_plus()
                                    break

                            elif cmd == 'minus':  # -3kG印加
                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) <= -3:
                                    print('field is already applied!!')

                                elif float(meascurrent) > -3:
                                    app_minus()
                                    break

                            elif cmd == 'command':
                                command()

                            elif cmd == 'end':  # 終了コマンド
                                init()

                                ioutfunc()
                                meascurrent = "%.2f" % (float(current))

                                if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:
                                    power.write("OUT 0")
                                    print('turn off state')
                                    break

                            else:
                                print('this command is not define or you cannot use now')

                for j in applied_field2:  # applied_field1のリストと比較
                    if value == j:  # リスト内の電流値とマッチしていれば測定
                        print('measuring...')
                        timeget()
                        time.sleep(5.0)  # 5sec待機
                        timeget()
                        ioutfunc()
                        print(current + 'A')  # 測定電流値を表示
                        fieldfunc()
                        print(field + '\n')  # 測定磁界を表示

            elif i == 3100:  # 電流値が3.1Aのとき
                print('finished\n')


"""
接続確認(始動動作)
"""
# ガウスメーターの接続確認
gaussconnection = gauss.query("*IDN?")

if gaussconnection == 'LSCI,MODEL421,0,010306\r\n':
    print("gauss : connection confirmed")

else:
    print("gauss : connection failed")

# バイポーラ電源の接続確認
powerconnection = power.query("IDN?")

if powerconnection == 'IDN PBX 40-10 VER1.13     KIKUSUI    \r\n':
    print("power : connection confirmed")

else:
    print("power : connection failed")

# バイポーラ電源の初期化
ioutfunc()
meascurrent = "%.2f" % (float(current))

if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:  # 文字列をfloatに変換して比較
    print("normal state\n")

else:
    print("abnormal state!!")
    init()

# ガウスメーターのレンジを最低感度に設定
gauss.write("RANGE 0")
time.sleep(1.0)
gaussrange = gauss.query("RANGE?")  # 現在の設定レンジの問い合わせ
if gaussrange == '0\r\n':
    print('ガウスメーターのレンジが最大に変更されました')

else:
    print('ガウスメーターのレンジを確認してください')

# バイポーラのOUTPUTをON
power.write("OUT 1")
time.sleep(1.0)
powerout = power.query("OUT?")
if powerout == 'OUT 001\r\n':
    print('バイポーラ電源の出力がONになりました')

else:
    print('バイポーラ電源の出力がONになっていません')

print('\n初期化が完了しました。\nコマンドリストを開くにはcommandと入力してください。\n')

"""
ユーザー入力
"""
while 1:
    cmd = input('input any commands >>> ')  # 設定したコマンドを入力
    print('\n')

    if cmd == 'command':  # コマンドリストの表示
        command()

    elif cmd == 'init':  # 初期化
        init()

    elif cmd == 'app':  # 3kGまで磁場印加
        app()

    elif cmd == 'meas':  # 測定処理
        meas()

    elif cmd == 'iout':  # バイポーラ電源の電流値を表示
        ioutfunc()
        print(current + 'A')

    elif cmd == 'field':  # ガウスメーターの測定磁界を表示
        fieldfunc()
        print(field)

    elif cmd == 'end':  # 終了コマンド
        init()

        ioutfunc()
        meascurrent = "%.2f" % (float(current))

        if float(meascurrent) < 0.009 and float(meascurrent) > -0.009:
            power.write("OUT 0")
            print('turn off state')
            break

    else:
        print('this command is not define')  # 指定されていないコマンドを打った場合



