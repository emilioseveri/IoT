import schedule, time
import traceback
import json

#Import custom class
from Class.message import imessage
from Class.apple import apple_api
from Class.cgoogle import cgoogle_api
from Class.openweather import openweather_api
from Class.fitbit import fitbit_api

#Activate API
message = imessage()
apple_token = apple_api("emilioseveri@me.com", "Spider1492!")
google_token = cgoogle_api(debug=True)
openweather_token = openweather_api()
fitbit_token = fitbit_api()

def current_weather():
    latitude, longitude = apple_token.location()
    current_weather = openweather_token.current_weather(latitude, longitude)
    return current_weather
    
def forecast_weather():
    latitude, longitude = apple_token.location()
    forecast_weather = openweather_token.forecast_weather(latitude, longitude)
    return forecast_weather

def sleep():
    sleep = fitbit_token.sleep()
    return sleep

def create(file, data):
    #file is either 'current_weather' or 'forecast_weather' or 'sleep'
    file = google_token.create_sheet(file, data)
    return file

def update_current_weather(file):
    cw = current_weather()
    google_token.add_data(cw, file, 'weather')
    return None
def update_forecast_weather(file):
    fw = forecast_weather()
    google_token.add_data(fw, file, 'weather')
    return None
def update_sleep(file):
    s = sleep()
    google_token.add_data(s, file, 'sleep')
    return None

try:
    cw_weather = current_weather()
    fw_weather = forecast_weather()
    s = sleep()

    data = {
        "current_weather" : cw_weather,
        "forecast_weather" : fw_weather,
        "sleep" : s
    }

    with open("files.json", "w") as files: 
        json.dump(data, files)
    
    current_weather_file = create('current_weather', cw_weather)
    forecast_weather_file = create('forecast_weather', fw_weather)
    sleep_file = create('sleep', s)

    schedule.every(30).minutes.do(lambda: print("getting current_weather"))
    schedule.every(30).minutes.do(lambda: update_current_weather(current_weather_file))
    schedule.every().day.at("20:15").do(lambda: print("getting forecast weather"))
    schedule.every().day.at("20:15").do(lambda: update_forecast_weather(forecast_weather_file))
    schedule.every().day.at("12:00").do(lambda: print("getting sleep"))
    schedule.every().day.at("12:00").do(lambda: update_sleep(sleep_file))

    while True:
        schedule.run_pending()
        time.sleep(1)

except Exception:
    m = traceback.format_exc()
    print(m)
    if len(m) < 1600:
        message.send_imessage(m)
    else:
        message.send_imessage("Error, check console")
