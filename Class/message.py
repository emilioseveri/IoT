import json
from twilio.rest import Client

class imessage:
    def __init__(self, debug=False):
        with open('keys/keys.json') as f:
            files = json.load(f)

        self.debug = debug
        self.client = Client(files["Twilio_SID"], files['Twilio_API'])
    
    def send_imessage(self, message):
        my_phone = "447921453342"
        twilio_phone = "447782680429"
        
        if self.debug:
            print("message sent")
            print(message)

        self.client.messages.create(to=my_phone,
                                from_=twilio_phone,
                                body=message)
        
    def imessage(self, recipient, message):
        twilio_phone = "447782680429"
        
        if self.debug:
            print("message sent")
        
        self.client.messages.create(to=recipient,
                                from_=twilio_phone,
                                body=message)

"""
gifts_giver = [["Sam","07946248487"],
["Scott", "07580119393"],
["Emilio", "07921453342"],
["JL", "07742417034"]]

gifts_giver = [["Sam","07946248487"],
["Scott", "07580119393"],
["Emilio", "07921453342"],
["JL", "07742417034"]]
"""