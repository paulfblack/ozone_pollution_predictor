# -*- coding: utf-8 -*-
"""
Functions and Classes Used for Metis' Project Luther

Metis Chicago Spring 2017

Created on Tue Apr 25 22:06:14 2017

@author: Paul
"""
import pandas as pd
import numpy as np
import pickle
import dateutil.parser
import datetime
from datetime import datetime, date, timedelta
import time
import logging
from copy import deepcopy
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import requests
import re
import os
# Webscraping Functions
class weather_date:
    """Class for scraping weather_data from www.wunderground.com"""
    def __init__(self, soup_obj, zipcode, date):
        self.date = date
        self.soup_obj = soup_obj
        self.zipcode = zipcode
        self.sunrise = self.get_sunrise(soup_obj)
        self.sunset = self.get_sunset(soup_obj)
        self.dew_point = self.get_dew_point(soup_obj)
        self.events = self.get_events(soup_obj)
        self.sea_level_pressure = self.get_sea_level_pressure(soup_obj)
        self.temp = self.get_temp(soup_obj)
        self.humidity = self.get_humidity(soup_obj)
        self.degree_days = self.get_degree_days(soup_obj)
        self.wind = self.get_wind(soup_obj)
        self.precipitation = self.get_precipitation(soup_obj)
        self.snow = self.get_snow(soup_obj)
        self.moon_phase = self.get_moon_phase(soup_obj)
        self.weather_dict = self.create_dict() 
    
    # Preliminary cleaning of data
    def clean(self, result):
        pattern = re.compile(r'\\n|\\xa0|\\xc2|\\t|b\'|\\xb0|<\w+>|</\w+>|')
        return re.sub(pattern,'', str(result.encode('utf8')))
    
    def get_sunrise(self, soup):
        sunrise = soup.find(text='Actual Time').find_next('td').text
        return self.clean(sunrise)
    
    def get_sunset(self, soup):
        sunset = soup.find(text='Actual Time').find_next('td').find_next('td').text
        return self.clean(sunset)
    
    def get_dew_point(self, soup):
        dew_point = soup.find(text='Dew Point').find_next('td').text
        return self.clean(dew_point)
    
    def get_events(self, soup):
        events = soup.find(text='Events').find_next('td').text
        return self.clean(events)
    
    def get_sea_level_pressure(self, soup):
        sea_level_pressure = soup.find(text='Sea Level Pressure').find_next(text='Sea Level Pressure').find_next('td').text
        return self.clean(sea_level_pressure)
    
    def get_temp(self, soup):
        temp_regex = re.compile(' temperature', re.I)
        temp_entries = soup.find_all(text = temp_regex)
        temp_list = []
        for record in temp_entries:
            temp_list.append(self.clean(record.find_next('td').text))
        return temp_entries, temp_list
    
    def get_humidity(self, soup):
        hum_regex = re.compile(' humidity', re.I)
        hum_entries = soup.find_all(text = hum_regex)
        temp_list = []
        for record in hum_entries:
            temp_list.append(record.find_next('td').text.encode('utf8'))
        return hum_entries, temp_list
    
    def get_degree_days(self, soup):
        temp_list = []
        degree_days_regex = re.compile('ing degree days', re.I)
        degree_days = soup.find_all(text = degree_days_regex)
        for record in degree_days:
            temp_list.append(self.clean(record.find_next('td').text))
        return degree_days, temp_list
    
    def get_wind(self, soup):
        wind_regex = re.compile(' speed', re.I)
        wind_entries = soup.find_all(text = wind_regex)
        wind_entries = wind_entries[:3]
        temp_list = []
        for record in wind_entries[:3]:
            temp_list.append(self.clean(record.find_next('td').text))
        return wind_entries, temp_list
    
    def get_precipitation(self, soup):
        precipitation_regex = re.compile('precipitation', re.I)
        precipitation = soup.find_all(text=precipitation_regex)
        precipitation = precipitation[1:-1]
        temp_list = []
        for record in precipitation:
            temp_list.append(self.clean(record.find_next('td').text))
        return precipitation, temp_list
    
    def get_snow(self, soup):
        snow_regex = re.compile('snow', re.I)
        snow = soup.find(class_='history-table-grey-header', text=snow_regex)
        snow_entries = ['Snow', 'Month to date snowfall', 'Since 1 July snowfall', 'Snow Depth']
        snow_data = []
        for x in range(5):
            try:
                snow = snow.find_next(text=snow_regex)
                snow_entries.append(self.clean(snow.encode))
                snow_data.append(self.clean(snow.find_next('td').text))
            except AttributeError:
                while len(snow_data) < len(snow_entries):
                    snow_data.append(np.nan)
            logging.debug('Error pulling snow for date %s' % date)
        return snow_entries, snow_data
    
    def get_moon_phase(self, soup):
        moon_phase = soup.find(class_='phaseIcon').find_next('td').text
        return self.clean(moon_phase)

    def create_dict(self):
        temp_dict = {}
        temp_dict['Date'] = self.date
        temp_dict['Zipcode'] = self.zipcode
        temp_dict['Sunrise'] = self.sunrise
        temp_dict['Sunset'] = self.sunset
        temp_dict['Dew Point'] = self.dew_point
        temp_dict['Events'] = self.events
        temp_dict['Sea Level Pressure'] = self.sea_level_pressure
        for n in range(len(self.temp[0])):
            temp_dict[self.clean(self.temp[0][n])] = self.temp[1][n]
        for n in range(len(self.humidity[0])):
            temp_dict[self.clean(self.humidity[0][n])] = self.humidity[1][n]
        for n in range(len(self.degree_days[0])):
            temp_dict[self.clean(self.degree_days[0][n])] = self.degree_days[1][n]
        for n in range(len(self.wind[0])):
            temp_dict[self.clean(self.wind[0][n])] = self.wind[1][n]
        for n in range(len(self.precipitation[0])):
            temp_dict[self.clean(self.precipitation[0][n])] = self.precipitation[1][n]
        for n in range(len(self.snow[0])):
            temp_dict[self.clean(self.snow[0][n])] = self.snow[1][n]
        temp_dict['Moon Phase'] = self.moon_phase
        return temp_dict

