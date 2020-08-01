import pandas as pd
import requests
import json
import time
import numpy as np
import datetime
from matplotlib import pyplot as plt
import seaborn as sns

#used code from https://medium.com/swlh/using-python-to-connect-to-stravas-api-and-analyse-your-activities-dummies-guide-5f49727aac86
#to download my data
#Have had to leave out sensitive data in the request sections

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
url = "https://www.strava.com"
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

#IQR and Boxplot for distance and paces:
def boxplot_distances():
    #boxplot of distance in km
    plt.figure(figsize=(10,5))
    plt.boxplot([activities['distance_km']],vert=0,patch_artist=True,labels=[""]) 
    plt.title("Boxplot of distances of runs in km")
    plt.xlabel("Kilometers")
    plt.show()
    plt.close()
    
    #we split the runs into two groups to get a better boxplot
    #above 10km and below 10km.
    ten_km_or_more = activities[activities.distance_km >=10]
    less_than_ten_km = activities[activities.distance_km < 10]
    ten_km_or_more.sort_values(by='distance_km',ascending=False,inplace=True,ignore_index=True)
    less_than_ten_km.sort_values(by='distance_km',ascending=False,inplace=True,ignore_index=True)
    #print(ten_km_or_more.head())
    #print(less_than_ten_km.head())
    plt.figure(figsize=(10,5))
    plt.boxplot([ten_km_or_more['distance_km'],less_than_ten_km['distance_km']],vert=0,patch_artist=True,labels=["10km or greater","Less than 10km"])
    plt.xlabel("Distance in km")
    plt.title("Comparing runs of more than 10km and runs of less than 10km")
    plt.show()
    plt.close()

    #boxplot of pace in mins/km
    plt.figure(figsize=(10,5))
    plt.boxplot(activities['pace_mins_per_km'],vert=0,patch_artist=True,labels=[""]) 
    plt.title("Boxplot of pace in mins/km")
    plt.xlabel("Mins per km")
    plt.show()
    plt.close()

#To find runs per month and distance per month:
def runs_by_month():
    #this is to collect data grouped by month.
    activities['month'] = activities.date.str[5:7]
    month_activities = activities.groupby('month')
    months_runs = month_activities['month'].count()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    #number of runs per month bar chart
    plt.figure(figsize=(10,5))
    plt.bar(month_names,months_runs)
    plt.title("Number of runs per calendar month.")
    plt.xlabel("Months")
    plt.ylabel("Number of runs")
    plt.show()
    plt.close()
    #can clearly see July is my top month for running.
    
    #to find distance covered by month in a bar chart 
    months_distance = month_activities['distance_km'].sum()
    #print(months_distance)
    plt.figure(figsize=(10,5))
    plt.bar(month_names,months_distance)
    plt.title("Distance by month in km.")
    plt.xlabel("Months")
    plt.ylabel("Distance (km)")
    plt.show()
    plt.close()

    #line graph for distance per month and runs per month:
    plt.figure(figsize=(10,5))
    plt.plot(month_names,months_distance)
    plt.title("Distance per calendar month in km")
    plt.xlabel("Month")
    plt.ylabel("Distance")
    plt.show()
    plt.close()

    plt.figure(figsize=(10,5))
    plt.plot(month_names,months_runs)
    plt.title("Runs per calendar month")
    plt.xlabel("Month")
    plt.ylabel("Number of runs")
    plt.show()
    plt.close()

    #bubble plot by month for number of runs and distance covered:
    plt.figure(figsize=(10,10))
    plt.scatter(x=month_names,y=months_distance,s=months_runs*100) #number of runs per month as size
    plt.title("Bubbleplot for distance ran by month(no.of runs as size)")
    plt.xlabel("Month")
    plt.ylabel("Distance (km)")
    plt.show()
    plt.close()

    plt.figure(figsize=(10,10))
    plt.scatter(x=month_names,y=months_runs,s=months_distance*35) #distance covered as size
    plt.title("Bubbleplot for runs per month(distance as size)")
    plt.xlabel("Month")
    plt.ylabel("Number of runs")
    plt.show()
    plt.close()

