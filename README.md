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


## Technologies






## Goal
