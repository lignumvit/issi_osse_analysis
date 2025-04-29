import xarray as xr
import numpy as np
from numpy.typing import ArrayLike
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from geopy.distance import great_circle
from pyproj import CRS, Transformer

def interp_vert(ds: xr.Dataset, var_name: str, new_levels: ArrayLike):
    """
    Interpolates a 2D variable (z, x) onto new vertical levels.

    Parameters:
    - ds: xarray.Dataset containing the variable and 'z' dimension
    - var_name: str, name of the variable to interpolate ('T' or 'Tp')
    - new_levels: array-like, new vertical levels to interpolate to

    Returns:
    - xarray.DataArray: interpolated variable with dimensions (new_z, x)
    """
    if var_name not in ds:
        raise ValueError(f"Variable '{var_name}' not found in dataset.")

    # Ensure levels are in numpy array form
    new_levels = np.asarray(new_levels)

    # Interpolation using xarray's `interp` with coordinate indexing
    interpolated = ds[var_name].interp(z=new_levels)

    # Rename the interpolated dimension for clarity
    interpolated = interpolated.rename({'z': 'new_z'})
    interpolated.coords['new_z'] = new_levels

    return interpolated

def plot_map_unstructured(lon, lat, var, fname='out.png'):
    plt.figure(figsize=(14, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())
    sc = ax.scatter(lon, lat, c=var, cmap='coolwarm', s=1, transform=ccrs.PlateCarree())
    plt.colorbar(sc, ax=ax, label='Temperature (K)', orientation='vertical')

    # Add political boundaries and other features
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAND, edgecolor='black', facecolor='none')

    # Add gridlines and labels
    gl = ax.gridlines(draw_labels=True)
    gl.top_labels = False
    gl.right_labels = False

    # Final touches
    ax.set_title('Temperature at Level 35.0 with Political Boundaries')
    plt.tight_layout()

    # Save the plot to a file
    plt.savefig(fname, dpi=300)
    print(f"Plot saved to {fname}")


def create_grid(lon, lat, target_dx):
    # how big a domain are we workin with?
    min_lat = min(lat)
    max_lat = max(lat)
    min_lon = min(lon)
    max_lon = max(lon)
    yspan = great_circle((max_lat,min_lon), (min_lat,min_lon)).kilometers
    xspan_north = great_circle((max_lat,min_lon), (max_lat,max_lon)).kilometers
    xspan_south = great_circle((min_lat,min_lon), (min_lat,max_lon)).kilometers
    #print(f"North-South: {yspan:.1f} km") # 2223.9 km
    #print(f"Northern East-West: {xspan_north:.1f} km") # 1129.4 km
    #print(f"Southern East-West: {xspan_south:.1f} km") # 2129.7 km

    # compute standard parallels
    lat_span = max_lat-min_lat
    lat_spacing = lat_span/3.
    standard_lat1 = min_lat + lat_spacing
    standard_lat2 = min_lat + 2*lat_spacing
    # grab mid-points of the box
    mid_lat = 0.5*(min_lat + max_lat)
    mid_lon = 0.5*(min_lon + max_lon) # CAUTION: Only works if the date line isn't crossed!!!

    target_dx = 3000. # m
    y_span = 2000000. # m, 2000 km north south
    x_span = 2000000. # m, 2000 km north south

    # Define the LCC projection
    crs_lcc = CRS.from_proj4(f"+proj=lcc +lat_1={standard_lat1} +lat_2={standard_lat2} +lat_0={mid_lat} +lon_0={mid_lon} +datum=WGS84")
    crs_geo = CRS.from_epsg(4326)  # WGS84 lat/lon

    transformer_lcc_to_geo = Transformer.from_crs(crs_lcc, crs_geo, always_xy=True)
    transformer_geo_to_lcc = Transformer.from_crs(crs_geo, crs_lcc, always_xy=True)

    x_ur, y_ur = transformer_geo_to_lcc.transform(max_lon, max_lat)
    x_ul, y_ul = transformer_geo_to_lcc.transform(min_lon, max_lat)
    x_lr, y_lr = transformer_geo_to_lcc.transform(max_lon, min_lat)
    x_ll, y_ll = transformer_geo_to_lcc.transform(min_lon, min_lat)
    #print(f"UR LCC: {x_ur/1000:7.1f} {y_ur/1000:7.1f}")
    #print(f"UL LCC: {x_ul/1000:7.1f} {y_ul/1000:7.1f}")
    #print(f"LR LCC: {x_lr/1000:7.1f} {y_lr/1000:7.1f}")
    #print(f"LL LCC: {x_ll/1000:7.1f} {y_ll/1000:7.1f}")

    # How many points/how big will the new grid be? 
    # Going for a square in the lcc projection entirely within the existing data.
    half_width = np.min(np.abs([x_ur, x_ul, x_lr, x_ll, y_ur, y_ul, y_lr, y_ll]))
    nx_new_half = int(half_width/target_dx) # truncating off the decimal points
    nx_new = nx_new_half*2
    xspan_new = int(nx_new*target_dx)
    #print(f"New grid will be {xspan_new/1000:.0f} km by {xspan_new/1000:.0f} km")

    # Define a grid of x, y coordinates in the LCC projection
    xspan_new_half = int(nx_new_half*target_dx)
    x = np.linspace(-xspan_new_half, xspan_new_half, nx_new+1)
    y = np.linspace(-xspan_new_half, xspan_new_half, nx_new+1)
    X, Y = np.meshgrid(x, y)


    # Transform x/y → lon/lat
    #lons_new, lats_new = transformer_lcc_to_geo.transform(X, Y)
    lonlat_new = transformer_lcc_to_geo.transform(X, Y)
    lon_new = lonlat_new[0]
    lat_new = lonlat_new[1]

    return lon_new, lat_new

