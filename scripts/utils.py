import pandas as pd
import numpy as np
import igraph as ig
import json
import os
from os.path import join, exists
import yaml
from sklearn.metrics.pairwise import haversine_distances

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

	return cbgs


def filter_patterns(pattern_file, cbgs, save_dir='.'):
	'''
	reads the pattern file, filters them wrt CBGs and saves them to save_dir 
	'''
	col_names = ['safegraph_place_id', 'poi_cbg', 'visitor_home_cbgs', 'raw_visit_counts', 'distance_from_home', 'median_dwell']
	dfs = pd.read_csv(pattern_file, 
		compression='gzip', 
		chunksize=10**6,
		usecols=col_names,
		dtype={c: 'object' for c in col_names})
	date_range = get_pattern_date_range(pattern_file)
	fname = join(save_dir, f"{date_range}.csv")
	header = True

	for df in dfs:
		if exists(fname):
			header = False
		df.loc[df['poi_cbg'].isin(cbgs)].to_csv(fname, 
			mode="a", 
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


def create_network(pattern_file, cbg_loc_df, exclude_cbgs, save_dir='.'):
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
	distance_in_km = []
	for cbg in links:
		for neg_cbg in links[cbg]:
			if neg_cbg in links:
				nodes.add(neg_cbg)
				edges.append((neg_cbg, cbg))
				visits.append(links[cbg][neg_cbg])
				distance_in_km.append(cbg_loc_df.loc[neg_cbg, cbg])
		nodes.add(cbg)

	g.add_vertices(list(nodes))
	g.add_edges(edges)
	g.es['visits'] = visits
	g.es['weight'] = distance_in_km

	g.write_pickle(join(save_dir, pattern_file.split('\\')[-1].split('.')[0]))


if __name__ == '__main__':
	config = parse_config()
	pwd = config['pwd']
	dpath = config['storage']
	patterns = config['pattern-data-path']
	w = 'weekly-v1'
	files = get_pattern_files(join(pwd, dpath, w), patterns[w])
	print(files)