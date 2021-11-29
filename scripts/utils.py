
from os.path import join, exists
from collections import Counter
import geopandas as gpd
from scipy.spatial import distance
import matplotlib.gridspec as gridspec
import pandas as pd
import numpy as np
from tqdm import tqdm
import igraph as ig
import os
import yaml
from os.path import join
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import matplotlib.ticker as ticker
from scipy.stats import entropy
from scipy import stats
from functools import reduce
from sklearn.metrics.pairwise import haversine_distances
import json
from sklearn.neighbors import BallTree
from math import radians
from scipy.cluster import hierarchy
from sklearn.metrics.pairwise import cosine_similarity
import shapely
from mpl_toolkits import mplot3d
import statsmodels.api as sm
import statsmodels.formula.api as smf

import warnings
warnings.filterwarnings('ignore')

nyc_borough_fips_codes = {
    36085: 'Staten Island',
    36061: 'Manhattan',
    36005: 'Bronx',
    36081: 'Queens',
    36047: 'Brooklyn'
}

def parse_config():
	'''
	parse and return the config file as a regular dict
	'''
	# read the config file
	with open(join('..', 'config.yml')) as f:
		config = yaml.safe_load(f)
	return config


def get_pattern_files(pattern_name, data_path):
	'''
	returns the pattern files as a list

	pattern_name: specifies the pattern type (e.g. week-v1) with full path
	data_path: the actual path that stores the patterns under pattern_name
	'''
	ext = 'csv.gz'
	fpath = join(pattern_name, data_path)
	pattern_files = []

	for root, dirs, files in os.walk(fpath):
		for file in files:
			if file.endswith(ext):
				pattern_files.append(join(root, file))

	return pattern_files


def get_pattern_date_range(pattern_file):
	'''
	returns the date range of the given pattern file
	'''
	df = pd.read_csv(pattern_file, compression='gzip', nrows=1)
	return df.iloc[0, :].loc['date_range_start'].split('T')[0]


def get_CBGS(cbg_file, dtype=str):
	'''
	returns the CBGs that belong to the analysed area
	'''
	cbgs = []
	with open(cbg_file) as f:
		d = json.load(f)
		for instance in d['features']:
			cbgs.append(dtype(instance['properties']['GEOID']))

	return set(cbgs)


def filter_patterns(pattern_file, region_fips, save_dir='.'):
	'''
	reads the pattern file, filters them wrt CBGs and saves them to save_dir 
	'''
	col_names = ['safegraph_place_id', 'poi_cbg', 'visitor_home_cbgs']
	dfs = pd.read_csv(pattern_file, 
		compression='gzip', 
		chunksize=10**7,
		usecols=col_names,
		dtype={c: 'object' for c in col_names})
	date_range = get_pattern_date_range(pattern_file)
	fname = join(save_dir, f"{date_range}.csv")
	header = not exists(fname)

	for df in dfs:
		#df = df.dropna(subset=['poi_cbg'])
		df.loc[(df['poi_cbg'].str[:5]).isin(region_fips)].to_csv(fname, 
			mode='a', 
			index=False, 
			header=header)

def generate_links(visit, links, exclude_cbgs):
	'''
	creates a dict of origin - target dict extracted from each row
	'''
	poi_cbg = str(int(visit["poi_cbg"]))
	if poi_cbg not in exclude_cbgs:
		visitor_cbgs = json.loads(visit["visitor_home_cbgs"])
		for cbg in visitor_cbgs.keys():
			str_cbg = str(cbg)
			if str_cbg not in exclude_cbgs:
				if poi_cbg in links:
					if str_cbg in links[poi_cbg]:
						links[poi_cbg][str_cbg] += visitor_cbgs[cbg]
					else:
						links[poi_cbg][str_cbg] = visitor_cbgs[cbg]
				else:
					links[poi_cbg] = {}
					links[poi_cbg][str_cbg] = visitor_cbgs[cbg]


