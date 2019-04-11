# -*- coding: utf-8 -*
__author__ = 'double k'

"""
唤醒APP
工作位置
x/2
y/1.05
"""

import time
import traceback
import os
import re
import configparser
import datetime
import random
import sched
scheduler = sched.scheduler(time.time, time.sleep)
path = os.getcwd() + "\\DingDingClockIn\\"
config = configparser.ConfigParser(allow_no_value=False)
# .cfg路径根据自己实际情况修改
config.read( path + "dingding.cfg")
go_hour = int(config.get("time", "go_hour"))
back_hour = int(config.get("time", "back_hour"))
# go_hour = 8
# back_hour = 17
def wakeUpTheScreen():
    displayPowerState = os.popen(
        "adb shell \"dumpsys power | grep 'Display Power: state=' \"").read().strip('\n')
    if displayPowerState == 'Display Power: state=OFF':
        print("唤醒屏幕")
        os.system("adb shell \"input keyevent 26\"")
    else:
        print("屏幕已开启不需要唤醒")
def deblocking():
    isStatusBarKeyguard = os.popen(
        "adb shell \"dumpsys window policy|grep isStatusBarKeyguard \"").read().strip(
        '\n')
    # print(isStatusBarKeyguard)
    # return
    if "isStatusBarKeyguard=false" in isStatusBarKeyguard:
        time.sleep(2)
        print("解锁屏保")
        # 滑动解锁
        os.system('adb shell \"input swipe  300 1000 300 500\"')
        # time.sleep(1)
        # print("输入密码")
        # os.system('adb shell \"input text 95729\"')
    else:
        print("屏幕已解锁不需要再次解锁")

def screencap(hourtype):
    if hourtype == 2:
        pref = "go"
    else:
        pref = "back"
    fileName = pref + "-" + time.strftime("%Y%m%d%H%M%S") + ".png"
    recordPath = path + "record\\"
    dir = recordPath + fileName
    os.system("adb shell screencap -p sdcard/screen.png")
    os.system("adb pull sdcard/screen.png %s" % dir)
    os.system("adb shell rm -r sdcard/screen.png")
    print("screencap to computer success")
def screenshot_prepare(hourtype):
    """
    打开APP
    :return:
    """
    try:
        """
        打开app 
        """
        appName = "com.alibaba.android.rimet"
        # 唤醒屏幕
        wakeUpTheScreen()
        # 解锁
        deblocking()

        time.sleep(1)
        # 获取正在启动的APP
        mFocusedActivity = os.popen(
            "adb shell \"dumpsys activity | grep 'mFocusedActivity' \"").read().strip('\n')
        if appName in mFocusedActivity:
            print("APP已启动，停止APP，等待重新启动")
            os.system("adb shell \"am force-stop %s\"" % (appName,))
        time.sleep(1)
        print("启动app")
        os.system(
            "adb shell \"monkey -p %s -c android.intent.category.LAUNCHER 1\"" % (appName, ))
        xy = os.popen("adb shell wm size").read().strip('\n')

        xyobj = re.search(re.compile("\d+x\d+"), xy).group().split("x")
        if len(xyobj) == 2:
            time.sleep(8)
            # 截屏
            screencap(hourtype)
            time.sleep(2)
            x = int(xyobj[0]) / 2
            y = int(xyobj[1]) / 1.05
            os.system('adb shell \"input tap %s %s\"' % (x, y))
    except Exception:
        print("screenshot_prepare error")
        # traceback.print_exc()
        # exit(-1)


# 随机打卡时间段
def random_minute():
    return random.randint(30,50)

# 包装循环函数，传入随机打卡时间点
def incode_loop(func,minute):
    """
    包装start_loop任务调度函数，主要是为了传入随机分钟数。保证在不打卡的情况下能保持分钟数不变。
    :param func: star_loop
    :param minute: 随机分钟数
    :return: None
    """
    # 判断时间当超过上班时间则打下班卡。否则则打上班卡。
    if datetime.datetime.now().hour >=go_hour and datetime.datetime.now().hour < back_hour :
        # 用来分类上班和下班。作为参数传入任务调度
        hourtype = 1
        print("下班打卡-下次将在", str(back_hour), ":", str(minute), "打卡")
    else:
        hourtype = 2
        print("上班打卡-下次将在", str(go_hour), ":", str(minute), "打卡")
    #执行任务调度函数
    func(hourtype, minute)


# 任务调度
def start_loop(hourtype,minute):
    """
    每次循环完成，携带生成的随机分钟数来再次进行循环，当打卡后，再重新生成随机数
    :param hourtype: 设置的上班时间点
    :param minute: 随机生成的分钟数（30-55）
    :return: None
    """
    now_time = datetime.datetime.now()
    now_hour = now_time.hour
    now_minute = now_time.minute
    hourtype = hourtype
    # 上班，不是周末（双休），小时对应，随机分钟对应
    if hourtype == 2 and now_hour == go_hour and now_minute == minute and is_weekend():
        print("hourtype", str(hourtype), "now_hour", str(now_hour), "now_minute", str(now_minute))
        random_time = random_minute()
        screenshot_prepare(hourtype)
        scheduler.enter(0,0,incode_loop,(start_loop,random_time,))
        return
    if hourtype == 1 and now_hour == back_hour and now_minute == minute and is_weekend():
        print("hourtype", str(hourtype), "now_hour", str(now_hour), "now_minute", str(now_minute))
        random_time = random_minute()
        screenshot_prepare(hourtype)
        scheduler.enter(0, 0, incode_loop, (start_loop,random_time,))
        return
    else:
        if hourtype ==1:
            nextHour = back_hour
        else:
            nextHour = go_hour
        print("现在时间：", now_hour, ':', now_minute, "--下次执行事件", nextHour, ":", minute)
        scheduler.enter(60, 0, start_loop, (hourtype, minute, ))
        return

# 是否是周末
def is_weekend():
    """
    :return: if weekend return False else return True
    """
    now_time = datetime.datetime.now().strftime("%w")
    if now_time == "6" or now_time == "0":
        print("今天周末不打卡")
        return False
    else:
        return True
if __name__ == "__main__":
    # ======formal
    scheduler.enter(0, 0, incode_loop, (start_loop, random_minute(),))
    scheduler.run()