import sys
sys.path.append('..')
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import utils.model_utils as mod_utils
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from geopy.distance import great_circle
from pyproj import CRS, Transformer


ds = xr.open_dataset('./test_dyamond.nc')

def test_vert_interpolation():
    z = ds['z'].values
    z_new = np.array([35.,33])

    T_new = mod_utils.interp_vert(ds, 'T', z_new)

    lat = ds['lat']
    lon = ds['lon']

    mod_utils.plot_map_unstructured(lon, lat, ds['T'][1,:], fname='T_vert_orig.png')
    mod_utils.plot_map_unstructured(lon, lat, T_new[0,:], fname='T_vert_interp.png')
    # check output manually to verify these two plots look similar. One of the original levels is 35012 m,
    # interpolated to 35000 m. (they do look nearly identical)

def test_grid_gen():
    lats = ds['lat'].to_numpy()
    lons = ds['lon'].to_numpy()

    target_dx = 3000. # m

    lons_new, lats_new = mod_utils.create_grid(lons, lats, target_dx)

    ny, nx = np.shape(lons_new)

    # ensure new lats/lons are within range of initial
    max_lat = np.max(lats)
    min_lat = np.min(lats)
    max_lon = np.max(lons)
    min_lon = np.min(lons)
    for j in range(ny):
        for i in range(nx):
            lat_new = lats_new[j,i]
            lon_new = lons_new[j,i]
            assert max_lat - lat_new > 0
            assert lat_new - min_lat > 0
            assert max_lon - lon_new > 0
            assert lon_new - min_lon > 0
            
    
    # check dx's 
    x_ind = int(nx/2)
    y_ind = int(ny/2)
    dx = []
    dy = []
    for i in range(nx-1):
        for j in range(ny-1):
            dx.append(great_circle((lats_new[j,i],lons_new[j,i]), (lats_new[j,i+1],lons_new[j,i+1])).meters)
            dy.append(great_circle((lats_new[j,i],lons_new[j,i]), (lats_new[j+1,i],lons_new[j+1,i])).meters)

    # check that all dx, dy are within 20 m of the target dx (not always possible, but is possible for this test case)
    assert np.all(np.abs(np.array(dx) - target_dx) < 20)
    assert np.all(np.abs(np.array(dy) - target_dx) < 20)


if __name__ == "__main__":
    #test_vert_interpolation()
    test_grid_gen()