#def create_network(pattern_file, cbg_loc_df, exclude_cbgs, save_dir='.'):
def create_network(pattern_file, exclude_cbgs, save_dir='.'):
	'''
	creates a directed CBG-CBG network and saves it to save_dir
	'''
	df = pd.read_csv(pattern_file)
	links = {}
	df[~df['poi_cbg'].astype(int).astype(str).isin(exclude_cbgs)].apply(generate_links, axis=1, links=links, exclude_cbgs=exclude_cbgs)

	g = ig.Graph(directed=True)

	nodes = set()
	edges = []
	visits = []
	#distance_in_km = []
	for cbg in links:
		for neg_cbg in links[cbg]:
			if neg_cbg in links:
				nodes.add(neg_cbg)
				edges.append((neg_cbg, cbg))
				visits.append(links[cbg][neg_cbg])
				#distance_in_km.append(cbg_loc_df.loc[neg_cbg, cbg])
		nodes.add(cbg)

	g.add_vertices(list(nodes))
	g.add_edges(edges)
	g.es['visits'] = visits
	#g.es['weight'] = distance_in_km

	g.write_pickle(join(save_dir, pattern_file.split('\\')[-1].split('.')[0]))


def bootstrap_ci(values, stat=np.mean, ci_level=95, repetition=10**3):
	nsize = len(values)
	sample_stat = stat(values)
	resamples = []

	for _ in range(repetition):
		rs = np.random.choice(values, nsize, replace=True)
		resamples.append(stat(rs))

	lower = np.percentile(resamples, (100 - ci_level)/2)
	upper = np.percentile(resamples, (100 + ci_level)/2)

	return lower, upper


def mean_time_to_work(row, cols):
    '''
    calculates the mean travel to work time with the help of time categories
    '''
    duration = 0
    w = 0
    for col in cols:
        seg = col.split('-')
        minutes = (int(seg[1]) + int(seg[-1])) / 2
        duration += row[col]*minutes
        w += row[col]
    return duration/w


def get_census_attributes(cpath, county_codes, income_col='median_house_income'):
	'''
	parse the census data for the given locations
	'''
	census_attrs = pd.read_csv(cpath)

	if isinstance(county_codes[0], str):
		fips_codes = census_attrs['census_block_group'].astype(str).str[:5]
	else:
		fips_codes = census_attrs['census_block_group'] // 10**7

	if not isinstance(county_codes, set):
		county_codes = set(county_codes)

	census_attrs = census_attrs[fips_codes.isin(county_codes)]

	commuting_cols = [i for i in census_attrs.columns if i.startswith('t-')]
	census_attrs['mean_time_to_work'] = census_attrs.apply(mean_time_to_work, cols=commuting_cols, axis=1)

	edu_cols = [i for i in census_attrs.columns if 'edu-' in i]
	census_attrs['education'] = sum([census_attrs[i] for i in edu_cols])

	census_attrs['racial_diversity'] = census_attrs.apply(lambda row: entropy([row['white_population'], row['black_population'], 
																			   row['asian_population'], row['hispanic_population']]), axis=1)

	census_attrs = census_attrs.rename(columns={income_col: 'income'})

	col_names = ['income', 'white_population', 'black_population', 'asian_population', 
	'racial_diversity', 'hispanic_population', 'education', 'mean_time_to_work']

	quart = ['Bottom', 'Third', 'Second', 'Top']
	for col in col_names:
		census_attrs[f'{col}-quartile'] = pd.qcut(census_attrs[col], q=4, labels=[f'{quart[i]}' for i in range(4)])

	census_quartiles = census_attrs[['census_block_group', *[f'{cn}-quartile' for cn in col_names]]]
	census_raw_values = census_attrs[['census_block_group', 'total_population', *col_names]]

	return census_quartiles, census_raw_values


def load_networks(network_dir):
	nets = [[datetime.strptime(f, '%Y-%m-%d'), ig.Graph.Read_Pickle(join(network_dir, f))] 
		for f in tqdm(os.listdir(network_dir))]
	return np.array(sorted(nets, key=lambda x: x[0]))


if __name__ == '__main__':
	config = parse_config()
	pwd = config['pwd']
	dpath = config['storage']
	patterns = config['pattern-data-path']
	w = 'weekly-v1'
	files = get_pattern_files(join(pwd, dpath, w), patterns[w])
	print(files)