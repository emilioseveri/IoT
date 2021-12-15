import requests
import json
from datetime import date
from pprint import pprint

#Implicit Grant flow
#Get this token from request in browser

class fitbit_api:
    def __init__(self, debug=False):
        with open('keys/keys.json') as f:
            files = json.load(f)
        
        #Implicit Grant flow
        self.fitbit_api = files['Fitbit_API']
        self.header = {'Authorization' : 'Bearer {}'.format(self.fitbit_api)}
        
        self.debug = debug
    
    def sleep(self):
        base_url = "https://api.fitbit.com/1.2/user/-/sleep/date/"

        today = date.today()
        d1 = today.strftime("%Y-%m-%d")

        complete_url = base_url + d1 + '.json'
        response = requests.get(complete_url, headers=self.header).json()
        
        if self.debug:
            print("sleep data \n")
            pprint(response)
        
        return response