#Standard classses
import os
import json
from datetime import datetime
import pickle
from Class.cgoogle import cgoogle_api

#Classes to analyse data with
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn import tree
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import r2_score
from six import StringIO  
from IPython.display import Image  
from sklearn.tree import export_graphviz
import pydotplus
import matplotlib.pyplot as plt

class analyse:
    def __init__(self) -> None:
        pass
        
    def get_data(self):
        #------------------------------------------------------------
        ###Import data
        if not os.path.exists("current_weather.json") and not os.path.exists("forecast_weather.json") and not os.path.exists("sleep.json"):
            google_token = cgoogle_api(debug=True)
            
            #Get google sheets ID
            if os.path.exists("files.json"):
                with open('files.json') as f:
                    files = json.load(f)

            #Read google sheets data
            current_weather = google_token.read_data(files['current_weather'])
            forecast_weather = google_token.read_data(files["forecast_weather"])
            sleep = google_token.read_data(files['sleep'])

            #Save for future use
            with open("current_weather.json", "w") as files: 
                json.dump(current_weather, files)
            with open("forecast_weather.json", "w") as files: 
                json.dump(forecast_weather, files)
            with open("sleep.json", "w") as files: 
                json.dump(sleep, files)
        else:
            with open('current_weather.json') as f:
                current_weather = json.load(f)
            with open('forecast_weather.json') as f:
                forecast_weather = json.load(f)
            with open('sleep.json') as f:
                sleep = json.load(f)
        return current_weather, forecast_weather, sleep
        
    def formatting(self, current_weather, forecast_weather, sleep, running=False):
        #------------------------------------------------------------
    ###Formatting
        current_weather['valueRanges'][0]['values'][0].append("ignore")

        #Transform data to pandas
        df_current = pd.DataFrame(current_weather['valueRanges'][0]['values'][1:], columns=current_weather['valueRanges'][0]['values'][0])
        df_forecast = pd.DataFrame(forecast_weather['valueRanges'][0]['values'][1:], columns=forecast_weather['valueRanges'][0]['values'][0])
        if not running:
            df_sleep = pd.DataFrame(sleep['valueRanges'][0]['values'][1:], columns=sleep['valueRanges'][0]['values'][0])

        #Convert all string values to float
        for i in df_current.columns:
            df_current[i] = df_current[i].astype(float)
        for i in df_forecast.columns:
            df_forecast[i] = df_forecast[i].astype(float)
        
        if not running:
            for i in df_sleep:
                if i != "startTime" and i!= "EndTime":
                    df_sleep[i] = df_sleep[i].astype(float)

        #Transform unix to datetime for easier read
        #+used to understand which row does a day start to a day end
        date = []
        days = {}
        n = 0
        starting_position = 0
        final_position = 0
        previous_point = datetime.fromtimestamp(df_current.dt[0])
        for i in df_current.dt:
            time_stamp = datetime.fromtimestamp(i)
            if str(previous_point)[:10] != str(time_stamp)[:10]:
                days["day_"+str(n)] = [starting_position, final_position]
                n+=1
                starting_position = final_position
                previous_point = time_stamp
            final_position+=1
            date.append(time_stamp)
        df_current['datetime'] = date

        date = []
        for i in df_forecast.dt:
            date.append(datetime.fromtimestamp(i))
        df_forecast['datetime'] = date

        if not running:
            #Turn users sleep score to a binary output for classifying
            sleep_score = []
            for i in df_sleep.efficiency:
                if i > 80:
                    sleep_score.append(1)
                else:
                    sleep_score.append(0)

            df_sleep['sleep_score'] = sleep_score

        #Transfrom the current weather data to the same number of entries as forecast and sleep
        #This is done to be able to create a model and compare

        data = {
            "sunrise" : [],
            "sunset" : [],
            "temp": [],
            "temp min": [],
            "temp max": [],
            "feels_like": [],
            "pressure": [],
            "humidity": [],
            "dew_point": [],
            "clouds": [],
            "wind_speed": [],
            "wind_deg": [],
            "datetime": []
        }

        for i in list(days.keys())[1:]:
            starting_position = days[i][0]
            final_position = days[i][1]
            for j in data.keys():
                if j != "temp min" and j != "temp max" and j != "datetime":
                    data[j].append(np.average(df_current[j][starting_position:final_position]))
                elif j == "temp min":
                    data[j].append(np.min(df_current["temp"][starting_position:final_position]))
                elif j == "temp max":
                    data[j].append(np.max(df_current["temp"][starting_position:final_position]))
                elif j == "datetime":
                    data["datetime"].append(df_current.datetime[starting_position+4])

        #df_new is therefore the current weather data condensed into the same number of rows as forecast and sleep
        df_new = pd.DataFrame(data)
        df_new.clouds = df_new.clouds/100

        #Using sunrise and sunset, convert this into how long a day was which will be more useful feature for the predicitive model
        #Reason being research has shown the legnth of a day has an effect of quality of sleep
        i = 0
        time_elapsed_current = []
        time_elapsed_forecast = []
        while i < len(df_new.sunrise):
            d1 = df_new.sunrise[i]
            d2 = df_new.sunset[i]
            converted_d1 = datetime.fromtimestamp(round(d1))
            converted_d2 = datetime.fromtimestamp(round(d2))

            time_elapsed_current.append((converted_d2 - converted_d1).total_seconds())

            d1 = df_forecast.sunrise[i]
            d2 = df_forecast.sunset[i]
            converted_d1 = datetime.fromtimestamp(round(d1))
            converted_d2 = datetime.fromtimestamp(round(d2))

            time_elapsed_forecast.append((converted_d2 - converted_d1).total_seconds())

            i += 1

        df_new['time_elapsed'] = time_elapsed_current
        df_forecast['time_elapsed'] = time_elapsed_forecast

        if not running:
            return df_new, df_forecast, df_sleep
        else:
            return df_new, df_forecast
    
    def predictive(self, df_new, df_forecast, df_sleep):
        #------------------------------------------------------------
        ###Predictive model

        #Able to choose if you want to use a regressor or classifier model
        print("Regressor or Classifier")
        choice = input()

        if choice == "Regressor":
            #Assign sleep score to df_new which will be used to predict sleep
            df_new = df_new.assign(efficiency=list(df_sleep.efficiency))

            #Split Data
            train_current, other_current = train_test_split(df_new, test_size = 0.3, random_state = 0)
            test_current, valid_current = train_test_split(other_current, test_size=0.5, random_state=0)

            #Initialise
            format_column_current = list(df_new.loc[:, ~df_new.columns.isin(['datetime', 'efficiency'])])
            X_train_current = train_current[format_column_current]
            y_train_current = train_current['efficiency'].values.reshape(-1,1)
            X_test_current = test_current[format_column_current]
            y_test_current = test_current['efficiency'].values.reshape(-1,1)
            X_valid_current = valid_current[format_column_current]
            y_valid_current = valid_current['efficiency'].values.reshape(-1,1)

            #Get R2 score of current and forecast
            #This is done to see how accurate the forecast data was when knowing what the actual weather was
            score_ = {}
            for i in format_column_current:
                if i == "temp":
                    score = r2_score(df_forecast['temp day'][1:], df_new['temp'][:-1])
                    print("temp: {}".format(score))
                    score_["temp"] = score
                elif i == "feels_like":
                    score = r2_score(df_forecast['feels_like day'][1:], df_new['feels_like'][:-1])
                    print("feels_like: {}".format(score))
                    score_["feels_like"] = score
                elif i not in ["clouds", "wind_speed", "wind_deg"]:
                    score = r2_score(df_forecast[i][1:], df_new[i][:-1])
                    print("{}: {}".format(i, score))
                    score_[i] = score
                elif i  in ["clouds", "wind_speed", "wind_deg"]:
                    score = r2_score(df_forecast[i][7:], df_new[i][6:-1]) #reason for the number 7 and 6 is the forecast data has no values for the initial 6 days.
                    print("{}: {}".format(i, score))
                    score_[i] = score
            
            #Train model
            regressor = RandomForestRegressor(random_state=0, min_samples_split=4)
            regressor.fit(X_train_current, y_train_current)
            train_score = regressor.score(X_train_current, y_train_current)
            test_score = regressor.score(X_test_current, y_test_current)
            valid_score = regressor.score(X_valid_current, y_valid_current)

            #Print score
            print("train score: {}".format(train_score)) #0.77
            print("test score: {}".format(test_score)) #0.13
            print("valid score: {}".format(valid_score)) #0.18

            #Save an example of one decision tree in the forest
            dot_data = StringIO()
            export_graphviz(regressor.estimators_[0], out_file=dot_data,  
                            filled=True, rounded=True,
                            special_characters=True)
            graph = pydotplus.graph_from_dot_data(dot_data.getvalue())  
            graph.write_png('model/regressor.png')

            #Print out which important features
            data = {
                'features': X_train_current.columns,
                'importance': regressor.feature_importances_
            }
            display = pd.DataFrame(data)
            display.sort_values('importance', inplace = True)
            print(display)

            #Get an example of it predicting your sleep score the next day
            #+ see if it actually got it right
            day = 11
            format_column_forecast = ['sunrise', 'sunset', 'temp day', 'temp min', 'temp max', 'feels_like day', 'pressure', 'humidity', 'dew_point', 'clouds', 'wind_speed', 'wind_deg', 'time_elapsed']
            X_forecast = df_forecast[format_column_forecast]
            predict_me = X_forecast.loc[day]
            predict_me = predict_me.values.reshape(1,13)

            y_pred = regressor.predict(predict_me)
            print("Prediction of a good night sleep: {}".format(y_pred))
            print("Actual good night sleep: {}".format(df_new.efficiency[day+1]))

            #Forecasting score
            print("Forecast accuracy score: {}".format(regressor.score(X_forecast[7:], df_new.efficiency[6:-1])))

            print("Save trained model?")
            choice = input()
            if choice == "Yes":
                with open('model/model.pkl','wb') as f:
                    pickle.dump(regressor,f)


        elif choice == "Classifier":
            #Assign sleep score to df_new which will be used to predict sleep
            df_new = df_new.assign(sleep_score=list(df_sleep.sleep_score))

            #Split Data
            train_current, other_current = train_test_split(df_new, test_size = 0.3, random_state = 0)
            test_current, valid_current = train_test_split(other_current, test_size=0.5, random_state=0)

            #Initialise
            format_column_current = list(df_new.loc[:, ~df_new.columns.isin(['datetime', 'sleep_score', 'efficiency', 'feels_like', 'sunset','sunrise', 'humidity'])])
            X_train_current = train_current[format_column_current]
            y_train_current = train_current['sleep_score'].values.reshape(-1,1)
            X_test_current = test_current[format_column_current]
            y_test_current = test_current['sleep_score'].values.reshape(-1,1)
            X_valid_current = valid_current[format_column_current]
            y_valid_current = valid_current['sleep_score'].values.reshape(-1,1)

            #Get R2 score of current and forecast
            #This is done to see how accurate the forecast data was when knowing what the actual weather was
            score_ = {}
            for i in format_column_current:
                if i == "temp":
                    score = r2_score(df_forecast['temp day'][1:], df_new['temp'][:-1])
                    print("temp: {}".format(score))
                    score_["temp"] = score
                elif i == "feels_like":
                    score = r2_score(df_forecast['feels_like day'][1:], df_new['feels_like'][:-1])
                    print("feels_like: {}".format(score))
                    score_["feels_like"] = score
                elif i not in ["clouds", "wind_speed", "wind_deg"]:
                    score = r2_score(df_forecast[i][1:], df_new[i][:-1])
                    print("{}: {}".format(i, score))
                    score_[i] = score
                elif i  in ["clouds", "wind_speed", "wind_deg"]:
                    score = r2_score(df_forecast[i][7:], df_new[i][6:-1]) #reason for the number 7 and 6 is the forecast data has no values for the initial 6 days.
                    print("{}: {}".format(i, score))
                    score_[i] = score

            #Train model

            #max_depth no change
            #min_samples_leaf no changee
            #min_samples_split no change

            classifer = RandomForestClassifier(random_state=0)
            classifer.fit(X_train_current, y_train_current)
            train_score = classifer.score(X_train_current, y_train_current)
            test_score = classifer.score(X_test_current, y_test_current)
            valid_score = classifer.score(X_valid_current, y_valid_current)

            #Print score
            print("train score current: {}".format(train_score)) #1.0
            print("test_score current: {}".format(test_score)) #0.5
            print("valid_score current: {}".format(valid_score)) #0.66

            #Save an example of a decision tree
            dot_data = StringIO()
            export_graphviz(classifer.estimators_[0], out_file=dot_data,  
                            filled=True, rounded=True,
                            special_characters=True)
            graph = pydotplus.graph_from_dot_data(dot_data.getvalue())  
            graph.write_png('model/classifier.png')

            #Print out important features
            data = {
                'features': X_train_current.columns,
                'importance': classifer.feature_importances_
            }
            display = pd.DataFrame(data)
            display.sort_values('importance', inplace = True)
            print(display)

            #Get an example of it predicting your sleep score the next day
            #+ see if it actually got it right
            day = 11
            format_column_forecast = ['temp day', 'temp min', 'temp max', 'pressure', 'dew_point', 'clouds', 'wind_speed', 'wind_deg', 'time_elapsed']
            X_forecast = df_forecast[format_column_forecast][7:]
            predict_me = X_forecast.loc[day]
            predict_me = predict_me.values.reshape(1,9)

            y_pred = classifer.predict(predict_me)
            print("Prediction of a good night sleep: {}".format(y_pred))
            print("Actual good night sleep: {}".format(df_new.sleep_score[day+1]))

            #Forecasting score
            print("Forecast accuracy score: {}".format(classifer.score(X_forecast, df_new.sleep_score[6:-1])))

            print("Save trained model?")
            choice = input()
            if choice == "Yes":
                with open('model/model.pkl','wb') as f:
                    pickle.dump(classifer,f)

