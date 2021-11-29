import glob
from utils import *

config = parse_config()

panel_summary_files = []
search_dirs = ['home_panel_summary', 'home-summary-file']
for sd in search_dirs:
	panel_summary_files += glob.glob(join(config['pwd'], config['storage'], '**', sd, '**', '*.csv'), recursive=True)

ny_msa = set(nyc_borough_fips_codes.keys())

dfs = []
for pfile in tqdm(panel_summary_files):
	df = pd.read_csv(pfile)
	df = df[(df.census_block_group // 10**7).isin(ny_msa)]
	dfs.append(df)

pd.concat(dfs, axis=0).to_csv(join(config['pwd'], config['util_datasets'], 'ny-msa-device-counts.csv'), index=False)