def scrape_data(zipcode, earliest_date):
    """Takes a zipcode string and an earliest date and scrapes www.wunderground.com
    from yesterday until the earliest date.
    
    Date must be in this form: Monday, April 3, 2017 """
    #Initiate Driver
    chrome_options = Options()
    chrome_options.add_argument("-allow-running-insecure-content")
    driver = webdriver.Chrome('C:/Users/Paull/ds/metis/metisgh/chromedriver_win32/chromedriver', chrome_options=chrome_options)
    driver.get('https://www.wunderground.com/')
    time.sleep(1)
    #Navigate to specific zipcode's history page
    menu_button = driver.find_element_by_class_name("fi-list")
    menu_button.click()
    time.sleep(1)
    historical_weather_button = driver.find_element_by_link_text("Historical Weather")
    historical_weather_button.click()
    time.sleep(1)
    search_bar = driver.find_element_by_id('histSearch')
    search_bar.send_keys(zipcode)
    search_bar.send_keys(Keys.RETURN)
    #Skip today's date
    previous_button = driver.find_element_by_link_text('« Previous Day')
    previous_button.click()
    weather_page = BeautifulSoup(driver.page_source, 'html.parser')
    date = weather_page.find('h2', class_="history-date").text
    data_entry = weather_date(weather_page, zipcode, date)
    weather_df = pd.DataFrame(data_entry.weather_dict, index = [1])
    previous_button = driver.find_element_by_link_text('« Previous Day')
    previous_button.click()
    while date != earliest_date:
        try:
            current_url = driver.current_url
            weather_page = BeautifulSoup(driver.page_source, 'html.parser')
            date = weather_page.find('h2', class_="history-date").text
            data_entry = weather_date(weather_page, zipcode, date)
            temp_df = pd.DataFrame(data_entry.weather_dict, index = [1])
            dfs = [weather_df, temp_df]
            weather_df = pd.concat(dfs, axis = 0)
            time.sleep(1)
            previous_button = driver.find_element_by_link_text('« Previous Day')
            previous_button.click()
        except TimeoutException:
            logging.debug('Error pulling date for on date: %s' % date)
            driver.close()
            driver = webdriver.Chrome('C:/Users/Paull/ds/metis/metisgh/chromedriver_win32/chromedriver')
            driver.get(current_url)
            time.sleep(1)
            previous_button = driver.find_element_by_link_text('« Previous Day')
            previous_button.click()
    driver.close()
    pickle.dump(weather_df, open( zipcode + '_' + date + ".p", "wb") ) 
    return weather_df

