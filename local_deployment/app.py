from flask import Flask, render_template, request, redirect, url_for, session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
import os
import google.auth.transport.requests
import requests
from pathlib import Path
import pandas as pd
from datetime import date, timedelta
from dateutil import easter
from prophet.diagnostics import cross_validation, performance_metrics
from prophet.plot import plot_cross_validation_metric
from prophet import Prophet


app = Flask(__name__)

# Secret key for session managament
app.secret_key = 'secret_key_placeholder'  # Use a secure key in production

###############################################################################
###################### GOOGLE LOGIN FUNCTIONALITIES ###########################
###############################################################################

GOOGLE_CLIENT_ID = Path('C:/Users/allan/Desktop/Personlige projekter/client_id_GAFlaskApp.json').read_text()
GOOGLE_CLIENT_SECRET = Path('C:/Users/allan/Desktop/Personlige projekter/client_secret_GAFlaskApp.json').read_text()
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")

# Allows OAuth over http. Used for development, should be removed in production.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Function to launch an OAuth login flow
def get_google_oauth_flow():
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        # Redirect to the callback route
        redirect_uri=url_for('callback', _external=True, _scheme='http')
    )

# Function to create service object
def create_service_object(api, version):
    creds_dict = session.get('credentials')
    if creds_dict:
        credentials = Credentials.from_authorized_user_info(creds_dict)
        service = build(api, version, credentials=credentials)
        return service
    return None

# Index route
@app.route('/')
def index():
    # Directly redirects to the login route
    return redirect(url_for('login'))

# Google OAuth login route
@app.route('/login')
def login():
    # Initiates OAuth login flow in browser
    flow = get_google_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    # State token saved in session
    session['state'] = state
    return redirect(authorization_url)

# Callback route that redirects to the choose_account page
@app.route('/callback')
def callback():
    flow = get_google_oauth_flow()
    flow.fetch_token(authorization_response=request.url)
    
    # Ensuring state token that is stored in the session is the same as the one 
    # returned from the callback
    if not session['state'] == request.args['state']:
        return 'State does not match!', 400
    
    # Credentials from OAuth flow stored in session
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return redirect(url_for('choose_account'))

# Logout route
@app.route('/logout')
def logout():
    # Clear the session of all credentials 
    session.clear()
    return redirect(url_for('login'))

###############################################################################
####################### ACCOUNT AND PROPERTY SELECTION ########################
###############################################################################

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


# Route for the choose_account page that pulls all the available GA4 accounts 
# and properties after login has been made
@app.route('/choose-account', methods=['GET', 'POST'])
def choose_account():
    # Create service object
    service_object = create_service_object('analyticsadmin', 'v1alpha')
    
    # Get accounts and properties dataframe
    df = list_ga4_accounts_and_properties_dataframe(service_object)
    
    selected_account_id = None
    properties = []
    
    if request.method == 'POST':
        # User has made a selection; fetch properties for the selected account
        selected_account_id = request.form.get('account')
        properties = df[df['Account ID'] == selected_account_id].to_dict('records')
    else:
        # No selection made yet; provide empty properties list
        properties = []
    
    # Get unique list of accounts for the initial dropdown
    accounts = df[['Account ID', 'Account Name']].drop_duplicates().to_dict('records')
    
    return render_template('choose_account.html', accounts=accounts, properties=properties, selected_account_id=selected_account_id)

# Route for handling choosen account and property and storing their ID's in the session
@app.route('/selection-handler', methods=['POST'])
def handle_selection():
    # Get selected account and property from the form submission
    selected_account_id = request.form.get('account')
    selected_property_id = request.form.get('property')
    
    # Store the selection in the session
    session['selected_account_id'] = selected_account_id
    session['selected_property_id'] = selected_property_id
    
    # Redirect to the dashboard page, passing the selections
    return redirect(url_for('dashboard', selected_account_id=selected_account_id, selected_property_id=selected_property_id))

###############################################################################
############################ DAILY SESSIONS CHART #############################
###############################################################################

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

