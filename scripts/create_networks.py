from tqdm import tqdm
from os.path import join
from utils import *
from math import radians

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

AREA_CBG_FILE = join('..', 'util_datasets', AREA_NAME, f'{AREA_NAME}-cbgs.json')
cbgs = get_CBGS(AREA_CBG_FILE)

cbg_loc_file = join('..', 'util_datasets', 'cbg_geographic_data.csv')
loc_df = pd.read_csv(cbg_loc_file, usecols=['census_block_group', 'latitude', 'longitude'])
loc_df['census_block_group'] = loc_df['census_block_group'].astype(str)
loc_df = loc_df[loc_df['census_block_group'].isin(cbgs)].set_index('census_block_group')
loc_df['latitude'] = loc_df['latitude'].apply(radians)
loc_df['longitude'] = loc_df['longitude'].apply(radians)

loc_df = pd.DataFrame(haversine_distances(loc_df[['latitude', 'longitude']].values) * 6371000/1000, columns=loc_df.index, index=loc_df.index)

for pattern_file in tqdm(pattern_files):
	create_network(pattern_file, loc_df, save_dir=NETWORK_SAVE_DIR)