#%%
import mylib.analyzer as mya
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
import sys

#%%
# Name of the test scenes
test_scene_name_list = [
    'maze',
    'base',
    'walls',
    'ceiling',
    'four_col',
    'example02',
]
# Directory names for the test scenes
dir_name_list = [
    './data/maze',
    './data/base',
    './data/walls',
    './data/ceiling',
    './data/four_col',
    './data/example02',
]
# List of experiment names and algorithm names
ex_name_list = [
    'RRT',
    'RRTConnect',
    'RRTstar',
    'EST',
    'BiEST',
    'PRM',
    'pPRM',
    'PRMstar',
]
# List of Planner IDs
alg_name_list = [
    'RRTkConfigDefault',
    'RRTConnectkConfigDefault',
    'RRTstarkConfigDefault',
    'ESTkConfigDefault',
    'BiESTkConfigDefault',
    'PRMkConfigDefault',
    'SemiPersistentPRM',
    'PRMstarkConfigDefault',
]
# List of experiment names excluding star algorithms
ex_name_list2 = [
    'RRT',
    'RRTConnect',
    'EST',
    'BiEST',
    'PRM',
    'pPRM',
]
# List of Planner IDs excluding star algorithms
alg_name_list2 = [
    'RRTkConfigDefault',
    'RRTConnectkConfigDefault',
    'ESTkConfigDefault',
    'BiESTkConfigDefault',
    'PRMkConfigDefault',
    'SemiPersistentPRM',
]

#%% 
# Make results directory if it doesn't exist
if not os.path.exists('./results'):
    os.makedirs('./results')

#%%
# Generate results for each directory
for test_scene_name, dir_name in zip(test_scene_name_list, dir_name_list):
    # Create a directory for each test scene
    if not os.path.exists(f'./results/{test_scene_name}'):
        os.makedirs(f'./results/{test_scene_name}')
    
    # Read the data from the directory
    exp_comp = mya.ExperimentComparison(dir_name, ex_name_list=ex_name_list, alg_name_list=alg_name_list)
    # PCA trajectory
    plt.figure(figsize=(10,12))
    exp_comp.plot_pca_trajectory()
    # plt.suptitle(f'PCA trajectory for {test_scene_name}')
    plt.savefig(f'./results/{test_scene_name}/pca_trajectory.jpg')
    
    plt.figure(figsize=(8,8))
    exp_comp.scatter_pca_trajectory()
    # plt.suptitle(f'PCA trajectory for {test_scene_name}')
    plt.savefig(f'./results/{test_scene_name}/pca_trajectory_scatter.jpg')
    plt.close()

    # Joint trajectory
    if not os.path.exists(f'./results/{test_scene_name}/joint_trajectory'):
        os.makedirs(f'./results/{test_scene_name}/joint_trajectory')
    for joint in range(1, 7):
        plt.figure(figsize=(10,12))
        exp_comp.plot_joint_positions(joint)
        plt.savefig(f'./results/{test_scene_name}/joint_trajectory/joint_{joint}.jpg')
        plt.close()

    # Success rate
    plt.figure()
    fileName = f'./results/{test_scene_name}/success_rate'
    exp_comp.compare_success_rate(saveFig=True, fileName=fileName)
    plt.close()
    # Path length
    plt.figure()
    fileName = f'./results/{test_scene_name}/path_length'
    exp_comp.violin_plot_joint_space_length(saveFig=True, fileName=fileName)
    plt.close()
    # Execution time
    plt.figure()
    fileName = f'./results/{test_scene_name}/exec_time'
    exp_comp.violin_plot_exec_time(saveFig=True, fileName=fileName)
    plt.close()
    # Path variance
    plt.figure()
    fileName = f'./results/{test_scene_name}/path_variance'
    exp_comp.violin_plot_avg_path_variance(saveFig=True, fileName=fileName)
    plt.close()

    # Comparison among the default algorithms
    exp_comp2 = mya.ExperimentComparison(dir_name, ex_name_list=ex_name_list2, alg_name_list=alg_name_list2)
    # Planning time
    plt.figure()
    fileName = f'./results/{test_scene_name}/planning_time'
    exp_comp2.box_plot_planning_time(saveFig=True, fileName=fileName)
    plt.close()


# %%
