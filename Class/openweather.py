import requests
import json
from pprint import pprint

class openweather_api:

    def __init__(self, debug=False):
        with open('keys/keys.json') as f:
            files = json.load(f)

        self.openweather_token = files["Openweather_API"]
        self.debug = debug
    
    def current_weather(self, latitude, longitude):
        base_url = 'https://api.openweathermap.org/data/2.5/onecall?'

        exclude = 'minutely,hourly,daily,alerts'
        units = 'metric'

        complete_url = base_url + 'lat=' + latitude + '&lon=' + longitude + '&exclude=' + exclude + '&units=' + units + '&appid=' + self.openweather_token

        weather_data = requests.get(complete_url).json()
        
        if self.debug:
            print("Current weather data")
            pprint(weather_data)

        return weather_data
    
    def forecast_weather(self, latitude, longitude):
        #Hourly forecast for 48 hours + national alerts
        base_url = 'https://api.openweathermap.org/data/2.5/onecall?'

        exclude = 'current,minutely,hourly'
        units = 'metric'

        complete_url = base_url + 'lat=' + latitude + '&lon=' + longitude + '&exclude=' + exclude + '&units=' + units + '&appid=' + self.openweather_token

        weather_data = requests.get(complete_url).json()

        if self.debug:
            print("Forecasted weather data")
            pprint(weather_data)

        return weather_data