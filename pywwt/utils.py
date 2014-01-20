import numpy as np
import csv
import matplotlib.cm as mcm
from matplotlib.colors import LogNorm, Normalize
import struct
from astropy.utils.console import ProgressBar
from datetime import datetime, timedelta
from dateutil import tz, parser

def map_array_to_colors(arr, cmap, scale="linear",
                        vmin=None, vmax=None):
    r"""
    Map a NumPy array to a colormap using Matplotlib.

    Parameters
    ----------
    arr : NumPy array of floats or ints
        The array to be mapped onto a colormap.
    cmap : string
        The name of a Matplotlib colormap.
    scale : string, optional
        The scaling of the data as mapped to the
        colormap. Takes "linear" or "log", default "linear".
    vmin : float or int
        The value associated with the lowest end of the colormap.
        Defaults to the minimum value of *arr*.
    vmax : float or int
        The value associated with the highest end of the colormap.
        Defaults to the maximum value of *arr*.

    Returns
    -------
    A list of colors, encoded in ARGB hex values.
    """
    if vmin is None:
        vmin = arr.min()
    if vmax is None:
        vmax = arr.max()

    if scale == "linear":
        norm = Normalize(vmin=vmin, vmax=vmax)
    elif scale == "log":
        norm = LogNorm(vmin=vmin, vmax=vmax)

    my_cmap = mcm.ScalarMappable(norm=norm, cmap=cmap)
    colors = my_cmap.to_rgba(arr, bytes=True)

    colors = ["FF"+struct.pack('BBB',*color[:3]).encode('hex').upper()
              for color in colors]

    return colors

def generate_utc_times(num_steps, step_size, start_time=None):
    r"""
    Generate a series of equally linearly spaced times in UTC.

    Parameters
    ----------
    num_steps : int
        The number of times to generate.
    step_size : dict
        A dictionary corresponding to the step size between
        the times, with keys referring to the unit (seconds,
        minutes, days, etc.) and the values of the step in that unit.
    start_time : string, optional
        A string corresponding to a time in the local time zone
        at which to start the timesteps. Defaults to the current
        system time.
        Formats (month/day/year):
        "1/1/2010 11:00:00 PM"
        "1/1/2010 11:30 AM"
        "1/1/2010 11 am"
        "1/1/2000"
        "1/2000"

    Returns
    -------
    A list of formatted date/time strings in UTC readable by
    World Wide Telescope.
    """
    if start_time is None:
        start_time = datetime.utcnow()
    else:
        start_time = parser.parse(start_time)
        utc_zone = tz.tzutc()
        local_zone = tz.tzlocal()
        # Tell the datetime object that it's in local time zone since
        # datetime objects are 'naive' by default
        local_time = start_time.replace(tzinfo=local_zone)
        # Convert time to UTC
        start_time = local_time.astimezone(utc_zone)

    time_arr = []
    new_time = start_time
    for i in xrange(num_steps):
        time_arr.append(new_time.strftime("%m/%d/%Y %I:%M:%S %p"))
        new_time += timedelta(**step_size)

    return time_arr

def convert_xyz_to_spherical(x, y, z, is_astro=True, ra_units="degrees"):
    r"""
    Convert rectangular coordinates (x,y,z) to spherical coordinates
    (Lat, Lon, Alt) or (RA, Dec, Alt).

    Parameters
    ----------
    x : NumPy array of floats
        The x-coordinates of the data.
    y : NumPy array of floats
        The y-coordinates of the data.
    z : NumPy array of floats
        The z-coordinates of the data.
    is_astro : boolean, optional
        Is the coordinate system astronomical (RA, Dec)
        or geographical (Lat, Lon)? Defaults to True.
    ra_units : string, optional
        The unit of the RA/Lon coordinate, "degrees" or
        "hours". Defaults to "degrees".

    Returns
    -------
    A dict of NumPy arrays corresponding to the positions in
    spherical coordinates.
    """
    if ra_units == "degrees" or not is_astro:
        ra_scale = 1.
    elif ra_units == "hours":
        ra_scale = 24./360.
    if is_astro:
        ra_name = "RA"
        dec_name = "DEC"
    else:
        ra_name = "LON"
        dec_name = "LAT"
    coords = {}
    coords["ALT"] = np.sqrt(x*x+y*y+z*z)
    coords[ra_name] = (np.rad2deg(np.arctan2(y, x)) + 180.)*ra_scale
    coords[dec_name] = np.rad2deg(np.arccos(z/coords["ALT"])) - 90.
    return coords

def write_data_to_csv(data, filename, mode="new"):
    r"""
    Write a dataset to a CSV-formatted file with a data header.

    Parameters
    ----------
    data : dictionary of NumPy arrays
        The data to be written.
    filename : string
        The filename to write the data to.
    mode : string, optional
        Write a "new" file or "append" to an existing file?
        Default "new".
    """
    if mode == "new":
        fmode = "wb"
    elif mode == "append":
        fmode = "a+b"
    f = open(filename, fmode)
    w = csv.DictWriter(f, data.keys())
    if mode == "new": w.writeheader()
    num_points = len(data.values()[0])
    for i in ProgressBar(xrange(num_points)):
        row = dict([(k,v[i]) for k,v in data.items()])
        w.writerow(row)
    f.close()




