import os
import json
from pprint import pprint
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class cgoogle_api():
    def __init__(self, debug=False):
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        
        self.creds = None
        self.debug = debug

        if os.path.exists("keys/token.json"):
            if self.debug:
                print("loading credentials from files")
            self.creds = Credentials.from_authorized_user_file('keys/token.json', SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                if self.debug:
                    print("refreshing tokens")
                self.creds.refresh(Request())
            else:
                if self.debug:
                    print("fetching new tokens")
                flow = InstalledAppFlow.from_client_secrets_file(
                    "keys/credentials.json", scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                flow.run_local_server(port=8080, access_type='offline', prompt = 'consent')
                
                self.creds = flow.credentials
                print(self.creds._refresh_token)

                with open("keys/token.json", "w") as token:
                    if self.debug:
                        print("saving credentials")
                    token.write(self.creds.to_json())
        
        if self.debug:
            print("accessing refresh token: {}" .format(self.creds._refresh_token))

        self.service = build('sheets', 'v4', credentials=self.creds)
    
    def create_sheet(self, title, data):
        #Create spreadsheet
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        sheets = self.service.spreadsheets().create(body=spreadsheet).execute()
        
        id = sheets['spreadsheetId']

        #creating the headers for the columns
        value = []
        
        if title == "current_weather":
            value.append(['latitude'])
            value.append(['longitude'])
            for i in data[list(data.keys())[-1]]:
                value.append([i])
        elif title == 'forecast_weather':
            value.append(['latitude'])
            value.append(['longitude'])
            for i in data[list(data.keys())[-1]][0]:
                if i == 'temp' or i == 'feels_like':
                    for j in data[list(data.keys())[-1]][0][i]:
                        value.append([i+' '+j])
                else:
                    value.append([i])
        elif title == 'sleep':
            value.append(["efficiency"])
            value.append(['totalTimeInBed'])
            value.append(['totalMinutesAsleep'])
            value.append(['totalMinutesAwake'])
            value.append(['minutesToFallAsleep'])
            value.append(['startTime'])
            value.append(['EndTime'])
            value.append(['deep_count'])
            value.append(['deep_time'])
            value.append(['deep_thirtyDayAvgMinutes'])
            value.append(['light_count'])
            value.append(['light_time'])
            value.append(['light_thirtyDayAvgMinutes'])
            value.append(['rem_count'])
            value.append(['rem_time'])
            value.append(['rem_thirtyDayAvgMinutes'])
            value.append(['wake_count'])
            value.append(['wake_time'])
            value.append(['wake_thirtyDayAvgMinutes'])
        
        if self.debug:
            pprint(value)

        resource = {
        "majorDimension": "COLUMNS",
        "values": value
        }
        #Append headder names to columns
        spreadsheetId = id
        range = "Sheet1!A:A"
        self.service.spreadsheets().values().append(
        spreadsheetId=spreadsheetId,
        range=range,
        body=resource,
        valueInputOption="USER_ENTERED"
        ).execute()

        if self.debug:
            print("Created Sheet")
            print("ID: {}".format(id))
        return id
    
    def add_data(self, data, spreadsheet_id, file_type):
        #data is a json file taking either openweather or fitbit output
        value = []

        if file_type == "weather":
            value.append([data['lat']])
            value.append([data['lon']])

            if list(data.keys())[-1] == 'current':
                for i in data[list(data.keys())[-1]]:
                    if i != 'weather' and i != 'rain':
                        value.append([data[list(data.keys())[-1]][i]])
            elif list(data.keys())[-1] == 'daily':
                for i in data[list(data.keys())[-1]][0]:
                    if i == 'temp' or i == 'feels_like':
                        for j in data[list(data.keys())[-1]][0][i]:
                            value.append([data[list(data.keys())[-1]][0][i][j]])
                    elif i != 'weather' and i != 'rain':
                        value.append([data[list(data.keys())[-1]][0][i]])
                    
        if file_type == 'sleep':
            value.append([data]["sleep"][0]['efficiency'])
            value.append([data['summary']['totalTimeInBed']])
            value.append([data['summary']['totalMinutesAsleep']])
            value.append([data['sleep'][0]['minutesAwake']])
            value.append([data['sleep'][0]['minutesToFallAsleep']])
            value.append([data['sleep'][0]['startTime']])
            value.append([data['sleep'][0]['endTime']])
            value.append([data['sleep'][0]['levels']['summary']['deep']['count']])
            value.append([data['sleep'][0]['levels']['summary']['deep']['minutes']])
            value.append([data['sleep'][0]['levels']['summary']['deep']['thirtyDayAvgMinutes']])
            value.append([data['sleep'][0]['levels']['summary']['light']['count']])
            value.append([data['sleep'][0]['levels']['summary']['light']['minutes']])
            value.append([data['sleep'][0]['levels']['summary']['light']['thirtyDayAvgMinutes']])
            value.append([data['sleep'][0]['levels']['summary']['rem']['count']])
            value.append([data['sleep'][0]['levels']['summary']['rem']['minutes']])
            value.append([data['sleep'][0]['levels']['summary']['rem']['thirtyDayAvgMinutes']])
            value.append([data['sleep'][0]['levels']['summary']['wake']['count']])
            value.append([data['sleep'][0]['levels']['summary']['wake']['minutes']])
            value.append([data['sleep'][0]['levels']['summary']['wake']['thirtyDayAvgMinutes']])
        
        if self.debug:
            pprint(value)

        resource = {
        "majorDimension": "COLUMNS",
        "values": value
        }

        spreadsheetId = spreadsheet_id
        range = "Sheet1!A:A"
        self.service.spreadsheets().values().append(
        spreadsheetId=spreadsheetId,
        range=range,
        body=resource,
        valueInputOption="USER_ENTERED"
        ).execute()

        if self.debug:
            print("Added Data")
    
    def read_data(self, file):
        range_names = [
            "Sheet1!A1:AA1000"
        ]

        result = self.service.spreadsheets().values().batchGet(
            spreadsheetId=file, ranges=range_names).execute()
        
        ranges = result.get('valueRanges', [])
        
        if self.debug:
            pprint(result)
        
        return result