def scrape_conditions(zipcode, earliest_date):
    """Takes a zipcode and earliest date and returns a dataframe with the hourly conditions
    for this zipcode from yesterday to earliest date as recorded by www.wunderground.com"""
    chrome_options = Options()
    chrome_options.add_argument("-allow-running-insecure-content")
    driver = webdriver.Chrome('C:/Users/Paull/ds/metis/metisgh/chromedriver_win32/chromedriver', chrome_options=chrome_options)
    driver.get('https://www.wunderground.com/');
    time.sleep(3)
    #Navigate to specific zipcode's history page
    menu_button = driver.find_element_by_class_name("fi-list")
    menu_button.click()
    time.sleep(3)
    historical_weather_button = driver.find_element_by_link_text("Historical Weather")
    historical_weather_button.click()
    time.sleep(3)
    search_bar = driver.find_element_by_id('histSearch')
    search_bar.send_keys(zipcode)
    search_bar.send_keys(Keys.RETURN)
    # Skip today's date
    previous_button = driver.find_element_by_link_text('« Previous Day')
    previous_button.click()
    # Find current date
    weather_page = BeautifulSoup(driver.page_source, 'html.parser')
    date = weather_page.find('h2', class_="history-date").text
    # Create a placeholder dataframe for concating with conditions dictionaries
    columns = ['Date','Time','Condition'] 
    hourly_conditions = pd.DataFrame([[1,1,1]],index=[0], columns=columns)
    # Continues scraping data until input date has been reached
    while date != earliest_date:
        try:
            current_url = driver.current_url
            weather_page = BeautifulSoup(driver.page_source, 'html.parser')
            date = weather_page.find('h2', class_="history-date").text
            cond_scrape = weather_page.find_all('tr', class_='no-metars')
            for i in range(len(cond_scrape)):
                temp_dict = {}
                row = cond_scrape[i]
                entry = row.findChildren('td')
                temp_dict['Date'] = dateutil.parser.parse(str(date)).date()
                temp_dict['Time'] = dateutil.parser.parse(str(entry[0].text)).time()
                temp_dict['Condition'] = str(entry[-1].text)
                hourly_conditions = hourly_conditions.append(temp_dict, ignore_index=True)
            previous_button = driver.find_element_by_link_text('« Previous Day')
            previous_button.click()
            time.sleep(3)
        except TimeoutException:
            logging.debug('Error pulling date on date: %s' % date)
            driver.close()
            driver = webdriver.Chrome('C:/Users/Paull/ds/metis/metisgh/chromedriver_win32/chromedriver')
            driver.get(current_url)
            time.sleep(3)
            previous_button = driver.find_element_by_link_text('« Previous Day')
            previous_button.click()
    driver.close()
    # Remove placeholder row
    hourly_conditions.drop(0,inplace=True)
    # Pickle dataframe for later use
    pickle.dump(hourly_conditions, open( zipcode + '_Conditions_' + date + ".p", "wb") ) 
    return hourly_conditions

# Functions for cleaning the data itself
def parse_date(x):
    """Takes a string date and converts it to a datetime object"""
    return dateutil.parser.parse(x).date()

