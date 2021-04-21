from utils import *
import os
from os.path import join, exists
import pandas as pd
from tqdm import tqdm

config = parse_config()
pwd = config['pwd']
dpath = config['storage']
patterns = config['pattern-data-path']

PATTERN_DIR = join(pwd, dpath, 'filtered-patterns')
if not exists(PATTERN_DIR):
	os.mkdir(PATTERN_DIR)

AREA_NAME = 'NYC'
FILTERED_PATTERN_SAVE_DIR = join(PATTERN_DIR, f'{AREA_NAME}-patterns-V2')
AREA_CBG_FILE = join('..', 'util_datasets', AREA_NAME, f'{AREA_NAME}-cbgs.json')

if not exists(FILTERED_PATTERN_SAVE_DIR):
	os.mkdir(FILTERED_PATTERN_SAVE_DIR)

cbgs = get_CBGS(AREA_CBG_FILE)

for pattern_type in patterns:
	print('-'*5, f'{pattern_type} started', '-'*5)
	pattern_files = get_pattern_files(join(pwd, dpath, pattern_type), patterns[pattern_type])
	for pattern_file in tqdm(pattern_files):
		filter_patterns(pattern_file, cbgs, save_dir=FILTERED_PATTERN_SAVE_DIR)