"""
OLD CODE
THIS FOLLOWING IS THE CODE USED FOR DECISION TREES
THEY PERFOMED WORSE COMPARE TO RANDOM DECISION TREES

THIS PART SIMPLY SERVES AS A COMPARISON ONCE IN A WHILE TO SEE IF RANDOMFOREST SCORE IS SIGNIFICANTLY BETTER THAN DECISION TREE SCORE

#max_depth =2
#min_samples_leaf =2
#min_samples_split =4

regressor = tree.DecisionTreeRegressor(random_state=0)
regressor.fit(X_train_current, y_train_current)
train_score=regressor.score(X_train_current, y_train_current)
test_score=regressor.score(X_test_current, y_test_current)
#valid_score=regressor.score(X_valid_current, y_valid_current)

print("train score current: {}".format(train_score)) #1.0
print("test_score current: {}".format(test_score)) #-13.44
#print("valid_score current: {}".format(valid_score)) #-5.6

dot_data = StringIO()
export_graphviz(regressor, out_file=dot_data,  
                filled=True, rounded=True,
                special_characters=True)
graph = pydotplus.graph_from_dot_data(dot_data.getvalue())  
graph.write_png('regressor.png')

#max_depth >=3
#min_samples_leaf >=5
#min_samples_split >=10
#Forecast score
# train 0.639
# test -1.22
# valid -5.6

regressor = tree.DecisionTreeRegressor(random_state=0, max_depth=2)
regressor.fit(X_train_current, y_train_current)
train_score = regressor.score(X_train_current, y_train_current)
test_score = regressor.score(X_test_current, y_test_current)
#valid_score = regressor.score(X_valid_current, y_valid_current)

print(train_score)
print(test_score)
#print(valid_score)

regressor = tree.DecisionTreeRegressor(random_state=0, min_samples_leaf=2)
regressor.fit(X_train_current, y_train_current)
train_score = regressor.score(X_train_current, y_train_current)
test_score = regressor.score(X_test_current, y_test_current)
#valid_score = regressor.score(X_valid_current, y_valid_current)

print(train_score)
print(test_score)
#print(valid_score)

regressor = tree.DecisionTreeRegressor(random_state=0, min_samples_split=4)
regressor.fit(X_train_current, y_train_current)
train_score = regressor.score(X_train_current, y_train_current)
test_score = regressor.score(X_test_current, y_test_current)
#valid_score = regressor.score(X_valid_current, y_valid_current)

print(train_score)
print(test_score)
#print(valid_score)

regressor = tree.DecisionTreeRegressor(random_state=0, max_depth = 2, min_samples_leaf=2, min_samples_split=4)
regressor.fit(X_train_current, y_train_current)
train_score = regressor.score(X_train_current, y_train_current)
test_score = regressor.score(X_test_current, y_test_current)
#valid_score = regressor.score(X_valid_current, y_valid_current)

print(train_score) #0.84
print(test_score) #-0.01
#print(valid_score) #0.35

#Classifier

max_depth no change
#min_samples_leaf no changee
#min_samples_split no change

classifer = tree.DecisionTreeClassifier(random_state=0)
classifer.fit(X_train_current, y_train_current)
train_score=classifer.score(X_train_current, y_train_current)
test_score=classifer.score(X_test_current, y_test_current)
valid_score=classifer.score(X_valid_current, y_valid_current)

print("train score current: {}".format(train_score)) #1.0
print("test_score current: {}".format(test_score)) #0.5
print("valid_score current: {}".format(valid_score)) #0.33

dot_data = StringIO()
export_graphviz(classifer, out_file=dot_data,  
                filled=True, rounded=True,
                special_characters=True)
graph = pydotplus.graph_from_dot_data(dot_data.getvalue())  
graph.write_png('classifier.png')
"""