def parse_time(x):
    """Takes a string date and converts it to a datetime time object"""
    return dateutil.parser.parse(x).time()

def fix_nan(string):
    """Takes string values that represesnt NaN and returns np.nan"""
    if string == 'NaN':
        return np.nan
    elif string == '':
        return np.nan
    elif string == '  -':
        return np.nan
    elif string == '-':
        return np.nan
    elif string == 'T':
        return 0.0001
    else:
        return string
    
def clean_weather_data(weather_data):
    """Takes a scraped weather_data dataframe and returns a cleaned dataframe"""
    #Clean Column Names
    weather_data.rename(columns=lambda x: x.replace(" ", "_"), inplace = True)
    weather_data.rename(columns=lambda x: x.replace("'", ""), inplace = True)
    weather_data.reset_index(inplace=True)
    weather_data = weather_data.drop('index',1);
    col_names = list(weather_data.columns)
    #Clean Strings
    weather_data['Average_Humidity'] = weather_data['Average_Humidity'].apply(lambda x: str(x))
    weather_data['Growing_Degree_Days'] = weather_data['Growing_Degree_Days'].apply(lambda x: str(x))
    for col in col_names:
        weather_data[col] = weather_data[col].apply(lambda x: str(x))
        weather_data[col] = weather_data[col].apply(lambda x: x.strip('\'').strip('b\''))
        weather_data[col] = weather_data[col].apply(lambda x: x.replace('in',''))
        weather_data[col] = weather_data[col].apply(lambda x: x.replace('(Base 50)',''))
        weather_data[col] = weather_data[col].apply(lambda x: x.replace('mph',''))
    temperature_cols = ['Max_Temperature','Min_Temperature','Mean_Temperature','Dew_Point']
    for col in temperature_cols:
        weather_data[col] = weather_data[col].apply(lambda x: x.replace('F',''))
    weather_data['Date'] = weather_data['Date'].apply(parse_date)
    weather_data['Sunrise'] = weather_data['Sunrise'].apply(parse_time)
    weather_data['Sunset'] = weather_data['Sunset'].apply(parse_time)
    weather_data['Wind_Dir'] = weather_data['Wind_Speed'].apply(lambda x: x.split())
    weather_data['Wind_Speed'] = weather_data['Wind_Dir'].apply(lambda x: x[0])
    weather_data['Wind_Dir'] = weather_data['Wind_Dir'].apply(lambda x: x[1])
    for col in col_names:
        weather_data[col] = weather_data[col].apply(fix_nan)
    for col in col_names:
        try: 
            weather_data[col] = weather_data[col].apply(lambda x: float(x))
        except:
            logging.debug('Could not convert to float for col in %s' % col)
    return weather_data

# Functions for assigning condition value to a date in weather data

def cond_to_value(cond):
    """assigns a numerical value to weather conditions"""
    if cond == 'Clear':
        return 1
    elif cond == 'Haze' or cond == 'Scattered Clouds':
        return 0.75
    elif cond == 'Partly Cloudy':
        return .5
    elif cond == 'Mostly Cloudy' or cond == 'Light Rain':
        return .25
    else:
        return 0.0
    
def to_datetime(time):
    """Takes a datetime.time object and converts it to a datetime object for calculations"""
    return datetime.combine(date.today(), time)

def fract_hour(time):
    """Takes a datetime.timedelta object and returns a fraction of hours ignoring any days"""
    return time.seconds/3600

