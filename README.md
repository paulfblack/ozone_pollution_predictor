# Ground Level Ozone Pollution Prediction
This project attempts to predict ground level ozone pollution in the L.A. area using linear regression modeling and weather related data. This was done as part of a 2 week introduction to linear regression modeling during my 12 week stint at Metis' data science bootcamp in Chicago. The goal of this project was to teach students to seek out and collect their own data from the web and to expose data science students to machine learning techniques. 
  
**Tools Used:** BS4, Selenium, SKLearn, StatsModels, MatPlotLib, Seaborn, Pandas.  

## Data Collection  
The Data for this project was collected from [Weather Underground](www.wunderground.org) and the [EPA](https://www.epa.gov/outdoor-air-quality-data/download-daily-data). All data centered around Los Angeles, California specifically looking at zip code [90012](https://www.google.com/maps/place/Los+Angeles,+CA+90012/@34.0659218,-118.2582039,14z/data=!3m1!4b1!4m5!3m4!1s0x80c2c6584fc8dfa1:0xce632757f29b6901!8m2!3d34.0653347!4d-118.243891) from January 1, 2005 to December 31, 2016.  
  
**Weather Data**  
Weather Data was scraped using BeautifulSoup and Selenium to pull data directly from Weather Underground. Features include time of sunset and sunrise, dew point, events (e.g. rain, snow, heavy wind), sea level pressure, temperature (daily min, max, and mean), humidity (daily min, max, and mean), degree days, wind (direction and speed), rain, snow, and lunar phase. Hourly features were also pulled to construct a more detailed understanding of the days total condition.

**Ozone pollution Data**
Ozone pollution data was collected from the EPA's Air Quality Index (AQI) report. Specifically, ground level ozone pollution concentration was pulled from the AQI report. While the goal of this project was to scrape data, this secondary source representing the target was opened up to allow for CSV formats. Data with incomplete observations were dropped in the final model fitting resulting in a total of 3118 entries.  
  
## Ground Level Ozone Pollution
  
Ground level ozone pollution occurs when ozone precursors, often produced during industrial processes, interact with UV radiation. High levels of ozone pollution have been linked to respiratory problems and, in severe cases, premature death. Developing a deeper understanding of how daily weather fluxuations contribute to ozone pollution can help high risk individuals take targeted preventative measures to protect their health. Because of the high level of industrialization and notoriously sunny climate, L.A. is a prime testing ground for exploring this relationship.

_sources:_ [www.epa.gov](https://www.epa.gov/ozone-pollution) and [wikipedia](https://en.wikipedia.org/wiki/Tropospheric_ozone#Health_effects)
  
## Feature Design  
  
The historical weather pages of Weather Underground do not list UV index data and for the scope of this project I wanted to limit myself to using the scraped data in my list of features. In order to create a proxy for sun exposure, I used hourly condition data during the time between sunrise and sunset for each day. In the end, this limited the predictive power of the model, but it was a wonderful introduction into feature engineering. For each hour, a numerical value ranging from 0 (full cloud cover) to 1 (full sun) was used to approximate how much direct sun exposure occurred during the day. This value was averaged over the total time between sunrise and sunset. Admittedly, this is a naive approach, particularly because the angle of the sun, the seasonal rotation of the Earth, and the ability of UV radiation to penetrate cloud cover were not included in this approach. For more information on this topic see my related [blog post](https://paulfblack.github.io/Feature-Design/).
  
## Linear Regression Model  
  
The Linear Regression model for this project comes from SKLearns [linear model](http://scikit-learn.org/stable/modules/linear_model.html) library. It was fit using ridge regression and scored with 10 fold cross validation. Features with P values of greater than .05 were removed from the data and for features with multiple measurements (e.g. humidity, wind, and temperature) only the feature shown to be most predictive was kept. This served to limit the effects of multicollinearity in a set of features that are intrinsically related. The final features used in the model were: average humidity, dew point, max wind gust speed, min. temperature, precipitation, sea level pressure, overall condition of day (UV proxy), and total length of daylight. In the end, this model accounted for 54% of variability in ground level ozone pollution. In part this lack of predictability is attributed to the naive nature of the UV radiation proxy feature design and the reliance on purely weather data. Incorporating traffic data and industrial processing is predicted to account for higher level of variation. 

## Repository Layout  
  
The functions used for this project can be found in the python file under the predictor functions folder. I have also included the final version of the Jupyter Notebook used in model analysis and scoring as well as the pdf of my presentation slides. 
