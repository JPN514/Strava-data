#Strava data in 2023
#More strava data analysis using pandas, plt, SQL and others

import pandas as pd
import requests
import json
import time
import numpy as np
import datetime
from matplotlib import pyplot as plt
import seaborn as sns

## Get the tokens from file to connect to Strava
with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)
## If access_token has expired then use the refresh_token to get the new access_token
if strava_tokens['expires_at'] < time.time():
#Make Strava auth API call with current refresh token
    response = requests.post(
                        url = 'https://www.strava.com/oauth/token',
                        data = {
                                'client_id': 0,
                                'client_secret': '',
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
url = "https://www.strava.com/api/v3/activities"
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
            "start_latlng",
            "end_latlng",
            "location_city",
            "achievement_count",
            "kudos_count",
            "average_speed",
            "max_speed",
            "elev_high",
            "elev_low",
            "pr_count"
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
        activities.loc[x + (page-1)*200,'start_latlng'] = r[x]['start_latlng']
        activities.loc[x + (page-1)*200,'end_latlng'] = r[x]['end_latlng']
        activities.loc[x + (page-1)*200,'location_city'] = r[x]['location_city']
        activities.loc[x + (page-1)*200,'achievement_count'] = r[x]['achievement_count']
        activities.loc[x + (page-1)*200,'kudos_count'] = r[x]['kudos_count']
        activities.loc[x + (page-1)*200,'average_speed'] = r[x]['average_speed']
        activities.loc[x + (page-1)*200,'max_speed'] = r[x]['max_speed']
        #activities.loc[x + (page-1)*200,'elev_high'] = r[x]['elev_high']
        #activities.loc[x + (page-1)*200,'elev_low'] = r[x]['elev_low']
        activities.loc[x + (page-1)*200,'pr_count'] = r[x]['pr_count']

# increment page
    page += 1
activities.to_csv('strava_activities_2023.csv')







#Manipulation of the dataframe starts here:

#print(activities.head())
#print out the datatypes
#print(activities.dtypes) 

#Firstly, get the year of each activity:
activities['year'] = activities.start_date_local.str[0:4] #need the first 4 chars of the start_date_local column
activities['month'] = activities.start_date_local.str[5:7] #this gives the two digits for the month 


#Rename and recalculate the distance column as km instead of meters:
activities = activities.rename(columns={'distance':'distance_km'})
activities.distance_km = activities.distance_km/1000



#Now convert the kilometers into miles and rename the column:
activities.distance_km = activities.distance_km * 0.6213711922
activities = activities.rename(columns={'distance_km':'distance_miles'})



#Recalculating paces and times into mins per mile, unfortunately will be in decimal form.
activities['pace_mins_per_mile_moving'] = activities.moving_time/60/activities.distance_miles #unfortunately is a decimal
activities['pace_mins_per_mile_elapsed'] = activities.elapsed_time/60/activities.distance_miles #unfortunately is a decimal
activities.elapsed_time = activities.elapsed_time/60 #converts seconds to minutes
activities.moving_time = activities.moving_time/60 #converts seconds to minutes



#Covert max speed to mins per mile using a lambda function to fill in NaN values for now:
#unsure if max speed is my fatest split as on the app or otherwise?
mylambda = lambda pace: 1 if pace == 0 else pace  
activities["max_speed_true"] = activities.max_speed.apply(mylambda)
activities.max_speed_true = 26.8224 / activities.max_speed_true
#print(activities[activities["max_speed_true"] != 26.8224])         #this has filled in 3 runs missing a value for max_speed 



#Convert the elevation columns from meters to feet as shown on app:
activities.total_elevation_gain = activities.total_elevation_gain *3.280839895 #maybe need to round this for calculations ?
#print(activities.total_elevation_gain.head())



#Fill in gaps in elevation using average elevation:
print(activities[activities.total_elevation_gain == 0].id.count())
elevation = activities[activities.total_elevation_gain != 0] #all runs with nonzero elevation
elevation_mean = elevation.total_elevation_gain.mean()
#print(elevation_mean)
mylambda = lambda elevation : elevation_mean if elevation == 0 else elevation
activities.total_elevation_gain = activities.total_elevation_gain.apply(mylambda) 
#print(activities[activities.total_elevation_gain == 0].id.count())



#Fixing the location_city using start_latlng and end_latlng and my anecdata about where I was at the time of these runs:
#We will use the first part of the start_latlng observation to obtain a location either Birmingham, Swindon or Mallorca. 
activities["start_latlng"] = activities.start_latlng.fillna(0)
activities.start_latlng = activities.start_latlng.apply(lambda row : str(row[0:1]))
activities["location_lat"] = activities.start_latlng.apply(lambda row : str(row[1:3])) #the two lambda functions allow us to get the first two digits of the latitude (how far north I was)

print(activities.location_lat.unique()) #shows all the different values, showing what we need to edit
activities["location_lat"] = activities["location_lat"].replace("]",'51') #gets rid of the ']' and replaces it with 51 which approximates Swindon's latitude
print(activities.location_lat.unique())
activities.location_lat = pd.to_numeric(activities.location_lat)

#We require a function to make the next lambda statement:
def location_condition(latitude):
    if latitude == 52:
        return "Birmingham"
    elif latitude == 51:
        return "Swindon"
    elif latitude == 39:
        return "Mallorca"
activities["location_city"] = activities.location_lat.apply(location_condition)


#Dropping undesired columns/renaming columns:
activities = activities.rename(columns={"moving_time":"moving_time_mins","elapsed_time":"elapsed_time_mins"})
activities = activities.rename(columns={"total_elevation_gain":"total_elev_gain_ft"})

#activities = activities.drop("start_latlng",axis=1) 
activities = activities.drop("end_latlng",axis=1)    #axis 1 is the column
activities = activities.drop("elev_high",axis=1)
activities = activities.drop("elev_low",axis=1)

print(activities.columns)



#A function to write my cleaned up data to a csv file:
def write_to_csv(df):
    df.to_csv("df_to_csv_strava_data_2023.csv")    
write_to_csv(activities)
   
    
# ::::::::::: SQL BELOW :::::::::::  
from python_SQL_functions import execute_query
from python_SQL_functions import read_query
from python_SQL_functions import into_mySQL
from python_SQL_functions import get_connection
 
into_mySQL(activities)

db_conn = get_connection() # this establishes a connection to mySQL database for whole program, use as connection for all SQL

# function to check number of runs >=n miles in distance using SQL, corroborated using the df:
def SQL_check():
    over = activities[activities.distance_miles >= 3].id.count() # using the df 
    print(over)
    
    select_count_query = """SELECT COUNT(*) FROM activities_test_table
                            WHERE distance_miles >= 3;"""
    select_count_result = read_query(db_conn,select_count_query)
    print(int(str(select_count_result)[2:].split(",")[0]))
    
    select_city_query = """SELECT DISTINCT location_city FROM activities_test_table;"""
    select_city_result = read_query(db_conn,select_city_query)
    print(select_city_result) 
    
SQL_check()


#:::::::::::::PLOTS BELOW :::::::::::

cities = activities.groupby("location_city").id.count().reset_index() #runs per city 
#print(cities)

#function to plot a simple test bar chart for runs per city:
def runs_per_city(cities): 
    plt.bar(cities.location_city,cities.id)
    plt.title("Total runs in each location")
    plt.xlabel("Location on Earth")
    plt.ylabel("Number of runs")
    plt.show()
    plt.clf()
#runs_per_city(cities)    

# function to plot histogram for minutes per mile:
def mins_per_mile_hist():
    
    mins_per_mile = activities['pace_mins_per_mile_moving']
    print(mins_per_mile.min(),mins_per_mile.max()) # to obtain the approx range for the bins
    mins_labels = np.arange(7.5, 12, 0.5).tolist()
    plt.hist(mins_per_mile,bins=9,range=(7.5,12),density=True)
    plt.title("Minutes per Mile")
    plt.xlabel("Minutes (Decimal)")
    plt.ylabel("Frequency")
    plt.xticks(mins_labels)
    plt.show()
    
    return
#mins_per_mile_hist()

# function to plot runs and distances by year as a bar chart:
def yearly_totals():
    # get the yearly totals for number of runs:
    t19 = activities[activities.year == '2019'].id.count()
    t20 = activities[activities.year == '2020'].id.count() # t20 is number of runs in 2020 
    t21 = activities[activities.year == '2021'].id.count() # note year column is a string
    t22 = activities[activities.year == '2022'].id.count()
    t23 = activities[activities.year == '2023'].id.count()
    print(t19,t20,t21,t22,t23) 
    
    # get the runs grouped by year and count from there: 
    run_count_by_year = activities.groupby("year").count()
    run_count_by_year = run_count_by_year.rename(columns={'id':'total_runs'})
    run_count_by_year = run_count_by_year["total_runs"]
    years = [2019,2020,2021,2022,2023]
    
    # bar chart for runs per year:
    plt.bar(years,run_count_by_year)
    plt.title("Number Of Runs By Calendar Year")
    plt.xlabel("Year")
    plt.ylabel("Run Count")
    plt.show()
    return
#yearly_totals()

# function to plot distances by year as a bar chart: 
def yearly_distances():
    distance_by_year = activities.groupby("year")
    distance_by_year = distance_by_year.distance_miles.sum()
    #distance_by_year = distance_by_year.rename(columns={"id" : "distance"})
    #distance_by_year = distance_by_year["distance"]
    years = [2019,2020,2021,2022,2023]
    print(distance_by_year)
    # bar chart for the distance in miles per calendar year:
    plt.bar(years,distance_by_year)
    plt.title("Yearly Mileage")
    plt.xlabel("Year")
    plt.ylabel("Miles")
    plt.show()
#yearly_distances()    