def get_day_cond(weather_df, cond_df):
    """Takes a daily weather dataframe and an hourly conditions dataframe,
    assigns values to the days overall weather condition with a higher value
    meaning a longer period of direct sun exposure and returns the daily weather
    dataframe, now with an added Day_Cond column"""
    # Merge Hourly Conditions with Daily Weather to get Sunrise and Sunset Times
    solar_data = weather_df[['Date','Sunrise','Sunset']]
    df = pd.merge(cond_df, solar_data, on='Date', how='left')
    # Remove hourse before and after sunrise
    df = deepcopy(df.query('Time > Sunrise').query('Time < Sunset'))
    
    # Identify points where date switches
    df['Next_Date'] = df['Date'].shift(-1)
    df['Dates_Match'] = df['Date'] == df['Next_Date']
    
    # Add Next_Time column for identifying length of measurement period
    df['Time'] = df['Time'].apply(to_datetime)
    df['Next_Time'] = df['Time'].shift(-1)
    
    # Assign values to different conditions according to the function cond_to_value
    df['Cond_Val'] = df['Condition'].apply(cond_to_value)
    
    # Split dataframe into dates_match and dates_dont match, find length of measurement period
    # convert length of measurement period to a fraction of an hour and then multiply by condition value
    # Dates_Match:
    dates_match = deepcopy(df.query('Dates_Match'))
    dates_match['dtime'] = dates_match['Next_Time'] - dates_match['Time']
    dates_match['Fract_of_Hour'] = dates_match['dtime'].apply(fract_hour)
    dates_match['Cond_Val'] = dates_match['Cond_Val'] * dates_match['Fract_of_Hour']
    # Repeat for Dates_Dont_Match, but now from measurement time to sunset:
    dates_dont_match = deepcopy(df.query('Dates_Match == False'))
    dates_dont_match['Sunset'] = dates_dont_match['Sunset'].apply(to_datetime)
    dates_dont_match['dtime'] = dates_dont_match['Sunset'] - dates_dont_match['Time']
    dates_dont_match['Fract_of_Hour'] = dates_dont_match['dtime'].apply(fract_hour)
    dates_dont_match['Cond_Val'] = dates_dont_match['Cond_Val'] * dates_dont_match['Fract_of_Hour']
    
    # rejoin split dataframes now with condition values by measurement period
    dfs = [dates_match,dates_dont_match]
    comb_df = pd.concat(dfs, axis = 0)
    
    # sum condition values and total measurement period by day and divide total cond. val. by total time
    comb_df = comb_df.groupby('Date')['Cond_Val','Fract_of_Hour'].sum()
    comb_df['Day_Cond'] = comb_df['Cond_Val']/comb_df['Fract_of_Hour']
    
    # merge resulting data set's value for condition of day (Day_Cond) onto original weather dataframe
    comb_df.reset_index(inplace = True)
    comb_df = comb_df[['Date','Day_Cond']]
    result_df = pd.merge(weather_df, comb_df, on='Date', how='left')
    return result_df

def clean_moon_phase(moon_phase):
    pattern = re.compile(r'^\w+\s[0-9]+')
    moon_phase = re.sub(pattern, '', moon_phase)
    return moon_phase

# AQI Data pull function

def parse_date(x):
    """Takes a string date and converts it to a datetime object"""
    return dateutil.parser.parse(x)
def aqi_data(year):
    """Pulls relevant AQI data from provided year for zipcode 90012
    This function could be edited to also take in a zipcode and then
    return location specific data."""
    year_list = [year + x for x in range(2016-year)]
    aqi_master = pd.read_csv('aqi_csv/daily_44201_2016.csv')
    aqi_master.rename(columns=lambda x: x.replace(" ", "_"), inplace = True)
    aqi_master = aqi_master.query('State_Code == 6').query('County_Code == 37')
    for year in year_list: 
        aqi_temp = pd.read_csv('aqi_csv/daily_44201_%s.csv' % str(year))
        aqi_temp.rename(columns=lambda x: x.replace(" ", "_"), inplace = True)
        aqi_temp = aqi_temp.query('State_Code == 6').query('County_Code == 37')
        aqi_master = pd.concat([aqi_master,aqi_temp], axis = 0)
    aqi_90012 = aqi_master.query('Site_Num == 1103')[['Date_Local',
                       '1st_Max_Hour',
                       '1st_Max_Value',
                       'Arithmetic_Mean',
                       'Observation_Percent',
                       'AQI']]
    aqi_90012['Date'] = aqi_90012['Date_Local'].apply(parse_date)
    return aqi_90012

