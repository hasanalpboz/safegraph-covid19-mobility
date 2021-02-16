import pandas as pd
import numpy as np
import igraph as ig
import json
import os
from os.path import join, exists
import yaml


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


def get_CBGS(cbg_file):
	'''
	returns the CBGs that belong to the analysed area
	'''
	cbgs = []
	with open(cbg_file) as f:
		d = json.load(f)
		for instance in d['features']:
			cbgs.append(instance['properties']['GEOID'])

	return cbgs


def filter_patterns(pattern_file, cbgs, save_dir='.'):
	'''
	reads the pattern file, filters them wrt CBGs and saves them to save_dir 
	'''
	col_names = ['poi_cbg', 'visitor_daytime_cbgs']
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


def create_network(pattern_file, save_dir='.'):
	'''
	creates a directed CBG-CBG network and saves it to save_dir
	'''
	


if __name__ == '__main__':
	config = parse_config()
	pwd = config['pwd']
	dpath = config['storage']
	patterns = config['pattern-data-path']
	w = 'weekly-v1'
	files = get_pattern_files(join(pwd, dpath, w), patterns[w])
	print(files)