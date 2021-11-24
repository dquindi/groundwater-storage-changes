import numpy as np
from datetime import date, timedelta
from scipy.interpolate import CubicSpline
import cartopy.io.shapereader as shpreader
from shapely.geometry import Point


def days2date(days, source):
    """
    Transform days (respect to a reference time) to dates with format 
    year-month-day.
    
    Arguments:
    days -- Masked array with days (respect to a reference date).
    source -- Source of the information, 'grace' or 'gldas'.
    
    Returns:
    dates -- List of date objects (datetime.date).
    """

    if source == 'grace':
        start_date = date(2002, 1, 1)
    else:
        start_date = date(2001, 3, 1)
        
    dates =[]  
    
    for i in range (0,len(days)):
        dates.append(start_date + timedelta(days[i]))

    return dates


def temporal_interpolation(grace_dates, gldas_dates, grace_data, gldas_data):
    """
    Interpolate GLDAS data in time to match GRACE data.
    
    Arguments:
    grace_dates -- GRACE list of date objects.
    gldas_dates -- GLDAS list of date objects.
    grace_data -- GRACE masked array to create final mask.
    gldas_data -- GLDAS masked array to be interpolated.
    
    Returns:
    gldas_data_interp -- GLDAS masked array interpolated.
    """
    
    grace_dates_array = np.asarray(grace_dates)
    gldas_dates_array = np.asarray(gldas_dates)
    
    x = []
    start_date = date(2001, 3, 1)    

    for i in range(0, len(grace_dates)):
	    ind = np.amax(np.where(gldas_dates_array <= grace_dates_array[i]))
	    days = grace_dates_array[i].day - gldas_dates_array[ind].day	    
	    x.append((gldas_dates_array[ind] - start_date).days + days)
        
    gldas_days = []
    
    for i in range(0, len(gldas_dates)):
        gldas_days.append((gldas_dates_array[i] - start_date).days)
		
    # Cubic spline data interpolator.
    f_interp = CubicSpline(gldas_days, gldas_data[:,:,:], axis = 0)
    # Use GRACE mask in time and GLDAS mask in space.
    # Mask in time takes information from coordinates lat[25], lon[302] where
    # there is data.
    time_mask = grace_data.mask[:, 25, 302]
    mixed_mask = np.logical_or(time_mask[:, None, None], 
                               gldas_data.mask[0, :, :][None, :, :])
    gldas_data_interp = np.ma.array(f_interp(x), mask = mixed_mask)
    
    return gldas_data_interp


def inside_polygon(lon, lat, data):
    """
    Filter data inside the polygon.
    
    Arguments:
    lon -- Masked array of longitudes.
    lat -- Masked array of latitudes.
    data -- Masked array to be filtered.
    
    Returns:
    filtered_data -- Filtered masked array.
    """
    
    lon_grid, lat_grid = np.meshgrid(lon, lat)

    # Read shapefile. The shapefile has information about the limits of the area
    # of interest.
    shp = shpreader.Reader('./shapefiles/loess_holes.shp')
    polygon = next(shp.geometries())

    # Redefine lon_grid because longitude in polygon takes values between -180 and 180.
    for i in range(0, lon_grid.shape[1]):
	    if lon_grid[0, i] > 180:
		    lon_grid[:, i] = lon_grid[:, i] - 360

    # Create list of lists with the points (lon and lat indexes) inside de polygon.
    ind = []
    for i in range(0, lon_grid.shape[0]):
	    for j in range (0, lon_grid.shape[1]):
		    if not ((polygon.bounds[0] - 1 <= lon_grid[i, j] and lon_grid[i, j] <= polygon.bounds[2] + 1) and 
				    (polygon.bounds[1] - 1 <= lat_grid[i, j] and lat_grid[i, j] <= polygon.bounds[3] + 1)):
			    continue

		    points = []
		    radio = 0.8
		    ntheta = 2**5
		    for theta in np.linspace(0, 2*np.pi, ntheta):
			    points.append(Point(lon_grid[i, j] + radio*np.cos(theta), lat_grid[i, j] + radio*np.sin(theta)))

		    for p in points:				
			    if polygon.contains(p):
				    ind.append([i, j])
				    continue
                
    # Generate mask with False inside the polygon and True outside of it.
    initial_mask = np.ma.getmaskarray(data)
    initial_mask[:, :, :] = True
    initial_mask[:, [x[0] for x in ind], [x[1] for x in ind]] = False 
    filtered_data = np.ma.masked_array(np.ma.getdata(data), mask = initial_mask)
    
    return filtered_data

	
def distance(lat0, lon0, lat1, lon1):
    """
    Calculate distance between two points on Earth, assuming they are close
    enough to considerate the Earth a flat surface.
    
    Arguments:
    lat0, lon0 -- Coordinates of point 0 in degrees.
    lat1, lon1 -- Coordinates of point 1 in degrees.
    
    Returns:
    dist -- Distance between points 0 and 1 in kilometers.
    """
    
    scalar = 2*np.pi*6371/360
    
    dif_lat = lat0 - lat1
    dif_lon = lon0 - lon1
    
    dist = np.sqrt((dif_lat*scalar)**2 + (dif_lon*scalar)**2)
    
    return dist
