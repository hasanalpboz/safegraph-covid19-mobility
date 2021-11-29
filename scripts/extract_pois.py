import pandas as pd
import numpy as np
import os
from utils import *
import tarfile
from zipfile import ZipFile
import shutil
from tqdm import tqdm
import geopandas as gpd

config = parse_config()
pwd = config['pwd']
dpath = config['storage']
util_datasets = config['util_datasets']

AREA = 'NYC'
SAVE_DIR = join(pwd, dpath, 'area-pois', AREA)
if not exists(SAVE_DIR):
	os.mkdir(SAVE_DIR)

area_boundaries = gpd.read_file(join(pwd, util_datasets, AREA, 'msa-counties.geojson'))
area_boundaries = area_boundaries.to_crs('EPSG:4326')
area_boundaries = area_boundaries[['GEOID', 'geometry']]

col_names = ['safegraph_place_id', 'top_category', 'sub_category', 'latitude', 'longitude']

source_path = join(pwd, dpath, 'core-places')
poi_files = []
ext = '.zip'
for root, dirs, files in os.walk(source_path):
		for file in files:
			if file.endswith(ext):
				poi_files.append((root, join(root, file)))

for root, pfile in tqdm(poi_files):
	with ZipFile(pfile, 'r') as zobj:
		for zf in zobj.namelist():
			if zf.endswith('.gz'):
				zobj.extract(zf, path=root)

	extracted_poi_files = []
	dfs = []
	for poif in os.listdir(root):
		if poif.endswith('.gz'):
			extracted_poi_files.append(poif)
			df = pd.read_csv(join(root, poif), compression='gzip', usecols=col_names)
			gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs='EPSG:4326')
			dfs.append(gpd.sjoin(gdf, area_boundaries, how='inner', op='within'))

	fname = root.split('\\')[-1]
	pd.concat(dfs, axis=0).to_csv(join(SAVE_DIR, f'{fname}-pois.csv'), index=False)

	for f in extracted_poi_files:
		os.remove(join(root, f))
