import pyswarms
import pandas as pd
import numpy as np
import scipy
from scipy import stats
from haversine import haversine, Unit
from pyswarms.single.global_best import GlobalBestPSO
import math
import warnings
warnings.filterwarnings("ignore")
import ast
import csv
import time
from mpi4py import MPI
import csv

year = 2018

def convert(df, colname):
    list_here = df[colname].tolist()
    max_num = max(list_here)
    min_num = min(list_here)
    deno = max_num - min_num
    ans = []
    for i in list_here:
        this = ((i-min_num)/deno)*9 + 1
        ans.append(this)
    return ans

def get_table(y):
    t_temp = pd.read_csv('/home/yilunx/Desktop/new_PSO_20210616/table_' + str(y) + '.csv').drop(columns = 'Unnamed: 0')
    t_final = t_temp[['A_cbg', 'B_store', 'I_Includes_parking_lot', 
                      'C_Percentage_of_Visits_'+str(y)]].rename(columns = {'C_Percentage_of_Visits_'+str(y): 'C_Percentage_of_Visits','G_ Distance_between_cbg_and_store': 'G_Distance_between_cbg_and_store'})
    change = ['H_Area_of_store', 'R_Percentage_of_Visits_by_brand_'+str(y), 'G_Distance_between_cbg_and_store', 
    'J_POI_count_where_store_is', 'K_POI_diversity_where_store_is',
             'L_Demographic_similarity']
    for i in change:
        t_final[i] = convert(t_temp, i)
        if str(y) in i:
            t_final = t_final.rename(columns = {i:i[:-5]})
    return t_final

table = get_table(year)
cbgs = list(table.A_cbg.unique())
cbgs_complete = list(table.A_cbg.unique())
params_dict = {'p_0': 'H_Area_of_store', 'p_1': 'I_Includes_parking_lot', 'p_2': 'R_Percentage_of_Visits_by_brand', 'p_3':'J_POI_count_where_store_is', 'p_4': 'K_POI_diversity_where_store_is', 'p_5': 'L_Demographic_similarity', 'p_6':'G_Distance_between_cbg_and_store'}

def get_rate(df, cbg):
    df_temp = df[['A_cbg', 'B_store', 'C_Percentage_of_Visits']]
    rate = df_temp[df_temp.A_cbg == cbg].drop(columns = ['A_cbg'])
    rate = rate.reset_index().rename(columns = {'index':'safegraph_place_id',rate.columns[-1]:'actual_rate'})
    return rate

def compute_row(row,p_0,p_1,p_2,p_3,p_4,p_5,p_6):
    up_first = (row['H_Area_of_store']**p_0)*((1+p_1)**row['I_Includes_parking_lot'])*(row['R_Percentage_of_Visits_by_brand']**p_2)
    up_second = (row['J_POI_count_where_store_is']**p_3)*(row['K_POI_diversity_where_store_is']**p_4)*(row['L_Demographic_similarity']**p_5)
    down = row['G_Distance_between_cbg_and_store']**p_6
    return up_first*up_second/down

def huff_pearson(df, cbg, p_0,p_1,p_2,p_3,p_4,p_5,p_6):
    rate = get_rate(df, cbg)
    df_temp = df[df['A_cbg'] == cbg].drop(columns = ['A_cbg'])
    df_temp['assumed_rate'] = df_temp.apply(lambda row: compute_row(row,p_0,p_1,p_2,p_3,p_4,p_5,p_6),axis = 1)
    df_temp = df_temp[['B_store', 'assumed_rate']]
    if df_temp['assumed_rate'].sum() != 0:
        df_temp['assumed_rate'] = df_temp['assumed_rate'].apply(lambda x:x/df_temp['assumed_rate'].sum())
    merged = pd.merge(rate, df_temp, on='B_store')
    results = stats.pearsonr(merged['actual_rate'],merged['assumed_rate'])
    return 1-results[0]

def get_final_pearson(params):
    return huff_pearson(df, cbg,params[0], params[1], params[2], params[3], params[4], params[5], params[6])

def opt_func(X):
    n_particles = X.shape[0]
    cost = [get_final_pearson(X[i]) for i in range(n_particles)]
    return np.array(cost)

