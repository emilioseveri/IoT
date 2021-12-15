from model.model import analyse

#Run this code to get analyse the data and output a predictive model to use

an = analyse()
current_weather, forecast_weather, sleep = an.get_data()
df_new, df_forecast, df_sleep = an.formatting(current_weather, forecast_weather, sleep)
an.predictive(df_new, df_forecast, df_sleep)