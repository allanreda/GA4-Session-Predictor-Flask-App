# GA4 Session Predictor

https://github.com/allanreda/GA_Flask_App/assets/89948110/dd031df6-63fe-4ad8-8ec8-f146c2ff6b3f  
  
## Overview
This repository firstly, contains a standalone script for testing local app functionalities, model parameter adjustment and model validation. This script also allows for visualizing forecasts and seasonality/holiday effects. Secondly, this repository contains both the backend and frontend for a Flask app that can predict the number of daily website sessions measured in GA4, based on historical data. The idea behind the setup of the repository being that one can adjust and test the model parameters, until it performs at a satisfactory level on the data of the desired GA4 property. The model can then be applied in the backend of the Flask app, which ultimately provides the perfect tool for predicting your daily GA4 sessions.

## Functionality

### functionalities.py:
This script contains the foundation of the functionalities in the backend of the Flask app, thus the name of the script. It contains the functions that lists all available GA4 accounts and properties to the logged in user, and the function that pulls all the daily sessions of the last two years (if available).   
Most important of all, it contains the model itself with all of its parameters, which provides the opportunity to experiment and add new ones or remove existing ones. The model is also trained on all Danish holidays/vacations, which can also be added/removed.   
<pre lang="no-highlight"><code>
# Initialize the Prophet model
model = Prophet(growth = 'logistic',
                holidays=all_holidays_df, # Include holidays in the model
                changepoint_prior_scale = 0.01,
                holidays_prior_scale = 5,
                daily_seasonality = True)
</code></pre>
The forecasts of the model can then be visualized, together with its seasonality/holiday effects.  

#### Example of plotted historical and forecasted daily sessions:  
![image](https://github.com/allanreda/GA_Flask_App/assets/89948110/569e8b9b-4f99-49e8-bc7b-c1f4fd9c6b60)
  
#### Example of plotted forecasted daily sessions only:  
![image](https://github.com/allanreda/GA_Flask_App/assets/89948110/8f3dd978-ae7d-484f-805b-b4ba1daa033b)

#### Example of plotted holiday effects:  
![image](https://github.com/allanreda/GA_Flask_App/assets/89948110/10aae05c-f7a9-4690-bef9-d785cf9117ea)  

#### Example of plotted seasonality effects:  
![image](https://github.com/allanreda/GA_Flask_App/assets/89948110/4e597bef-072e-43c0-9389-66b89fa5a6ae)

#### Example of plotted weekly effects:  
![image](https://github.com/allanreda/GA_Flask_App/assets/89948110/2889c825-7bd0-4d4e-b03b-0d88dbae2d0e)  
  
#### Example of plotted average model performance metrics  

Lastly, the script contains a section for cross validation, which can be adjusted as needed. This section calculates the average evaluation metrics 'mse', 'rmse', 'mae', 'mape' and also allows for the visualization of those.  

<table>
  <tr>
    <td><img src="https://github.com/allanreda/GA_Flask_App/assets/89948110/0778b091-8c8c-484c-94d1-2bd6b453855f" alt="Image 1" width="300"/></td>
    <td><img src="https://github.com/allanreda/GA_Flask_App/assets/89948110/86dd8e57-0cb6-4e31-9b53-d3741d2e0a42" alt="Image 2" width="300"/></td>
  </tr>
  <tr>
    <td><img src="https://github.com/allanreda/GA_Flask_App/assets/89948110/071ed5bb-c9d5-42b4-a3c9-4eaa93a279c4" alt="Image 3" width="300"/></td>
    <td><img src="https://github.com/allanreda/GA_Flask_App/assets/89948110/f1518ef9-45e9-47c4-a7cf-432dd9881ab2" alt="Image 4" width="300"/></td>
  </tr>
</table>

### local_deployment (folder for the Flask app script)
The folder contains both the backend of the Flask app, in the form of the app.py file, and the frontend the app, in the form of the three templates in the "templates" folder.  
All together they make up the three components that makes up the app itself.  
The first part is the login which activates the OAuth flow which allows for the user to log in to the Google account that has access to the desired GA4 account(s).  
The second part is where the user gets to choose the desired GA4 account and property, from which the historical sessions will be pulled.  
The third and most important part, is where the user will see the historical daily sessions displayed on the left chart and have the opportunity to choose a number of days to forecast. The forecasted daily sessions will then be displayed in the right chart.

## Technologies  
The project is built using:  
-Flask for building and interactive interface  
-The Google Analytics Admin API (v1alpha) for accessing available GA4 accounts and properties  
-The Google Analytics 4 API for pulling historical number of daily sessions  
-Prophet for model creation, time series forecasting and cross validation  
-Matplotlib for visualisation  
-Pandas for data manipulation

## Goal
The aim of this project is to empower Danish GA4 users and website owners to forecast daily session counts and understand the impact of seasons, holidays, and vacations on web traffic. The project provides a user-friendly interface that can be deployed locally and used to anticipate future traffic. Additionally, it offers a straightforward method for comprehending historical web traffic patterns and their determinants.