#preparing a correlation matrix for all the important pace/distance/time fields
#shows no strong correlation between average pace per km and any other fields
def correlation_maps():
    corr_activities = activities 
    #get rid of unwanted columns
    del corr_activities['name']
    del corr_activities['id']
    del corr_activities['type']
    del corr_activities['date']
    del corr_activities['average_speed']
    del corr_activities['max_speed']
    #print(corr_activities.columns)
    #print(corr_activities)
    corr_activities = corr_activities.astype(float) #ensure all columns are floats
    corr = corr_activities.corr()
    plt.figure(figsize = (12,8))
    sns.heatmap(corr_activities.corr(), annot=True, fmt=".2f")
    plt.title("Correlation between time,pace and distance")
    plt.show()
    plt.close()

#making histograms for pace and distance:
def histograms():
    #for pace:
    #big chunk of this is between 5.10 and 5.80 or 5:06 to 5:48 mins/km
    bin_list = [4.75,5,5.1,5.2,5.3,5.4,5.5,5.6,5.7,5.8,5.9,6,6.25]
    plt.figure(figsize=(10,5))
    plt.hist(activities['pace_mins_per_km'],bins=bin_list,range=(4.75,6.25))
    plt.title("Number of runs by mins per kilometer")
    plt.xlabel("Minutes per kilometer(decimal)")
    plt.ylabel("Frequency")
    plt.xticks(bin_list)
    plt.show()
    plt.close()

    #for distance: shows no runs between 8km and 10km
    #lots less than 8km and some greater than 10km
    bin_list = [3,5,6,8,9,10,12.5,25]
    plt.figure(figsize=(10,5))
    plt.hist(activities['distance_km'],bins=bin_list)
    plt.title("Distances in km")
    plt.xlabel("Distance")
    plt.xticks(bin_list)
    plt.ylabel("Frequency")
    plt.show()
    plt.close()

#attempt to show distances by month on a scatterplot
def beehive_plot():
    activities['month'] = activities.date.str[5:7]
    month_activities = activities.groupby('month')
    plt.figure(figsize=(10,5))
    sns.stripplot(x="month", y="distance_km", data=activities['distance_km'])
    plt.show()
    plt.close()

def all_time_lines():
    #print(activities)
    #we put the runs in order of the date and map the distances on a line graph:
    activities.sort_values(by='date',ascending=True,inplace=True,ignore_index=True)
    plt.figure(figsize=(10,5))
    plt.plot(activities['distance_km'])
    plt.title("All time distances in km")
    plt.xlabel("Runs in chronological order")
    plt.ylabel("Distance")
    plt.show()
    plt.close()
    
    #line graph for pace in mins/km across all runs 
    plt.figure(figsize=(10,5))
    plt.plot(activities['pace_mins_per_km'])
    plt.title("All time pace in mins/km")
    plt.xlabel("Runs in chronological order")
    plt.ylabel("Mins/km")
    plt.show()
    plt.close()
    
    #moving and elapsed times as lines across all runs
    plt.figure(figsize=(10,5))
    plt.plot(activities['moving_time'],label='Moving time')
    plt.plot(activities['elapsed_time'],label='Elapsed time')
    plt.title("Moving vs elapsed times all data")
    plt.xlabel("Runs in chronological order")
    plt.ylabel("Minutes")
    plt.legend(loc="best")
    plt.show()
    plt.close()



def stacked_bars_time():
    #We overlap the elapsed time with the moving time(as it is smaller) to show the difference in these times across all runs
    plt.figure(figsize=(10,5))
    plt.bar(activities.index,activities['elapsed_time'],label='Elapsed time')
    plt.bar(activities.index,activities['moving_time'],label='Moving time')
    plt.title("Moving and elapsed times in minutes across all runs")
    plt.xlabel("Runs in chronological order")
    plt.ylabel("Minutes")
    plt.legend(loc='best')
    plt.show()
    plt.close()



#first_plot()
#top5_runs()
#boxplot_distances()
#runs_by_month()
#correlation_maps()
#histograms()
#beehive_plot()
#all_time_lines()
#stacked_bars_time()
