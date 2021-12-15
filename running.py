import os
import schedule, time
import traceback
import json
import pickle

#Import custom class
from Class.message import imessage
from Class.apple import apple_api
from Class.cgoogle import cgoogle_api
from Class.openweather import openweather_api
from model.model import analyse

#Activate API
message = imessage()
apple_token = apple_api("emilioseveri@me.com", "Spider1492!")
google_token = cgoogle_api(debug=True)
openweather_token = openweather_api()
an = analyse()

ID_verified = False
model_verified = False

if os.path.exists("files.json"):
    with open('files.json') as f:
        files = json.load(f)

    current_weather_ID = files['current_weather']
    forecast_weather_ID = files["forecast_weather"]

    ID_verified = True
else:
    print("No file ID")

if os.path.exists("model/model.pkl"):
    with open('model/model.pkl', 'rb') as f:
        model = pickle.load(f)
    model_verified = True
else:
    print("No model trained")

def current_weather():
    latitude, longitude = apple_token.location()
    current_weather = openweather_token.current_weather(latitude, longitude)
    return current_weather
    
def forecast_weather():
    latitude, longitude = apple_token.location()
    forecast_weather = openweather_token.forecast_weather(latitude, longitude)
    return forecast_weather

def update_current_weather(file):
    cw = current_weather()
    google_token.add_data(cw, file, 'weather')
    return None
def update_forecast_weather(file):
    fw = forecast_weather()
    google_token.add_data(fw, file, 'weather')
    return None

def prediction(current_ID, forecast_ID):
    current = google_token.read_data(current_ID)
    forecast = google_token.read_data(forecast_ID)
    df_new, df_forecast = an.formatting(current, forecast, {}, running=True)

    format_column_current = list(df_new.loc[:, ~df_new.columns.isin(['datetime', 'sleep_score', 'efficiency', 'feels_like', 'sunset','sunrise', 'humidity'])])
    format_column_forecast = ['temp day', 'temp min', 'temp max', 'pressure', 'dew_point', 'clouds', 'wind_speed', 'wind_deg', 'time_elapsed']

    X_forecast = df_forecast[format_column_forecast]
    X_forecast = X_forecast.iloc[-1]
    X_forecast = X_forecast.values.reshape(1,9)

    X_current = df_new[format_column_current]
    X_current = X_current.iloc[-1]
    X_current = X_current.values.reshape(1,9)
    
    y_pred_current= model.predict(X_current)
    y_pred_forecast = model.predict(X_forecast)

    if y_pred_current == 1:
        m = "Today you will have a great night sleep"
        message.send_imessage(m)
    else:
        m = "Sorry you won't have great night sleep, think of maybe taking more time to relax tonight before going to bed"
        message.send_imessage(m)
    if y_pred_forecast == 1:
        m = "Tomorrow you will have a great night sleep"
        message.send_imessage(m)
    else:
        m = "Tomorrow you won't have a great night sleep, think of maybe taking more time to relax tonight before going to bed"
        message.send_imessage(m)
    return None

if ID_verified and model_verified:
    try:
        schedule.every().day.at("09:00").do(lambda: print("getting curent weather"))
        schedule.every().day.at("09:00").do(lambda: update_current_weather(current_weather_ID))
        schedule.every().day.at("09:00").do(lambda: print("getting forecast weather"))
        schedule.every().day.at("09:00").do(lambda: update_forecast_weather(forecast_weather_ID))
        schedule.every().day.at("09:00").do(lambda: print("sending a text"))
        schedule.every().day.at("09:00").do(lambda: prediction(current_weather_ID, forecast_weather_ID))


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