import numpy as np
import numpy.ma as ma
from functions import days2date, distance
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


#=======================================================
#               Groundwater variations
#=======================================================

# Load the output from gw_calculation.py.
npzfile = np.load('dgw.npz')

dgw_data = npzfile['dgw_filtered_data']
dgw_mask = npzfile['dgw_filtered_mask']
dgw = ma.masked_array(dgw_data, mask = dgw_mask)

time = npzfile['time']
dates = days2date(time, source = 'grace')

lat = npzfile['lat']
lon = npzfile['lon']


#=======================================================
#       Groundwater variations at a given point
#=======================================================

# This section performs spatial interpolation in order to obtain groundwater 
# variations at a specific place.

lat_point = np.asarray(input('Enter a latitude in grades ranging from -90 to 90:'),
                       dtype = np.float32)
lon_point = np.asarray(input('Enter a longitude in grades ranging from 0 to 360:'),
                       dtype = np.float32)

# Test point.
# lat_point = -34.9
# lon_point = 302.06

# Find the cell where the point is located.
for i in lat:
	if (i <= lat_point <= (i+1)):
		lat_extremes = [i, i+1]
		
for i in lon:
	if (i <= lon_point <= (i+1)):
		lon_extremes = [i, i+1]

lat_inds = np.where((lat >= lat_extremes[0]) & (lat <= lat_extremes[1]))
lon_inds = np.where((lon >= lon_extremes[0]) & (lon <= lon_extremes[1]))

lat_ind_min = np.amin(lat_inds)
lat_ind_max = np.amax(lat_inds)	 
lon_ind_min = np.amin(lon_inds)  
lon_ind_max = np.amax(lon_inds)     

# Check if there is data at the chosen point.
data_nw = dgw[:, lat_ind_max, lon_ind_min] # North-West node
data_sw = dgw[:, lat_ind_min, lon_ind_min] # South-West node
data_ne = dgw[:, lat_ind_max, lon_ind_max] # North-East node
data_se = dgw[:, lat_ind_min, lon_ind_max] # South-East node

data = [data_nw, data_sw, data_ne, data_se]

for d in data:
    if d.mask.all() == True:
        raise Exception('There is no data at the chosen point.')

# Inverse distance weighting.
dist_nw = distance(lat_point, lon_point, lat[lat_ind_max], lon[lon_ind_min])
dist_sw = distance(lat_point, lon_point, lat[lat_ind_min], lon[lon_ind_min])
dist_ne = distance(lat_point, lon_point, lat[lat_ind_max], lon[lon_ind_max])
dist_se = distance(lat_point, lon_point, lat[lat_ind_min], lon[lon_ind_max])

numerator, denominator = (0, 0)
for data, dist in zip([data_nw, data_sw, data_ne, data_se], [dist_nw, dist_sw, dist_ne, dist_se]):
    if np.all(data.mask == True):  
        continue
    else:
        numerator = numerator + data/dist
        denominator = denominator + 1/dist

# Groundwater storage variations.
dgw_point = numerator/denominator 

# Understanding the central tendency.
dgw_point_mean = np.mean(dgw_point) # Mean
dgw_point_median = np.median(dgw_point) # Median


#=======================================================
#                   Linear Regression
#=======================================================

# This section calculates Ordinary least squares Linear Regression.
# Used as a way to find a general trend in data.

n_samples = len(dgw_point)
n_features = 1

x = [] 
for i in range(n_samples):
    x.append(dates[i].toordinal()) # Returns the day count from the date 01/01/01
    
x = np.asarray(x).reshape(-1, n_features) 
# LinearRegression needs x (array) of shape (n_samples, n_features). It can't 
# handle datetime.date on the x-axis.

y = dgw_point
# LinearRegression needs y (array) of shape (n_samples,). 

model = LinearRegression()
model.fit(x, y)

y_line = model.predict(x) 

# y_line = ax + b.
a = model.coef_ # [cm/day]
b = model.intercept_ # [cm]

# Slope: variations in cm per year.
a_year = a*365 # [cm/year]


#=======================================================
#                        Plots
#=======================================================

# Plot 1: Histogram of groundwater variations.
plt.figure(1)
plt.hist(dgw_point, bins = 'sqrt', density = True, ec = 'grey',
         fc = 'lightgrey')
plt.axvline(x = dgw_point_mean, color = '#ff7f0e', linestyle = '--', 
            label = 'Mean = {:.2f}'.format(dgw_point_mean))
plt.axvline(x = dgw_point_median, color = '#1f77b4', linestyle = '--', 
            label = 'Median = {:.2f}'.format(dgw_point_median))
plt.xlabel('Groundwater variations in equivalent water thickness [cm]')
plt.ylabel('Probability')
plt.title('Histogram of groundwater variations. \n Lat = {:.2f}°, Lon = {:.2f}°.'.format(lat_point, lon_point))
plt.legend()

plt.savefig('histogram_point.png', bbox_inches = 'tight')

# Plot 2: Dates vs. Groundwater variations.
plt.figure(2, figsize = (10, 5))
plt.plot(dates, dgw_point, '--o')
plt.plot(dates, y_line, label = 'Regression line')
plt.text(dates[0], 2.5, '{:.2f} cm/year'.format(a_year[0]), fontsize = 7,
         bbox = dict(edgecolor = '#ff7f0e', facecolor = '#ff7f0e', alpha = 0.6))
plt.xlabel('Dates [Year]')
plt.ylabel('Groundwater variations in equivalent water thickness [cm]')
plt.title('Groundwater variations \n Lat = {:.2f}°, Lon = {:.2f}°'.format(lat_point, lon_point))
plt.legend()

plt.savefig('dgw_point.png', bbox_inches = 'tight')