###############################################################################
############################### PREDICTION CHART ##############################
###############################################################################

# Function to calculate static holidays
def create_holiday_df(holiday_name, start_month, start_day, end_month, end_day, years = range(2020, 2031), lower_window=0, upper_window=0):
    holiday_list = []
    for year in years:
        start_date = pd.Timestamp(year=year, month=start_month, day=start_day) + pd.Timedelta(days=lower_window)
        end_date = pd.Timestamp(year=year, month=end_month, day=end_day) + pd.Timedelta(days=upper_window)
        date_range = pd.date_range(start=start_date, end=end_date)
        for day in date_range:
            holiday_list.append({'holiday': holiday_name, 'ds': day, 'lower_window': lower_window, 'upper_window': upper_window})
    return pd.DataFrame(holiday_list)

def danish_holidays():
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
    
    return all_holidays_df

# Function to predict number of daily sessions
def predict_sessions(session_data, days_to_forecast):
    
    # Rename columns to fit Prophet standards
    session_data = session_data.rename(columns={'Date': 'ds', 'Sessions': 'y'})

    # Initialize the Prophet model
    model = Prophet()
    
    # Setting the floor of the predictions to zero to avoid negative forecasts
    session_data['floor'] = 0
    # The highest ammount of sessions historically is found
    max_sessions = int(session_data['y'].max())
    # Set the cap to this maximum value for all rows
    session_data['cap'] = max_sessions
    
    # Initializing Prophet model
    all_holidays_df = danish_holidays()
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
    forecast_days = days_to_forecast
    # Define days to be forecasted in the model
    future = model.make_future_dataframe(periods = forecast_days)
    
    # Add cap and floor to the future dataframe
    future['floor'] = 0
    future['cap'] = max_sessions
    
    # Predict the number of days
    forecast = model.predict(future)
    
    # Find the last historical date
    last_historical_date = session_data['ds'].max()
    # Filter the forecast dataframe to only the forecasted period, which is after the last historical date
    forecasted_only = forecast[forecast['ds'] > last_historical_date]
    # Select only the relevant columns
    forecasted_only = forecasted_only[['ds', 'yhat']]
    
    # Rename columns
    forecasted_only.rename(columns = {'ds': 'Date', 'yhat':'Sessions'}, inplace = True)
    
    # Rounding number of daily sessions
    forecasted_only['Sessions'] = round(forecasted_only['Sessions'])
    
    return forecasted_only

# Route for the dashboard page where historical and predicted number of daily sessions is shown
@app.route('/dashboard')
def dashboard():
    # Create service object
    service_object = create_service_object('analyticsdata', 'v1beta')
    
    # The dates from 2 years ago and 2 days ago are defined
    start_date = (date.today() - timedelta(days=730)).strftime("%Y-%m-%d")
    end_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
    
    # Default data for the last 2 years of session data is imported
    daily_sessions = get_ga4_daily_sessions(service_object, session['selected_property_id'], start_date, end_date)
    #_______________________________________
    forecasted_sessions = None
    # Check if forecast_days parameter is present in the request
    if 'forecast_days' in request.args and request.args['forecast_days']:
        forecast_days = int(request.args.get('forecast_days'))
        forecasted_sessions = predict_sessions(daily_sessions, forecast_days)
        # Concatenate forecasted sessions with real sessions
        daily_sessions = pd.concat([daily_sessions, forecasted_sessions], ignore_index=True, axis=0)
        
        # If forecast_days parameter is defined, show both data for daily_sessions and forecasted_sessions
        return render_template('dashboard.html', daily_sessions = daily_sessions.to_dict(orient='records'),
                               forecasted_sessions = forecasted_sessions.to_dict(orient='records'))
    else:
        # If forecast_days parameter is NOT defined, show only data for daily_sessions
        return render_template('dashboard.html', daily_sessions = daily_sessions.to_dict(orient='records'))


if __name__ == '__main__':
    app.run(debug=True)  # Turn off debug mode in production
