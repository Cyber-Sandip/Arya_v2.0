import ctypes
import psutil
import subprocess
import datetime
import time 
from datetime import datetime
from colorama import Style,Fore,init
import os
import sys
import subprocess
import pyautogui
from pathlib import Path


###########################################################################################################################
######## for path related issues ############
root_dir =Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

###########################################################################################################################

from voice.text_to_speech import say


###########################################################################################################################
############ find battery related all data ##########
def get_battery():
    return psutil.sensors_battery()

def power():
    bat = get_battery()
    if bat is None:
        say("battery information is not available")
        return
    say(f"your device running on {bat.percent} parcent battery ")

def full_charged():
    bat = get_battery()
    if bat is not None and bat.power_plugged == True and bat.percent >= 100:
        say("my battery is fully charged...please plug in out...")


def charge():
    bat = get_battery()
    if bat is None:
        return
    per = bat.percent
    cha = bat.power_plugged
    if per >= 100 and cha == True:
        say("my battery is full")
    elif per <=2 and cha == False:
        say("my battery percentage low. please plug in....")
    elif per <=1 and cha == False:
        say("my battery percentage too low .if you now charge i will be shutdown within few minute. please plug in....")

def is_charge():
    bat = get_battery()
    if bat is None:
        say("battery information is not available")
        return
    if bat.power_plugged == False:
        say(f"your device is running {bat.percent} parcent battery")
    else:
        say("your device is running on power cable...")

###################################################################################################################################
##################find date and time related all date ################################
def get_time():
    g_time=datetime.now().strftime("%H:%M:%S")
    return g_time

def continues_timer():
    while True:
        print(f"\r Time is : {get_time()}",end="",flush=True)
        time.sleep(1)

def get_date():
    return datetime.now().strftime("%d/%m/%Y")

def month():
    m=datetime.now().strftime("%m")
    if m=="01":
        return "january"
    if m=="02" :
        return "February"
    if m=="03" :
        return "March"
    if m=="04" :
        return "April"
    if m=="05" :
        return "May"
    if m=="06":
        return "june"
    if m=="07":
        return "july"
    if m=="08":
        return "August"
    if m=="09" :
        return "September"
    if m=="10" :
        return "October"
    if m=="11" :
        return "November"
    if m=="12":
        return "December"

def real_date():
    date=datetime.now().strftime("%d")
    say(f"today is : {date}  {month()}")

###################################################################################################################################
########################## it can take screenshots ########################################


def take_screenshot():
    # Set your desired folder path
    from config import SCREENSHOT_DIR
    folder_path = str(SCREENSHOT_DIR)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Make sure the folder exists (create it if not)
    os.makedirs(folder_path, exist_ok=True)

    # Create timestamp-based filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{timestamp}.png"

    # Full file path
    file_path = os.path.join(folder_path, filename)

    # Take and save screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save(file_path)
    return {"success": True, "message": f"Screenshot saved to {file_path}."}

###################################################################################################################################
################## media control #######################

def volume_up():
    pyautogui.press("volumeup")
    say("volume increase")

def volume_down():
    pyautogui.press("volumedown")
    say("volume decrease")

def mute():
    pyautogui.press("volumemute")
    say("volume muted")

######################################################################################################################################
#################### control wifi and blutooth ########################
def turn_off_bluetooth():
    say("turning off blutooth")
    subprocess.run('powershell (Get-PnpDevice -FriendlyName "*Bluetooth*" | Disable-PnpDevice -Confirm:$false)', shell=True)

def turn_on_blutooth():
    say("turning on blutooth")
    subprocess.run('powershell (Get-PnpDevice -FriendlyName "*Bluetooth*" | Enable-PnpDevice -Confirm:$false)', shell=True)

def turn_on_wifi():
    say("turning on wifi")
    subprocess.run('nets h interface set interface "Wi-Fi" enable', shell=True)


##################################################################################################################################
############ system control #########################

def shutdown():
    say("shurting down your computer")
    os.system("shutdown /s /f /t 0")
    return {"success": True, "message": "Shutting down."}

def restart():
    say("restarting your computer")
    subprocess.run(["shutdown", "/r", "/t", "0"],check= True)
    return {"success": True, "message": "Restarting."}

def lock_pc():
    ctypes.windll.user32.LockWorkStation()
    return {"success": True, "message": "Computer locked."}


def sleep():
    say("Putting the computer to sleep...")
    ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)


###################################################################################################################################
