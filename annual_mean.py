import numpy as np
import numpy.ma as ma
from functions import days2date
from dateutil.relativedelta import relativedelta
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
#        Deviations from monthly mean maps
#===================================================

# Load the output from monthly_mean.py.
npzfile = np.load('dev.npz')

dev_data = npzfile['dev_data']
dev_mask = npzfile['dev_mask']
dev = ma.masked_array(dev_data, mask = dev_mask)


#===================================================
#              Year-on-year variations
#===================================================

# Calculate annual mean variations.

# List of years.
m = np.asarray([2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 
                2012, 2013, 2014, 2015, 2016])

# Group the maps by year.
# Shift the data in time in order to obtain years with July as first month.
ind_year = [[] for i in range(len(m))]
for i in range (len(m)):
    for j in range(len(dates)):
        if (dates[j] + relativedelta(months = 6)).year == m[i]:
            ind_year[i].append(j)

# Average the groundwater variations for all periods July-June in 2002-2016.
annual_map = np.zeros(shape = (len(m), 150, 360))
annual_map = np.ma.masked_array(annual_map, mask = True)
for i in range(len(m)):
    annual_map[i] = np.ma.mean(dev[ind_year[i], :, :], axis = 0)


#===================================================    
#                Year-on-year maps
#===================================================

# Create maps.

# Shapefile with the provinces of Argentina.
shp_provinces = shpreader.Reader('./shapefiles/provinces.shp')

# Shapefile with the limits of the area of interest.
shp_polygon = shpreader.Reader('./shapefiles/loess_holes.shp')

titles = ['Jul 2002 - Jun 2003', 'Jul 2003 - Jun 2004',
          'Jul 2004 - Jun 2005', 'Jul 2005 - Jun 2006',
          'Jul 2006 - Jun 2007', 'Jul 2007 - Jun 2008', 
          'Jul 2008 - Jun 2009', 'Jul 2009 - Jun 2010', 
          'Jul 2010 - Jun 2011', 'Jul 2011 - Jun 2012', 
          'Jul 2012 - Jun 2013', 'Jul 2013 - Jun 2014',
          'Jul 2014 - Jun 2015', 'Jul 2015 - Jun 2016']

fig = plt.figure(figsize = (13, 7))

# Maps from 2002 to 2010 -> i from 0 to 8.
# Maps from 2010 to 2016 -> i from 8 to 14.
for i in range(8, 14):
    # ax = plt.subplot(2, 4, i + 1, projection = ccrs.PlateCarree())
    ax = plt.subplot(2, 4, (i + 1) - 8, projection = ccrs.PlateCarree())
    plot = ax.contourf(annual_map[i, :, :], 
                       transform = ccrs.PlateCarree(), cmap = 'rainbow_r', 
                       extent = [lon[0] - 360, lon[-1] - 360, lat[0], lat[-1]], 
                       levels = np.linspace(-30, 30, 7), extend = 'both')
    
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
    
    plt.title(titles[i], size = 15)

fig.subplots_adjust(left = 0.125, bottom = None, right = None, top = None, 
                    wspace = 0.1, hspace = 0.3)

cax = fig.add_axes([0.03, 0.33, 0.014, 0.28])
cb = plt.colorbar(plot, cax = cax, orientation = "vertical")
cb.set_label('EWT [cm]', color = "black", size = 14)
cb.ax.tick_params(labelsize = 14)

# Save plot as a .png image.
# plt.savefig('annual_mean_2002to2010.png', bbox_inches = 'tight')
plt.savefig('annual_mean_2010to2016.png', bbox_inches = 'tight')