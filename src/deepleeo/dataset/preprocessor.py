import numpy as np
import gdal
import sys
import tensorflow as tf
from os import path

sys.path.insert(0, path.join(path.dirname(__file__),"../"))
import utils.geofunctions as gf

# ----------------------------------------------------------------- #
# Predefined Indexes
# ----------------------------------------------------------------- #
def compute_NDVI(np_raster, parameters):
    # print("Computing NDVI")
    red = np_raster[:,:,parameters["idx_b_red"]]
    nir = np_raster[:,:,parameters["idx_b_nir"]]
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = np.true_divide(np.subtract(nir, red), np.add(nir, red))

    return ndvi

def compute_EVI(np_raster, parameters):
    # print("Computing EVI")
    if ("factor" in parameters):
        factor = parameters["factor"]
    else:
        factor = 1
    red = np_raster[:,:,parameters["idx_b_red"]] * factor
    nir = np_raster[:,:,parameters["idx_b_nir"]] * factor
    blue = np_raster[:,:,parameters["idx_b_blue"]] * factor

    with np.errstate(divide='ignore', invalid='ignore'):
        divider = nir - red
        dividend = nir + (6.0 * red) - (7.5 * blue) + 10000.0
        evi = 2.5 * (np.true_divide(divider, dividend))

    return evi

def compute_EVI2(np_raster, parameters):
    # print("Computing EVI2")
    red = np_raster[:,:,parameters["idx_b_red"]] * 0.0001
    nir = np_raster[:,:,parameters["idx_b_nir"]] * 0.0001

    with np.errstate(divide='ignore', invalid='ignore'):
        divider = np.subtract(nir, red)
        dividend = nir + (2.4 * red) + 10000.0
        evi2 = 2.5 * np.true_divide(divider, dividend)

    return evi2

# ----------------------------------------------------------------- #
# Predefined Standardization Functions
# ----------------------------------------------------------------- #

def standardize_median_std(raster_array):
    nbands = raster_array.shape[2]
    norm_raster_array = None
    for band in range(nbands):
        band_norm = raster_array[:, :, band]
        median = np.median(band_norm)
        stddev = np.std(band_norm)
        band_norm = (band_norm - median) / stddev
        if (norm_raster_array is None):
            norm_raster_array = band_norm
        else:
            norm_raster_array = np.ma.dstack((norm_raster_array, band_norm))

    return np.array(norm_raster_array, dtype=np.float32)


def standardize_mean_std(raster_array):
    nbands = raster_array.shape[2]
    norm_raster_array = None
    for band in range(nbands):
        band_norm = raster_array[:, :, band]
        mean = np.mean(band_norm)
        stddev = np.std(band_norm)
        band_norm = (band_norm - mean) / stddev
        if (norm_raster_array is None):
            norm_raster_array = band_norm
        else:
            norm_raster_array = np.ma.dstack((norm_raster_array, band_norm))

    return np.array(norm_raster_array, dtype=np.float32)


def standardize_tf(raster_array):
    img = tf.placeholder(shape=raster_array.shape, dtype=tf.float32)
    tf_img = tf.image.per_image_standardization(img)
    with tf.Session() as sess:
        stand_img = sess.run(tf_img, feed_dict={img: raster_array})
        return np.array(stand_img, dtype=np.float32)

# ----------------------------------------------------------------- #
# Preprocessor class
# ----------------------------------------------------------------- #

class Preprocessor(object):
    predefIndexes = {
        "ndvi": compute_NDVI,
        "evi": compute_EVI,
        "evi2": compute_EVI2
    }

    standardize_functions = {
        "mean_std": standardize_mean_std,
        "median_std": standardize_median_std,
        "tensorflow": standardize_tf
    }

    sint_bands = {}

    def __init__(self, raster_path, vector_path, no_data=0):
        self.raster_path = raster_path
        self.vector_path = vector_path
        self.raster_array = gf.load_image(raster_path, no_data)
        self.img_dataset = gdal.Open(raster_path)
        # self.raster_array = self.img_dataset.ReadAsArray()
        # self.raster_array = np.rollaxis(self.raster_array, 0, start=3)
        

    #TODO: Verify why the EVI result is all 0.0
    #TODO: Review either EVI2
    def compute_indexes(self, parameters):
        for idx, params in parameters.items():
            result = self.predefIndexes[idx](self.raster_array, params)
            num_bands = self.raster_array.shape[2]
            self.sint_bands[idx] = num_bands
            self.raster_array = np.ma.dstack((self.raster_array[:,:,:num_bands], result))

        return self.raster_array

    def get_position_index_band(self, index):
        return self.sint_bands[index]

    def get_index_band(self, index):
        return self.raster_array[:,:,self.get_position_index_band(index)]

    def get_raster_stacked_raster(self):
        return self.raster_array

    def register_new_idx_func(self, name, function):
        self.predefIndexes[name] = function

    def standardize_image(self, strategy="mean_std", params=None):
        if params is None:
            self.raster_array = self.standardize_functions[strategy](self.raster_array)
        else:
            self.raster_array = self.standardize_functions[strategy](self.raster_array, params)
        return self.raster_array

    def register_standardization(self, name, function):
        self.standardize_functions[name] = function

    def save_index_raster(self, index, out_path):
        driver = gdal.GetDriverByName("GTiff")
        ds_band = self.img_dataset.GetRasterBand(1)
        out_xSize = ds_band.XSize
        out_ySize = ds_band.YSize
        output_ds = driver.Create(out_path,
                                  out_xSize, out_ySize, 1)
        output_ds.SetProjection(self.img_dataset.GetProjection())
        output_ds.SetGeoTransform(self.img_dataset.GetGeoTransform())
        outputBand = output_ds.GetRasterBand(1)
        outputBand.WriteArray(self.get_index_band(index))

    def save_stacked_raster(self, out_path):
        driver = gdal.GetDriverByName("GTiff")
        ds_band = self.img_dataset.GetRasterBand(1)
        out_xSize = ds_band.XSize
        out_ySize = ds_band.YSize
        nbands = self.raster_array.shape[2]
        output_ds = driver.Create(out_path,
                                  out_xSize, out_ySize, nbands)

        for band in range(nbands):
            output_ds.SetProjection(self.img_dataset.GetProjection())
            output_ds.SetGeoTransform(self.img_dataset.GetGeoTransform())
            outputBand = output_ds.GetRasterBand(band + 1)
            outputBand.WriteArray(self.raster_array[:,:,band])