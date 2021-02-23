from utils import *
import pandas as pd
import os
from os.path import join, exists
import yaml
from functools import reduce
import shutil
from tqdm import tqdm
import tarfile

config = parse_config()
pwd = config['pwd']
dpath = config['storage']
census_path = join(pwd, dpath, config['proj-config']['open-census'])

census_attributes = config['census-attributes']
codes = {}
for key in census_attributes:
	for field in census_attributes[key]:
		if 'total_population' == field:
			code = census_attributes[key][field]
			codes[code] = code[:3].lower()
		else:
			for subfield, value in census_attributes[key][field].items():
				codes[value] = value[:3].lower()

source_path = join(census_path, 'safegraph_open_census_data', 'data')
if not exists(source_path):
	print('Extracting the specified census files...')
	tobj = tarfile.open(join(census_path, 'safegraph_open_census_data.tar.gz'), mode='r:gz')
	members = []
	for m in tobj.getmembers():
		for code in codes.values():
			if code in m.name:
				members.append(m)
	tobj.extractall(path=census_path, members=members)
	tobj.close()

census_files = np.array([[join(source_path, fname), fname.split('.')[0].split('_')[-1]] for fname in os.listdir(source_path) if not fname.startswith('.')])

dfs = []
for col_name, code in tqdm(codes.items()):
	dfs.append(pd.read_csv(census_files[census_files[:, 1] == code][0,0], usecols=['census_block_group', col_name]))

df = reduce(lambda x,y: x.merge(y, on='census_block_group', how='inner'), dfs)

col_names = ['census_block_group']
for key in census_attributes:
	normalizer = None
	if 'total_population' in census_attributes[key]:
		normalizer = census_attributes[key]['total_population']
	for field, code in census_attributes[key]['subgroups'].items():
		df = df.rename(columns={code: field})
		if normalizer:
			df[field] /= df[normalizer]
		col_names.append(field)

df[col_names].to_csv(join(pwd, 'util_datasets', 'census_attributes.csv'), index=False)