import numpy as np
import numpy.ma as ma
from functions import days2date
import matplotlib.pyplot as plt
from cartopy.feature import ShapelyFeature
import cartopy.io.shapereader as shpreader
import cartopy.crs as ccrs


#=======================================================
#               Groundwater variations
#=======================================================

# Load the output from dgw_calculation.py.
npzfile = np.load('dgw.npz')

dgw_data = npzfile['dgw_filtered_data']
dgw_mask = npzfile['dgw_filtered_mask']
dgw = ma.masked_array(dgw_data, mask = dgw_mask)

time = npzfile['time']
dates = days2date(time, source = 'grace')

lat = npzfile['lat']
lon = npzfile['lon']


#===================================================
#              Monthly mean variations
#===================================================

# Calculate monthly mean variations.

# List of months.
n = np.asarray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

# Group the maps by month.
ind_month = [[] for i in range(len(n))]
for i in range(len(n)):
    for j in range(len(dates)):
        if dates[j].month == n[i]:
            ind_month[i].append(j)

# Take all the January maps for the period 2002-2016 and average them. 
# The same with the other months.
monthly_map = np.zeros(shape = (len(n), 150, 360))
monthly_map = np.ma.masked_array(monthly_map, mask = True)

for i in range(len(n)):
    monthly_map[i, :, :] = (np.ma.mean(dgw[ind_month[i], :, :], axis = 0))

# Variations relative to the monthly mean maps.
# Useful for creating annual mean maps (annual_mean.py).
dev = np.zeros(shape = (len(dates), 150, 360))
dev = np.ma.masked_array(dev, mask = True)
for i in range(len(n)):
    for j in range(len(dates)):
        if dates[j].month == n[i]:
            dev[j] = dgw[j, :, :] - monthly_map[i]

# Export data. Useful in annual_mean.py.
np.savez('dev', dev_data = dev.data, dev_mask = dev.mask)


#===================================================
#                  Extreme cases
#===================================================

# Month with maximum positive deviation.    
dev_max = np.amax(dev[:, :, :])
dev_max_ind = np.argwhere(dev == dev_max)
print('Maximum positive deviation in cm of EWT:', dev_max)
print('Month - year when maximum positive deviation happened:',
      dates[dev_max_ind[0][0]].month, '-', dates[dev_max_ind[0][0]].year)

# Month with maximum negative deviation.
dev_min = np.amin(dev[:, :, :])
dev_min_ind = np.argwhere(dev == dev_min)
print('Maximum negative deviation in cm of EWT:', dev_min)
print('Month - year when maximum negative deviation happened:',
      dates[dev_min_ind[0][0]].month, '-', dates[dev_min_ind[0][0]].year)

    
#==================================================
#                Monthly mean maps
#==================================================

# Create maps.

# Shapefile with the provinces of Argentina.
shp_provinces = shpreader.Reader('./shapefiles/provinces.shp')

# Shapefile with the limits of the area of interest.
shp_polygon = shpreader.Reader('./shapefiles/loess_holes.shp')

# titles = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto',
#           'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

titles = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
         'September', 'October', 'November', 'December']

fig = plt.figure(figsize = (11, 7))

# Maps from January to June -> i from 0 to 6. 
# Maps from July to December -> i from 6 to 12.
for i in range(6, 12):
    # ax = plt.subplot(2, 3, i + 1, projection = ccrs.PlateCarree())
    ax = plt.subplot(2, 3, (i + 1) - 6, projection = ccrs.PlateCarree())
    plot = ax.contourf(monthly_map[i,:,:], 
                       transform = ccrs.PlateCarree(), cmap = 'rainbow_r', 
                       extent = [lon[0] - 360, lon[-1] - 360, lat[0], lat[-1]], 
                       levels = np.linspace(-15, 15, 7))
    
    prov_feature = ShapelyFeature(shp_provinces.geometries(), 
                                  ccrs.PlateCarree())
    prov_plot = ax.add_feature(prov_feature, linewidth = 0.6,
                               edgecolor = 'black', facecolor = 'none')
    
    polygon_feature = ShapelyFeature(shp_polygon.geometries(), 
                                     ccrs.PlateCarree())
    polygon_plot = ax.add_feature(polygon_feature, linewidth = 2, 
                                  edgecolor = '#f0e615', facecolor = 'none', 
                                  zorder = 15) 
    
    holes_feature = ShapelyFeature(next(shp_polygon.geometries()).interiors, 
                                   ccrs.PlateCarree())    
    holes_plot = ax.add_feature(holes_feature, linewidth = 2, 
                                  edgecolor = '#f0e615', facecolor = 'w', 
                                  zorder = 30)
      
    gl = ax.gridlines(draw_labels = True, alpha = 0.25)
    gl.top_labels = False
    gl.right_labels = False
    
    plt.title(titles[i], size = 21)

fig.subplots_adjust(left = 0.075, bottom = None, right = None, top = None, 
                    wspace = -0.3, hspace = 0.3)

cax = fig.add_axes([0.03, 0.33, 0.014, 0.28])
cb = plt.colorbar(plot, cax = cax, orientation = "vertical")
cb.set_label('EWT [cm]', color = "black", size = 14)
cb.ax.tick_params(labelsize = 14)

# Save plot as a .png image.
# plt.savefig('monthly_mean_jan2jun.png', bbox_inches = 'tight')
plt.savefig('monthly_mean_jul2dec.png', bbox_inches = 'tight')