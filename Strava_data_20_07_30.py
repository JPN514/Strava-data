import pandas as pd
import requests
import json
import time
import numpy as np
import datetime
from matplotlib import pyplot as plt

## top code taken from https://medium.com/swlh/using-python-to-connect-to-stravas-api-and-analyse-your-activities-dummies-guide-5f49727aac86
## in order to pull the data

## Get the tokens from file to connect to Strava
with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)
## If access_token has expired then use the refresh_token to get the new access_token
if strava_tokens['expires_at'] < time.time():
#Make Strava auth API call with current refresh token
    response = requests.post(
                        url = 'https://www.strava.com/oauth/token',
                        data = {
                                'client_id': 00000,
                                'client_secret': 'blank',
                                'grant_type': 'refresh_token',
                                'refresh_token': strava_tokens['refresh_token']
                                }
                    )

#Save response as json in new variable
    new_strava_tokens = response.json()
# Save new tokens to file
    with open('strava_tokens.json', 'w') as outfile:
        json.dump(new_strava_tokens, outfile)
#Use new Strava tokens from now
    strava_tokens = new_strava_tokens
#Loop through all activities
page = 1
url = "blank"
access_token = strava_tokens['access_token']
## Create the dataframe ready for the API call to store your activity data
activities = pd.DataFrame(
    columns = [
            "id",
            "name",
            "start_date_local",
            "type",
            "distance",
            "moving_time",
            "elapsed_time",
            "total_elevation_gain",
            "location_city",
            "average_speed",
            "max_speed"
    ]
)

while True:
    
    # get page of activities from Strava
    r = requests.get(url + '?access_token=' + access_token + '&per_page=200' + '&page=' + str(page))
    r = r.json()
# if no results then exit loop
    if (not r):
        break
    
    # otherwise add new data to dataframe
    for x in range(len(r)):
        activities.loc[x + (page-1)*200,'id'] = r[x]['id']
        activities.loc[x + (page-1)*200,'name'] = r[x]['name']
        activities.loc[x + (page-1)*200,'start_date_local'] = r[x]['start_date_local']
        activities.loc[x + (page-1)*200,'type'] = r[x]['type']
        activities.loc[x + (page-1)*200,'distance'] = r[x]['distance']
        activities.loc[x + (page-1)*200,'moving_time'] = r[x]['moving_time']
        activities.loc[x + (page-1)*200,'elapsed_time'] = r[x]['elapsed_time']
        activities.loc[x + (page-1)*200,'total_elevation_gain'] = r[x]['total_elevation_gain']
        activities.loc[x + (page-1)*200,'location_city'] = r[x]['location_city']
        activities.loc[x + (page-1)*200,'average_speed'] = r[x]['average_speed']
        activities.loc[x + (page-1)*200,'max_speed'] = r[x]['max_speed']

# increment page
    page += 1
activities.to_csv('strava_activities.csv')

#ANALYSIS STARTS FROM HERE:

#print(activities)

#rename and recalculate the distance column as km instead of meters.
activities = activities.rename(columns={'distance':'distance_km'})
activities.distance_km = activities.distance_km/1000

#recalculating paces and times.
activities['pace_mins_per_km'] = activities.moving_time/60/activities.distance_km #unfortunately is a decimal
activities.elapsed_time = activities.elapsed_time/60
activities.moving_time = activities.moving_time/60
#print(activities.columns)
#print(activities.moving_time)
#print(activities.elapsed_time)

#First plot to show runs by year
def first_plot():
    activities.start_date_local = activities.start_date_local.astype('str')
    activities['year'] = activities.start_date_local.str[0:4] #first get the year of the activity.
    runs_by_year = activities.groupby('year').count()
    runs_by_year = runs_by_year.rename(columns={'id':'total_runs'})
    runs_by_year = runs_by_year['total_runs']
    years = [2019,2020]

    plt.bar(years,runs_by_year)
    plt.title("Strava recorded runs by year.")
    plt.xlabel("Year")
    plt.xticks(years,[2019,2020])
    plt.ylabel("Number of runs")
    plt.show()
    plt.close()

#turn the start_date_local column into just the date
activities.start_date_local = activities.start_date_local.astype('str')
activities['date'] = activities.start_date_local.str[0:10]
del activities['start_date_local']
del activities['location_city']
#print(activities.head())

#find 5 longest runs by distance:
def top5_runs():
    activities.sort_values(by='distance_km',ascending=False,inplace=True,ignore_index=True)
    top5 = activities.head()
    print(top5)
    #plot showing distance of longest runs and the dates:
    plt.bar(top5['date'],top5['distance_km'])
    plt.title("Top 5 runs by distance")
    plt.xlabel("Date of run")
    plt.ylabel("Distance in km")
    plt.show()
    plt.close()

    #side by side bars for moving and elapsed times for each of the top 5 runs:
    N = 5 # number of pairs of bars
    ind = np.arange(N)
    plt.figure(figsize=(10,5))
    w = 0.3 #bar width
    plt.bar(ind,top5['moving_time'],w,label='moving time')
    plt.bar(ind+w,top5['elapsed_time'],w,label='elapsed time')
    plt.title("Comparison of moving time vs elapsed time for the top 5 runs by distance")
    plt.xlabel("Date of run")
    plt.ylabel("Time in minutes")
    plt.xticks(ind+w/2,top5['date'])
    plt.legend(loc='best')
    plt.show()
    plt.close()

#IQR and Boxplot for distance:
def boxplot_distances():
    pass





#first_plot()
# #top5_runs()
boxplot_distances()