from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import pandas as pd
from prophet import Prophet
import holidays
from dateutil import easter
from prophet.diagnostics import cross_validation, performance_metrics
from prophet.plot import plot_cross_validation_metric
from googleapiclient.errors import HttpError
import matplotlib.pyplot as plt

# Function for authentication
def google_auth(scopes, existing_token_path, service_name, service_version):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(existing_token_path):
        creds = Credentials.from_authorized_user_file(existing_token_path, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'C:/Users/allan/Desktop/Personlige projekter/GA_Flask_App_Credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(existing_token_path, 'w') as token:
            token.write(creds.to_json())

    service = build(service_name, service_version, credentials=creds)

    return service


service_ga4 = google_auth(scopes = ['https://www.googleapis.com/auth/analytics.readonly'], 
                          existing_token_path = 'C:/Users/allan/Desktop/Personlige projekter/token_ga4.json', 
                          service_name = 'analyticsdata', 
                          service_version = 'v1beta')

service_ga4_admin = google_auth(scopes=['https://www.googleapis.com/auth/analytics.readonly'],
                                existing_token_path='C:/Users/allan/Desktop/Personlige projekter/token_ga4_admin.json',
                                service_name='analyticsadmin',
                                service_version='v1alpha')

#______________________________________________________________________________

# Function to list GA4 accounts and properties in a dataframe
def list_ga4_accounts_and_properties_dataframe(service_object):
    try:
        # List all GA4 accounts and their properties
        account_summaries = service_object.accountSummaries().list().execute()

        # Initialize a list to store data
        data = []

        # Extract all account names
        for account_summary in account_summaries.get('accountSummaries', []):
            account_id = account_summary['name']
            account_display_name = account_summary['displayName']
            
            # Iterate through the properties under each account
            for property_summary in account_summary.get('propertySummaries', []):
                property_id = property_summary['property']
                property_display_name = property_summary['displayName']

                # Append account and property info to the data list
                data.append({
                    'Account ID': account_id,
                    'Account Name': account_display_name,
                    'Property ID': property_id,
                    'Property Name': property_display_name
                })

        # Convert the list of dictionaries into a pandas dataframe
        df = pd.DataFrame(data)

        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()  # Return an empty dataframe in case of error

ga4_accounts_and_properties_df = list_ga4_accounts_and_properties_dataframe(service_ga4_admin)

#______________________________________________________________________________

# Function to pull overall daily sessions 
def get_ga4_daily_sessions(service, property_id, start_date, end_date):
    max_retries = 5  # Set the maximum number of retry attempts

    # Attempt the API call up to a maximum number of retries
    for attempt in range(1, max_retries + 1):
        try:
            # Define the request body with the required parameters
            request_body = {
                "requests": [
                    {
                        "dateRanges": [
                            {
                                "startDate": start_date,  # Start date for the data range
                                "endDate": end_date  # End date for the data range
                            }
                        ],
                        "dimensions": [{"name": "date"}],  # Request data by date
                        "metrics": [{"name": "sessions"}],  # Request session metrics
                    }
                ]
            }

            # Execute the API call to fetch the report
            response = service.properties().batchRunReports(
                property=property_id, 
                body=request_body
            ).execute()

            # Initialize an empty list to store the session data
            sessions_data = []
            # Parse the response and populate the sessions_data list
            for report in response.get('reports', []):
                for row in report.get('rows', []):
                    date = row['dimensionValues'][0]['value']  # Extract date
                    sessions = row['metricValues'][0]['value']  # Extract session count
                    # Append the data as a dictionary to the sessions_data list
                    sessions_data.append({'Date': date, 'Sessions': sessions})

            # Convert the list of dictionaries to a dataframe
            sessions_data = pd.DataFrame(sessions_data)
            # Convert the 'Date' column to datetime format for proper sorting and manipulation
            sessions_data['Date'] = pd.to_datetime(sessions_data['Date'], format='%Y%m%d')
            # Sort the dataframe by the 'Date' column
            sessions_data = sessions_data.sort_values(by='Date')
            # Reset the index of the dataframe for cleanliness
            sessions_data = sessions_data.reset_index(drop=True)

            # Return the prepared dataframe
            return sessions_data
        except HttpError as e:
            # If an HTTP error occurs, print the error and attempt number
            print(f"HTTP error occurred on attempt {attempt}: {e}")
            if attempt == max_retries:
                # If the maximum number of retries has been reached, give up and return an empty dataframe
                print("Max retries reached. Giving up.")
                return pd.DataFrame()
        except Exception as e:
            # Catch any other exceptions and print the error
            print(f"An unspecified error occurred: {e}")
            return pd.DataFrame()  # Return an empty dataframe in case of unexpected errors

#______________________________________________________________________________

###############################################################################
######################### Including Danish Holidays ###########################
###############################################################################

# Function to calculate static holidays
def create_holiday_df(holiday_name, start_month, start_day, end_month, end_day, years = range(2020, 2031), lower_window=0, upper_window=0):
    holiday_list = []
    for year in years:
        start_date = pd.Timestamp(year=year, month=start_month, day=start_day) + pd.Timedelta(days=lower_window)
        end_date = pd.Timestamp(year=year, month=end_month, day=end_day) + pd.Timedelta(days=upper_window)
        date_range = pd.date_range(start=start_date, end=end_date)
        for date in date_range:
            holiday_list.append({'holiday': holiday_name, 'ds': date, 'lower_window': lower_window, 'upper_window': upper_window})
    return pd.DataFrame(holiday_list)

# New years
nytaar = create_holiday_df(holiday_name = 'Nytaar', 
                               start_month = 1, 
                               start_day = 1, 
                               end_month = 1, 
                               end_day = 1, 
                               lower_window = -1, 
                               upper_window = 1)
# Christmas
juleaften = create_holiday_df(holiday_name = 'Juleaften', 
                               start_month = 12, 
                               start_day = 24, 
                               end_month = 12, 
                               end_day = 25,  
                               lower_window = -2, 
                               upper_window = 1)

# Grundlovsdag
grundlovsdag = create_holiday_df(holiday_name = 'Grundlovsdag', 
                               start_month = 6, 
                               start_day = 5, 
                               end_month = 6, 
                               end_day = 5)

# Sankt Hans Aften 
sankt_hans_aften = create_holiday_df(holiday_name = 'Sankt Hans Aften', 
                               start_month = 6, 
                               start_day = 24, 
                               end_month = 6, 
                               end_day = 24)

# Halloween
halloween = create_holiday_df(holiday_name = 'Halloween', 
                               start_month = 10, 
                               start_day = 31, 
                               end_month = 10, 
                               end_day = 31)


# Valentinsdag 
valentinsdag = create_holiday_df(holiday_name = 'Valentinsdag', 
                               start_month = 2, 
                               start_day = 14, 
                               end_month = 2, 
                               end_day = 14)

# Sommerferie
sommerferie = create_holiday_df(holiday_name = 'Sommerferie', 
                               start_month = 6, 
                               start_day = 25, 
                               end_month = 8, 
                               end_day = 5)

# Vinterferie 
vinterferie = create_holiday_df(holiday_name = 'Vinterferie', 
                               start_month = 2, 
                               start_day = 10, 
                               end_month = 2, 
                               end_day = 17,
                               lower_window = -2, 
                               upper_window = 2)

# Efterårsferie 
efteraarsferie = create_holiday_df(holiday_name = 'Efteraarsferie', 
                               start_month = 10, 
                               start_day = 12, 
                               end_month = 10, 
                               end_day = 17,
                               lower_window = -2, 
                               upper_window = 2)

#______________________________
# Calculating holidays that are based on the Easter date

years = range(2020, 2031)

# Empty dataframe to hold all the holidays
holidays_df = pd.DataFrame()
# Empty list to store holiday data
holidays_list = []

for year in years:
    # Pull the date for Easter Sunday for the year.
    easter_sunday = easter.easter(year)

    # Calculate other holidays based on Easter.
    holidays_data = [
        {'ds': easter_sunday - pd.Timedelta(days=3), 'holiday': 'Skaertorsdag'},
        {'ds': easter_sunday - pd.Timedelta(days=2), 'holiday': 'Langfredag'},
        {'ds': easter_sunday + pd.Timedelta(days=1), 'holiday': 'Anden paaskedag'},
        {'ds': easter_sunday + pd.Timedelta(days=(4 * 7 - 2)), 'holiday': 'Store Bededag'},
        {'ds': easter_sunday + pd.Timedelta(days=39), 'holiday': 'Kristi Himmelfartsdag'},
        {'ds': easter_sunday + pd.Timedelta(days=49), 'holiday': 'Pinsedag'},
        {'ds': easter_sunday + pd.Timedelta(days=50), 'holiday': 'Anden Pinsedag'},
        {'ds': easter_sunday - pd.Timedelta(days=49), 'holiday': 'Fastelavn'}
    ]

    # Convert holidays data for the year into a dataframe and add it to the list.
    holidays_list.append(pd.DataFrame(holidays_data))

# Concatenate all dataframes in the list into a single dataframe.
holidays_df = pd.concat(holidays_list, ignore_index=True)
#______________________________

# All holidays are combined
all_holidays_df = pd.concat([holidays_df, 
                             nytaar, 
                             juleaften, 
                             grundlovsdag, 
                             sankt_hans_aften, 
                             halloween, 
                             valentinsdag,
                             sommerferie,
                             vinterferie,
                             efteraarsferie])

#______________________________________________________________________________

property_id = 'properties/254492974'  
start_date = '2022-01-01'
end_date = '2023-01-31'

session_data = get_ga4_daily_sessions(service_ga4, property_id, start_date, end_date)
print(session_data)

#
session_data = session_data.rename(columns={'Date': 'ds', 'Sessions': 'y'})

# Setting the floor of the predictions to zero to avoid negative forecasts
session_data['floor'] = 0
# The highest ammount of sessions historically is found
max_sessions = int(session_data['y'].max())
# Set the cap to this maximum value for all rows
session_data['cap'] = max_sessions 

# Initialize the Prophet model
model = Prophet(growth = 'logistic',
                holidays=all_holidays_df, # Include holidays in the model
                changepoint_prior_scale = 0.01,
                holidays_prior_scale = 5,
                daily_seasonality = True)

# Add custom weekly seasonality
model.add_seasonality(name='custom_weekly', period=7, fourier_order=10)
# Add custom weekly seasonality
model.add_seasonality(name='custom_yearly', period=365.25, fourier_order=10)

# Fit model
model.fit(session_data)

# Choose number of days to be forecasted
forecast_days = 60
# Define days to be forecasted in the model
future = model.make_future_dataframe(periods = forecast_days)

# Add cap and floor to the future dataframe
future['floor'] = 0
future['cap'] = max_sessions

# Predict the number of days
forecast = model.predict(future)


###############################################################################
################################# Plots #######################################
###############################################################################

# Standard prophet plot
fig1 = model.plot(forecast)
#_____________________________________
# Smoothed version of plotted data and forecast

# Drop cap and floor columns for visual purpose
forecast = forecast.drop(['cap', 'floor'], axis = 1)
# Calculate a rolling average of the forecasted 'yhat' values
forecast['yhat_smooth'] = forecast['yhat'].rolling(window=7, center=True).mean()
# Plot the original forecast
fig = model.plot(forecast)
# Overlay the smoothed predictions
plt.plot(forecast['ds'], forecast['yhat_smooth'], color='red', label='Smoothed Forecast')
# Add a legend 
plt.legend()
# Define x and y labels
plt.xlabel('Date')
plt.ylabel('Sessions')
# Show the plot
plt.show()

#_____________________________________
# Smoothed version of plotted forecast data

# Find the last historical date
last_historical_date = session_data['ds'].max()

# Filter the forecast dataframe to only the forecasted period, which is after the last historical date
forecasted_only = forecast[forecast['ds'] > last_historical_date]

# Calculate a rolling average of the forecasted 'yhat' values for the forecasted period only
forecasted_only['yhat_smooth'] = forecasted_only['yhat'].rolling(window=7, min_periods=1, center=True).mean()

# Plot the forecasted data only
plt.figure(figsize=(10, 6))
plt.plot(forecasted_only['ds'], forecasted_only['yhat'], label='Forecast')
plt.fill_between(forecasted_only['ds'], forecasted_only['yhat_lower'], forecasted_only['yhat_upper'], alpha=0.2, label='Confidence Interval')
plt.plot(forecasted_only['ds'], forecasted_only['yhat_smooth'], color='red', label='Smoothed Forecast')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Forecasted Value')
plt.title('Forecasted Period Only - with Smoothed Line')
plt.show()


#_____________________________________
# Plot holiday components

# Extract the holiday names from the columns (assuming the holiday effect columns follow the pattern 'holidayname')
holiday_names = set(col for col in forecast.columns if not col.endswith(('lower', 'upper', 'smooth')) and 
                    col not in ['cap','floor','ds', 'trend', 'yhat', 'yhat_lower', 'yhat_upper', 'trend_lower', 'trend_upper', 'additive_terms', 'additive_terms_lower', 'additive_terms_upper', 'holidays', 'holidays_lower', 'holidays_upper', 'weekly', 'weekly_lower', 'weekly_upper', 'multiplicative_terms', 'multiplicative_terms_lower', 'multiplicative_terms_upper']
                    and not col.startswith(('custom', 'daily'))) 


# Plot the holiday effects
plt.figure(figsize=(10, 6))
for holiday_name in holiday_names:
    # Prophet outputs the effects with the holiday names as columns
    plt.plot(forecast['ds'], forecast[holiday_name], label=holiday_name)

plt.title('Holiday Effects')
plt.xlabel('Date')
plt.ylabel('Effect')
# Place the legend outside of the plot
plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')

# Adjust the layout to make room for the legend
plt.tight_layout(rect=[0, 0, 1, 1])
plt.show()

#_____________________________________
# Plot seasonality components

# Extract the holiday names from the columns (assuming the holiday effect columns follow the pattern 'holidayname')
seasonality_names = set(col for col in forecast.columns if not col.endswith(('lower', 'upper', 'smooth')) and
                    col not in ['cap', 'floor', 'ds', 'trend', 'yhat', 'yhat_lower', 'yhat_upper', 'trend_lower', 'trend_upper', 'additive_terms', 'additive_terms_lower', 'additive_terms_upper',
                                'holidays', 'holidays_lower', 'holidays_upper', 'weekly', 'weekly_lower', 'weekly_upper', 'multiplicative_terms', 'multiplicative_terms_lower', 'multiplicative_terms_upper']
                    and not col.startswith(('Anden Pinsedag',
                                            'Anden paaskedag',
                                            'Efteraarsferie',
                                            'Fastelavn',
                                            'Grundlovsdag',
                                            'Halloween',
                                            'Juleaften',
                                            'Kristi Himmelfartsdag',
                                            'Langfredag',
                                            'Nytaar',
                                            'Pinsedag',
                                            'Sankt Hans Aften',
                                            'Skaertorsdag',
                                            'Sommerferie',
                                            'Store Bededag',
                                            'Valentinsdag',
                                            'Vinterferie')))


# Plot the holiday effects
plt.figure(figsize=(10, 6))
for seasonality_name in seasonality_names:
    # Prophet outputs the effects with the holiday names as columns
    plt.plot(forecast['ds'], forecast[seasonality_name], label=seasonality_name)

plt.title('Seasonality Effects')
plt.xlabel('Date')
plt.ylabel('Effect')
# Place the legend outside of the plot
plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')

# Adjust the layout to make room for the legend
plt.tight_layout(rect=[0, 0, 1, 1])
plt.show()

#_____________________________________
# Plot weekly components

# Extract the day of the week from the 'ds' column
forecast['day_of_week'] = forecast['ds'].dt.day_name()

# Group by the day of the week and take the mean to get the average seasonal effect per day
weekly_effect = forecast.groupby('day_of_week')['weekly'].mean().reindex([
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'
])

# Now plot the weekly effect
plt.figure(figsize=(10, 6))
weekly_effect.plot(kind='line')
plt.title('Weekly Seasonality')
plt.xlabel('Day of Week')
plt.ylabel('Effect')
plt.show()



###############################################################################
############################## Model Validation ###############################
###############################################################################

# Cross validation

# Perform time series cross-validation using the specified time intervals
# 'initial' specifies the training period length, 
# 'period' determines the spacing between cutoff dates,
# and 'horizon' defines the length of the forecast horizon for each fold.
model_validation = cross_validation(model, initial='240 days', period='60 days', horizon = '30 days')

# Calculate evaluation metrics
res = performance_metrics(model_validation)

# Calculate the averages
average_metrics = res[['mse', 'rmse', 'mae', 'mape']].mean().tolist()
print(average_metrics)

# Explanation of each metric:
# MSE (Mean Squared Error): Measures the average of the squares of the errors, 
# i.e., the average squared difference between the estimated values and the actual value.
# A lower MSE indicates a better fit of the model to the data.

# RMSE (Root Mean Squared Error): The square root of the average of squared differences 
# between prediction and actual observation. It's a measure of the accuracy of the model 
# in predicting the data. Like MSE, a lower RMSE is better.

# MAE (Mean Absolute Error): Measures the average magnitude of the errors in a set of predictions, 
# without considering their direction. It's the average over the test sample of the absolute differences 
# between prediction and actual observation where all individual differences have equal weight.
# A lower MAE indicates a better fit of the model to the data.

# MAPE (Mean Absolute Percentage Error): Measures the size of the error in percentage terms. 
# It is calculated as the average of the absolute percentage errors of the predictions.
# A lower MAPE indicates a better fit of the model to the data, with values closer to 0% being ideal.

# Plot evaluation metrics
plot_cross_validation_metric(model_validation, metric= 'mse')
plot_cross_validation_metric(model_validation, metric= 'rmse')
plot_cross_validation_metric(model_validation, metric= 'mae')
plot_cross_validation_metric(model_validation, metric= 'mape')
#___________________________







