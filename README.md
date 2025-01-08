# GA4 Session Predictor

https://github.com/user-attachments/assets/45758ce1-fea8-4119-858a-56f9a88849d2  

## Overview
This repository firstly, contains a standalone script for testing local app functionalities, model parameter adjustment and model validation. This script also allows for visualizing forecasts and seasonality/holiday effects. Secondly, this repository contains both the backend and frontend for a Flask app that can predict the number of daily website sessions measured in GA4, based on historical data. The idea behind the setup of the repository being that one can adjust and test the model parameters, until it performs at a satisfactory level on the data of the desired GA4 property. The model can then be applied in the backend of the Flask app, which ultimately provides a solid tool for predicting your daily GA4 sessions.

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
![image](https://github.com/user-attachments/assets/abf4e0f1-36ed-467d-a53d-99f43468fb19)  
  
#### Example of plotted forecasted daily sessions only:  
![image](https://github.com/user-attachments/assets/add48a6c-8c2c-43df-8fd1-93102a09859d)  

#### Example of plotted holiday effects:  
![image](https://github.com/user-attachments/assets/ed46beb7-7b6b-47a0-a5b4-980969319f41)   

#### Example of plotted seasonality effects:  
![image](https://github.com/user-attachments/assets/2cdab991-350b-459a-a813-22b99c6fc987)  

#### Example of plotted weekly effects:  
![image](https://github.com/user-attachments/assets/b2cfbb44-5fc2-4ee8-8dc1-9f72f37ac089)  
  
#### Example of plotted average model performance metrics  

Lastly, the script contains a section for cross validation, which can be adjusted as needed. This section calculates the average evaluation metrics 'mse', 'rmse', 'mae', 'mape' and also allows for the visualization of those.  

<table>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/7dfe419a-4da1-431f-b279-6668995156d0" alt="Image 1" width="300"/></td>
    <td><img src="https://github.com/user-attachments/assets/a54c9033-debe-4551-b763-eba667dc3137" alt="Image 2" width="300"/></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/3c9a13ca-d3d9-4a20-a337-576292f7f7f3" alt="Image 3" width="300"/></td>
    <td><img src="https://github.com/user-attachments/assets/1b18bc15-051f-43c9-9a43-7906d2d412af" alt="Image 4" width="300"/></td>
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

