import requests
from pathlib import Path
import sys

root_dir =Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from voice.text_to_speech import say
#########################################################################################################################
############# weather report ##############

def get_weather(city):
    url = f"https://wttr.in/{city}?format=4"  # simple one-line report
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return "Sorry, couldn't fetch weather data."


def weather():
    weather_report = get_weather("Bishnupur,Bankura")
    weather=weather_report.split(" ")
    # say(weather_report)
    # print(weather[0])
    weather[0]=weather[0].replace("Bankura","")
    say(f"today's weather in {weather[0]} is ")
    say(weather[1])
    weather[4]=weather[4].replace("🌡️+","")
    say(f"temperature is {weather[4]}")
    weather[5] = weather[5].replace("🌬️↖", "")
    weather[5] = weather[5].replace("km/h", "")
    weather[5]=weather[5]+" kilometers per hour"
    say(f" wind speed is{weather[5]}")
   
################################################################################################################################






def internet():
    pass
def ip_address():
    pass
def unit_convert():
    pass

def tel_a_joke():
    pass
