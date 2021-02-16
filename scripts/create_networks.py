from tqdm import tqdm
from os.path import join
from utils import *

config = parse_config()
pwd = config['pwd']
dpath = config['storage']
patterns = config['pattern-data-path']

PATTERN_DIR = join(pwd, dpath, 'filtered-patterns')

AREA_NAME = 'NYC'
FILTERED_PATTERN_DIR = join(PATTERN_DIR, f'{AREA_NAME}-patterns')
pattern_files = [join(FILTERED_PATTERN_DIR, f) for f in os.listdir(FILTERED_PATTERN_DIR) if f.endswith('csv')]

NET_PATTERN_DIR = join(pwd, dpath, 'Nets')
if not exists(NET_PATTERN_DIR):
	os.mkdir(NET_PATTERN_DIR)

NETWORK_SAVE_DIR = join(NET_PATTERN_DIR, f'{AREA_NAME}-CBG-CBG-Nets')
if not exists(NETWORK_SAVE_DIR):
	os.mkdir(NETWORK_SAVE_DIR)

for pattern_file in tqdm(pattern_files):
	create_network(pattern_file, save_dir=NETWORK_SAVE_DIR)