def go_once(cbg):
    constraints = (np.array([1, 1, 1, 1, 1, 1, 1]),
               np.array([40, 40, 40, 40, 40, 40, 40]))
    options = {'c1': 1.5, 'c2': 1.5, 'w': 0.9}
    optimizer = GlobalBestPSO(n_particles=20,
                                    dimensions=7,
                                    options=options,
                                    bounds=constraints)
    cost, joint_vars = optimizer.optimize(opt_func, iters=10)
    return cost, joint_vars

PSO_results = {'cbg':[], 'cost':[], params_dict['p_0']: [], params_dict['p_1']:[], params_dict['p_2']: [], params_dict['p_3']: [], params_dict['p_4']: [], params_dict['p_5']: [], params_dict['p_6']: []}
comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()
N = len(cbgs_complete)//(size-1)
index_here = rank * N
if rank < size -1:
    cbgs = cbgs[index_here:index_here+N]
else:
    cbgs = cbgs[index_here:]

'''
for i, cbg in enumerate(cbgs):

    df = table.copy()
    PSO_results['cbg'].append(str(cbg))

    if max(get_rate(df, cbg)['actual_rate']) == 0:

        PSO_results['cost'].append('no visitors')
        PSO_results[params_dict['p_0']].append('no visitors')
        PSO_results[params_dict['p_1']].append('no visitors')
        PSO_results[params_dict['p_2']].append('no visitors')
        PSO_results[params_dict['p_3']].append('no visitors')
        PSO_results[params_dict['p_4']].append('no visitors')
        PSO_results[params_dict['p_5']].append('no visitors')
        PSO_results[params_dict['p_6']].append('no visitors')

        string = ' no visitors'
    else:
        result_temp = go_once(cbg)
        
        PSO_results['cost'].append(result_temp[0])
        PSO_results[params_dict['p_0']].append(result_temp[1][0])
        PSO_results[params_dict['p_1']].append(result_temp[1][1])
        PSO_results[params_dict['p_2']].append(result_temp[1][2])
        PSO_results[params_dict['p_3']].append(result_temp[1][3])
        PSO_results[params_dict['p_4']].append(result_temp[1][4])
        PSO_results[params_dict['p_5']].append(result_temp[1][5])
        PSO_results[params_dict['p_6']].append(result_temp[1][6])

        string = ' ok'
    print(cbg, string, 'No.'+ str(i))
'''
#r_walks = []
fields=['cbg','cost','H_Area_of_store', 'I_Includes_parking_lot', 'R_Percentage_of_Visits_by_brand', 'J_POI_count_where_store_is', 'K_POI_diversity_where_store_is', 'L_Demographic_similarity', 'G_Distance_between_cbg_and_store']
with open('/home/yilunx/Desktop/new_PSO_20210616/sub_' + str(year) +'/PSO_7params_NYC_20210616_sub_' +str(rank) + '_' + str(year) + '.csv', 'a') as myfile:
    writer = csv.writer(myfile)
    writer.writerow(fields)
    
for cbg in cbgs:
    df = table.copy()
    ans = [str(cbg)]
    if max(get_rate(df, cbg)['actual_rate']) == 0:
        ans.extend(['no visitors']*8)
        string = ' no visitors '
    else:
        result_temp = go_once(cbg)
        ans.append(result_temp[0])
        for c in result_temp[1]:
            ans.append(c)
        string = ' ok '
    print(cbg, string)
    with open('/home/yilunx/Desktop/new_PSO_20210616/sub_' + str(year) +'/PSO_7params_NYC_20210616_sub_' +str(rank) + '_' + str(year) + '.csv', 'a') as myfile:
        wr = csv.writer(myfile)
        wr.writerow(ans)
    #r_walks.append(ans)
'''
r_walks_array = np.array(r_walks)

r_walks_all = None
if rank == 0:
    #eps_mat = sts.norm.rvs(loc=0, scale=sigma, size=(T, S))
    r_walks_all = np.empty([N*size,], dtype='float')
comm.Gather(sendbuf = r_walks_array, recvbuf = r_walks_all, root=0)


PSO_results_df = pd.DataFrame(r_walks_all)
PSO_results_df.to_csv('PSO_7params_NYC_20210616_' +str(size) +'(mpi)_' + str(year) + '.csv')
'''

