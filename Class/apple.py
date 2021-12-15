import sys
from pprint import pprint
from pyicloud import PyiCloudService
from shutil import copyfileobj

class apple_api:
    def __init__(self, username, password, debug=False):
        self.apple_token = PyiCloudService('emilioseveri@me.com', 'Spider1492!')

        #Requires inputting initially the two step authentication code
        if self.apple_token.requires_2fa:
            print("Two-factor authentication required.")
            code = input("Enter the code you received of one of your approved devices: ")
            result = self.apple_token.validate_2fa_code(code)
            print("Code validation result: %s" % result)

            if not result:
                print("Failed to verify security code")
                sys.exit(1)

            if not self.apple_token.is_trusted_session:
                print("Session is not trusted. Requesting trust...")
                result = self.apple_token.trust_session()
                print("Session trust result %s" % result)

                if not result:
                    print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
        elif self.apple_token.requires_2sa:
            import click
            print("Two-step authentication required. Your trusted devices are:")

            devices = self.apple_token.trusted_devices
            for i, device in enumerate(devices):
                print("  %s: %s" % (i, device.get('deviceName',
                    "SMS to %s" % device.get('phoneNumber'))))

            device = click.prompt('Which device would you like to use?', default=0)
            device = devices[device]
            if not self.apple_token.send_verification_code(device):
                print("Failed to send verification code")
                sys.exit(1)

            code = click.prompt('Please enter validation code')
            if not self.apple_token.validate_verification_code(device, code):
                print("Failed to verify verification code")
                sys.exit(1)

        self.debug = debug
    
    def location(self):
        loc = self.apple_token.devices[3].location()
        latitude = str(loc['latitude'])
        longitude = str(loc['longitude'])

        if self.debug:
            print(self.apple_token.devices[3])

            print("Location data")
            pprint(loc)
        
        return latitude, longitude
