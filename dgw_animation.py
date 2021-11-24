import numpy as np
import matplotlib.pyplot as plt
import cartopy.io.shapereader as shpreader
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature
from matplotlib import ticker
import matplotlib.animation as animation
from functions import days2date
import numpy.ma as ma


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

lon = npzfile['lon']
lat = npzfile['lat']

dgw_min = np.amin(dgw)
dgw_max = np.amax(dgw)

date_format = "%d-%m-%Y"


#==============================================================
#                       Animation
#==============================================================

# Create animation.

# Shapefile with the provinces of Argentina.
shp_provinces = shpreader.Reader('./shapefiles/provinces.shp')

# Shapefile with the limits of the area of interest.
shp_polygon = shpreader.Reader('./shapefiles/loess_holes.shp')


# Create the figure object (fig), axis object (ax) and plot object (plot).
fig = plt.figure(figsize = (5, 7), constrained_layout=True)
ax = plt.axes(projection=ccrs.PlateCarree())
plot = ax.contourf(dgw[0, :, :], 
                   transform = ccrs.PlateCarree(), 
                   cmap = 'rainbow_r', 
                   extent = [lon[0] - 360, lon[-1] - 360, lat[0], lat[-1]], 
                   levels = np.linspace(-50, 50, 7), extend = 'both')

# Add features to the map.
prov_feature = ShapelyFeature(shp_provinces.geometries(), ccrs.PlateCarree())

polygon_feature = ShapelyFeature(shp_polygon.geometries(), ccrs.PlateCarree())

holes_feature = ShapelyFeature(next(shp_polygon.geometries()).interiors, 
                               ccrs.PlateCarree())

prov_plot = ax.add_feature(prov_feature, linewidth = 0.6, edgecolor = 'black', 
                           facecolor = 'none')

polygon_plot = ax.add_feature(polygon_feature, linewidth = 2, 
                              edgecolor = '#f0e615', facecolor = 'none', 
                              zorder = 15)

holes_plot = ax.add_feature(holes_feature, linewidth = 2, edgecolor = '#f0e615', 
                            facecolor = 'w', zorder = 30)

# Add title.
title = ax.text(.35, 1.1, dates[0].strftime(date_format), transform = ax.transAxes)
title.set_fontsize(10)

# Add colorbar.
cb = plt.colorbar(plot, shrink = 0.5, orientation = 'horizontal', pad = 0.075)
cb.set_label('Groundwater variations in equivalent water thickness [cm]', color = 'black', size = 9)
cb.ax.tick_params(labelsize = 8, rotation = 30)

# Add grid.
gl = ax.gridlines(draw_labels = True, alpha = 0.25)
gl.xlabel_style = {'size': 8}
gl.ylabel_style = {'size': 8}
gl.bottom_labels_ = False
gl.right_labels = False
gl.xlocator = ticker.LinearLocator(numticks = 4)

ax.set_xlim(111-180, 124.5-180)
ax.set_ylim(-40, -21)

# Animation function. 
def animate(i): 
    plot = ax.contourf(dgw[i, :, :], 
                       transform = ccrs.PlateCarree(), 
                       cmap = 'rainbow_r', 
                       extent = [lon[0] - 360, lon[-1] - 360, lat[0], lat[-1]], 
                       levels = np.linspace(dgw_min, dgw_max, 7))
    title.set_text(dates[i].strftime(date_format))
    return plot, prov_plot, polygon_plot, title

# Call the animation function.
anim = animation.FuncAnimation(fig, animate, frames = np.arange(0, 155), interval = 250, blit = False)

# Save the animation as a .gif file.
writergif = animation.PillowWriter(fps = 4) 
anim.save('dgw_animation.gif', writer = writergif)

# Save the animation in .mp4 format.
writervideo = animation.FFMpegWriter(fps = 4) 
anim.save('dgw_animation.mp4', writer = writervideo)
