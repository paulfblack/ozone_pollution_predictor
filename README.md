# Ground Level Ozone pollution prediction model  
This project looks at weather data from wunderground.com and attempts to predict ground level (or tropospheric) ozone pollution concentration. 
The model at present can account for 54% of variability in tropospheric ozone levels. All functions used are in the .py file and the commented out 
code at the start of the .ipynb will scrape wunderground data if run. The ipynb relies on pickle files currently only stored on my local computer, but 
the notebook accurately represents the linear regression modelling done in this project. This model uses ridge regression with L2 regularlization and 
cross fold validation. Primarliy, this was an exercise in experimenting with linear regression models. The original dataset used for this modelling totalled 
3118 entries which were combined with entries from the EPA's Air Quality Index data to map ozone pollution levels to key weather features.
