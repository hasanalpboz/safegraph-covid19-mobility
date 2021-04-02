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

NETWORK_SAVE_DIR = join(NET_PATTERN_DIR, f'{AREA_NAME}-CBG-CBG-Nets-Staten_Island_Removed')
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

# staten island cbgs
si_cbgs = set(pd.read_csv(join(pwd, 'util_datasets', 'staten_island_cbgs.csv'))['cbgs'].astype(str).values)

for pattern_file in tqdm(pattern_files[34:]):
	create_network(pattern_file, loc_df, si_cbgs, save_dir=NETWORK_SAVE_DIR)
