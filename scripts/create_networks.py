import pandas as pd
import numpy as np
from tqdm import tqdm
from os.path import join
import glob
import json
import igraph as ig
from collections import Ordereddict

config = parse_config()
pwd = config['pwd']
dpath = config['storage']
patterns = config['pattern-data-path']

PATTERN_DIR = join(pwd, dpath, 'filtered-patterns')

AREA_NAME = 'NYC'
FILTERED_PATTERN_DIR = join(PATTERN_DIR, f'{AREA_NAME}-patterns')
pattern_files = [join(FILTERED_PATTERN_DIR, f) for f in os.listdir(FILTERED_PATTERN_DIR) if f.endswith('csv')]

NETWORK_SAVE_DIR = join(pwd, dpath, 'Nets', f'{AREA_NAME}-CBG-CBG-Nets')
if not exists(NETWORK_SAVE_DIR):
	os.mkdir(NETWORK_SAVE_DIR)

for pattern_file in tqdm(pattern_files):
