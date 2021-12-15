#IoT

This is an IoT project for university. The outcome of the code below is tracking the weather and sleep. With this, it will create a predictive model on how good of a night sleep you will have. It will notify you by sending you a text.

The hardware to run this code are the following:
- Fitbit
- iPhone

To run this code, you will need to sign up to the following API:
- Fitbit
- Openweather
- Google Sheets (credential files)
- Twilio

Once you have everything set, make sure you upload you API keys to the file API key.
Run collect.py for as long as you want to collect your weather and sleep data.
Run analyse.py to create the predicitive model you want, either regression (outputs an actual score but is less precise) or classifier (is more accurate but doesn't give a score on your quality of sleep, simply if you will have a good night sleep or not).
After just run running.py as long as you want. This will send you gather the weather data and using the model will send you a text on what your sleep will be like tonight.
