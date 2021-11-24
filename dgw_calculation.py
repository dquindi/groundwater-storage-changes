from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
from functions import days2date, temporal_interpolation, inside_polygon


#=======================================================
#		                GLDAS
#=======================================================

# Load GLDAS netCDF file.
gldas = Dataset('./data/GLDAS.A200201_201607.nc4')

# Define variables of interest.
gldas_lat = gldas.variables['lat']  # lat[0] = -59.5, lat[149] = 89.5 [grades]
gldas_lon = gldas.variables['lon']  # lon[0] = -179.5, lon[359] = 179.5 [grades]
gldas_time = gldas.variables['time']  # time[0] = 306, time[174] = 5601 [days since 2001-03-01]
 
# Soil moisture in different layers ranging from 0-10 cm, 10-40 cm, 40-100 cm and 100-200 cm.
sm_0_10 = gldas.variables['SoilMoi0_10cm_inst'][ :, :, :]  # [kg/m**2]
sm_10_40 = gldas.variables['SoilMoi10_40cm_inst'][:, :, :]
sm_40_100 = gldas.variables['SoilMoi40_100cm_inst'][:, :, :]
sm_100_200 = gldas.variables['SoilMoi100_200cm_inst'][:, :, :]

# Canopy water storage (water in plants).
canopy = gldas.variables['CanopInt_inst'][:, :, :]  # [kg/m**2]

# Convert variables from kg/m**2 to cm, assuming water_density = 1000 kg/m**3.
sm_0_10_cm = sm_0_10*0.1 
sm_10_40_cm = sm_10_40*0.1
sm_40_100_cm = sm_40_100*0.1
sm_100_200_cm = sm_100_200*0.1

canopy_cm = canopy*0.1

# Add the components soil moisture and canopy to obtain ws_gldas (water storage GLDAS).
gldas_ws = canopy_cm + sm_0_10_cm  + sm_10_40_cm # + sm_40_100_cm + sm_100_200_cm

# Rearrange GLDAS data in order to be consistent with GRACE data.
gldas_ws1 = ma.array(gldas_ws[:, :, 0:180])
gldas_ws2 = ma.array(gldas_ws[:, :, 180:360])
gldas_ws = ma.concatenate((gldas_ws2, gldas_ws1), axis = 2)


#=======================================================
#						 GRACE
#=======================================================

# Load GRACE data. 
# CSR, JPL and GFZ are three different centers.

# Define variables of interest.
# The variables csr_data, jpl_data and gfz_data are land water storage 
# variations relative to a mean field calculated for the period 2004-2009.

csr = Dataset('./data/GRCTellus.CSR.200204_201607.LND.RL05.DSTvSCS1409.nc')
csr_lon = csr.variables['lon']  # csr_lon[0] = 0.5, csr_lon[359] = 359.5 [grades]
csr_lat = csr.variables['lat']  # csr_lat[0] = -89.5, csr_lat[179] = 89.5 [grades]
csr_time = csr.variables['time']  # csr_time[0] = 107.5, csr_time[154] = 5310 [days since 2002-01-01]
csr_data = csr.variables['lwe_thickness']  # csr_data is equivalent water thickness [cm]                                       

jpl = Dataset ('./data/GRCTellus.JPL.200204_201607.LND.RL05_1.DSTvSCS1411.nc')
jpl_lon = jpl.variables['lon']
jpl_lat = jpl.variables['lat']
jpl_time = jpl.variables['time']
jpl_data = jpl.variables['lwe_thickness']  # jpl_data is equivalent water thickness [cm] 

gfz = Dataset ('./data/GRCTellus.GFZ.200204_201607.LND.RL05.DSTvSCS1409.nc')
gfz_lon = gfz.variables['lon']
gfz_lat = gfz.variables['lat']
gfz_time = jpl.variables['time']
gfz_data = jpl.variables['lwe_thickness']  # gfz_data is equivalent water thickness [cm] 

factors = Dataset ('./data/CLM4.SCALE_FACTOR.DS.G300KM.RL05.DSTvSCS1409.nc')
factors_lon = factors.variables['Longitude'][:]
factors_lat = factors.variables['Latitude'][:]
factors_data = factors.variables['SCALE_FACTOR'] # Dimensionless coefficients

# Masks the array where equal to a FillValue.
factors_data = np.ma.masked_equal(factors_data, factors_data._FillValue) 

# Water storage variations from GRACE. 
# Calculate an average value of equivalent water thickness.
average_data = (csr_data[:, :, :] + jpl_data[:, :, :] + gfz_data[:, :, :]) / 3

grace_ws = ma.masked_all(average_data.shape)

for i in range (0, len(csr_time)):
	grace_ws[i] = np.multiply(average_data[i, :, :], factors_data[:, :])

# Rearrange ws_grace in order to be consistent with GLDAS data.	
grace_ws = ma.array(grace_ws[:, 30:180, :])


#=======================================================
#			     Interpolation in time
#=======================================================

# Interpolate GLDAS data in time so that the dates are the same as GRACE.

# List of date objects.
grace_dates = days2date(csr_time[:], source = 'grace')
gldas_dates = days2date(ma.getdata(gldas_time), source = 'gldas')

# Interpolation.
gldas_ws_interp = temporal_interpolation(grace_dates, gldas_dates, grace_ws, gldas_ws)


#=======================================================
#			     Conceptual model
#=======================================================

# Calculate ws_gldas anomalies (dws_gldas) as the difference between ws_gldas and its mean for the study period.
gldas_dws = gldas_ws_interp - np.ma.mean(gldas_ws_interp, axis = 0)

# Calculate ws_grace anomalies (dws_grace) as the difference between ws_grace and its mean for the study period.
# Now, the water storage variations are referred to the mean value of the study period.
grace_dws = grace_ws - np.ma.mean(grace_ws, axis = 0)

# Calculate groundwater storage variations.
dgw = grace_dws - gldas_dws

# Filter data inside the area of interest.
dgw = inside_polygon(csr_lon, gldas_lat, dgw)

# Groundwater storage variations inside the polygon for the study period.
time_mask = grace_ws.mask[:, 25, 302]
mixed_mask = np.logical_or(time_mask[:, None, None], dgw.mask[None, :, :])
dgw_filtered = np.ma.masked_array(np.ma.getdata(dgw), mask = mixed_mask)

# Export data.
np.savez('dgw', dgw_filtered_data = dgw_filtered.data, dgw_filtered_mask = dgw_filtered.mask, 
         time = csr_time, lon = csr_lon, lat = gldas_lat)
