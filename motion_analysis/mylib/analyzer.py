import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import yaml
from sklearn.decomposition import PCA
from scipy.interpolate import CubicSpline
import numpy as np
from scipy.stats import t

def calculate_statistics(data, confidence=0.95):
    """
    Calculate the mean, variance, and confidence interval for the given data.

    Parameters:
    - data: list or np.array, the input data
    - confidence: float, the confidence level (default is 0.95)

    Returns:
    - mean: float, the mean of the data
    - variance: float, the variance of the data
    - confidence_interval: tuple, the lower and upper bounds of the confidence interval
    """

    data = np.array(data)
    mean = np.mean(data)
    if len(data) < 2:
        print("Warning: Not enough data points to calculate variance and confidence interval.")
        return mean, 0, (mean, mean)  # No variance if less than 2 data points
    variance = np.var(data, ddof=1)  # Sample variance
    std_error = np.sqrt(variance / len(data))
    t_score = t.ppf((1 + confidence) / 2, df=len(data) - 1)
    margin_of_error = t_score * std_error
    confidence_interval = (mean - margin_of_error, mean + margin_of_error)

    return mean, variance, confidence_interval

def plot_confidence_intervals(data_list, labels, confidence=0.95):
    """
    Plot confidence intervals for given data.

    Parameters:
    - data_list: list of np.array, each array contains data for a specific group
    - labels: list of str, labels for each group
    - confidence: float, confidence level for the intervals (default is 0.95)
    """
    for i, data in enumerate(data_list):
        mean, var, cf_interval = calculate_statistics(data, confidence)
        # print(f"Group: {labels[i]}, Mean: {mean}, Variance: {var}, Confidence Interval: {cf_interval}")
        # Plot mean
        plt.plot(i, mean, 'o', color='red', label='Mean' if i == 0 else "")
        # Plot confidence interval
        plt.errorbar(i, mean, yerr=cf_interval[1] - mean, fmt='none', ecolor='black', capsize=5, label='95% CI' if i == 0 else "")



class SingleExperiment: 
    """
    This class provide some metrices for each single experiment.
    The metrices include:
        Scalar:
        - joint space length
        - jerkiness
        - execution time
        - avg mse
        Vector:
        - joint jerks
        - joint errors
        - joint MSE
        - average velocities
        Matrix:
        - joint positions
        - joint velocities
        - joint accelerations

    """
    def __init__(self, dir_name, alg_name, id):
        self.id = id
        # self.planning_time = None
        self.dir_name = dir_name
        self.alg_name = alg_name
        filename = f"{dir_name}/{alg_name}_{id}.csv"
        self.filename = filename  
        if not os.path.exists(filename):
            self.df = None
            self.succeeded = False
        else: 
            self.df = pd.read_csv(filename)
            self.change_df_labels()
            # self.sort_df()
            self.make_time_strictly_increasing()
            self.filter_time_sequence()
            self.succeeded = True
    def copy(self):
        """
        Create a copy of the current instance.
        """
        new_instance = SingleExperiment(self.dir_name, self.alg_name, self.id)
        new_instance.df = self.df.copy() if self.df is not None else None
        new_instance.succeeded = self.succeeded
        return new_instance
    
    def make_time_strictly_increasing(self, debug=False):
        maxTA = 0
        maxTD = 0
        for i in range(len(self.df)):
            if self.df['secA'][i] >= maxTA:
                maxTA = self.df['secA'][i]
            else:
                if debug:
                    print(f'REPORT: secA is going backward at {i} from {maxTA} to {self.df["secA"][i]}')
                self.df.loc[i, 'secA'] = maxTA + self.df['secA'][i]
            if self.df['secD'][i] > maxTD:
                maxTD = self.df['secD'][i]
            elif self.df['secD'][i] == maxTD:
                self.df.loc[i, 'secD'] = self.df['secD'][i] # + 1e-10
                maxTD = self.df['secD'][i]
            else:
                if debug:
                    print(f'REPORT: secD is going backward at {i} from {maxTD} to {self.df["secD"][i]}')
                self.df.loc[i, 'secD'] = maxTD + self.df['secD'][i]

    def filter_time_sequence(self, debug=False):
        if self.df is not None:
            # Ensure that the time columns are strictly increasing
            initial_length = len(self.df)
            new_rows = []
            new_rows.append(self.df.iloc[0])
            currA = self.df['secA'][0]
            currD = self.df['secD'][0]
            prevA = self.df['secA'][0]
            prevD = self.df['secD'][0]
            for i in range(1, len(self.df)):
                prevA = currA
                prevD = currD
                currA = self.df['secA'][i]
                currD = self.df['secD'][i]
                # # if the neighboring time is almost the same
                if currA == prevA:
                    currA = prevA + 1e-10
                    self.df.loc[i, 'secA'] = currA
                if currD == prevD:
                    currD = prevD + 1e-10
                    self.df.loc[i, 'secD']= currD
                # only if the time is strictly increasing, append the row
                if currA > prevA and currD > prevD:
                    new_rows.append(self.df.iloc[i])
                else:
                    currA = prevA
                    currD = prevD
                
                
            self.df = pd.DataFrame(new_rows)
            self.df.reset_index(drop=True, inplace=True)
            res_len = len(self.df)
            if res_len / initial_length < 0.95 and debug:
                print(f"Warning: The number of rows after filtering is {res_len/initial_length * 100 :.2f}%: {res_len}/{initial_length}")

                        
    def sort_df(self):
        if self.df is not None:
            sorted_tA_index = self.df['secA'].argsort()
            sorted_tD_index = self.df['secD'].argsort()
            self.df['secA'] = self.df['secA'].iloc[sorted_tA_index]
            self.df['secD'] = self.df['secD'].iloc[sorted_tD_index]
            for i in range(6):
                self.df[f'j{i+1}pA'] = self.df[f'j{i+1}pA'].iloc[sorted_tA_index]
                self.df[f'j{i+1}pD'] = self.df[f'j{i+1}pD'].iloc[sorted_tD_index]
                self.df[f'j{i+1}vD'] = self.df[f'j{i+1}vD'].iloc[sorted_tD_index]
                self.df[f'j{i+1}aD'] = self.df[f'j{i+1}aD'].iloc[sorted_tD_index]
        
    def smoothen_data(self, resolution=500):
        """
        Smoothen all the data in the dataframe.
        """
        if self.df is not None:
            new_df = pd.DataFrame()
            for i in range(6):
                tA, jpA = self.smooth_curve(self.df['secA'], self.df[f'j{i+1}pA'], resolution)
                tD, jpD = self.smooth_curve(self.df['secD'], self.df[f'j{i+1}pD'], resolution)
                tD, jvD = self.smooth_curve(self.df['secD'], self.df[f'j{i+1}vD'], resolution)
                tD, jaD = self.smooth_curve(self.df['secD'], self.df[f'j{i+1}aD'], resolution)
                new_df[f'j{i+1}pA'] = jpA
                new_df[f'j{i+1}pD'] = jpD
                new_df[f'j{i+1}vD'] = jvD
                new_df[f'j{i+1}aD'] = jaD
                new_df['secA'] = tA
                new_df['secD'] = tD
            self.df = new_df


    def change_df_labels(self):
        self.df = self.df.loc[:, ~self.df.columns.str.contains('^Unnamed')]
        new_labels = [
            'secA', 'secD', 
            'j1pA', 'j1pD', 'j1vD', 'j1aD',
            'j2pA', 'j2pD', 'j2vD', 'j2aD',
            'j3pA', 'j3pD', 'j3vD', 'j3aD',
            'j4pA', 'j4pD', 'j4vD', 'j4aD',
            'j5pA', 'j5pD', 'j5vD', 'j5aD',
            'j6pA', 'j6pD', 'j6vD', 'j6aD'
        ]
        if self.df is not None:
            self.df.columns = new_labels
    
    def smooth_curve(self, x, y, resolution=500):
        """
        Smoothens a sequence of 1D data points using cubic spline interpolation.

        Parameters:
        - x: array-like, the x-values (must be increasing and unique)
        - y: array-like, the y-values corresponding to x
        - resolution: int, number of points in the smoothened curve

        Returns:
        - x_smooth: np.ndarray, interpolated x values
        - y_smooth: np.ndarray, interpolated y values
        """
        x = np.asarray(x)
        y = np.asarray(y)

        # Remove data points where the difference in x is less than 1e-5
        diff_x = np.diff(x)
        valid_indices = np.where(diff_x >= 1e-5)[0]
        x = x[valid_indices]
        y = y[valid_indices]

        if np.any(np.diff(x) <= 0):
            raise ValueError("x values must be strictly increasing for CubicSpline")

        spline = CubicSpline(x, y)
        x_smooth = np.linspace(x[0], x[-1], resolution)
        y_smooth = spline(x_smooth)

        return x_smooth, y_smooth

    def plot_positions(self, joint, smoothen=False):
        if smoothen:
            x_smoothA, y_smoothA = self.smooth_curve(self.df['secA'], self.df[f'j{joint}pA'])
            x_smoothD, y_smoothD = self.smooth_curve(self.df['secD'], self.df[f'j{joint}pD'])
            plt.plot(x_smoothA, y_smoothA, label=f'Joint {joint} Position A Iteration: {self.id}', color='b', marker='', linestyle='-')
            plt.plot(x_smoothD, y_smoothD, label=f'Joint {joint} Position D Iteration: {self.id}', color='r', marker='', linestyle='-')
        else:
            # Plot (timeA, joint_1_positionA)
            plt.plot(self.df['secA'], self.df[f'j{joint}pA'], label=f'Joint {joint} Position A Iteration: {self.id}', color='b', linestyle='-')
            plt.plot(self.df['secD'], self.df[f'j{joint}pD'], label=f'Joint {joint} Position D Iteration: {self.id}', color='r', linestyle='-')
        
    def plot_pca_trajectory(self, pca=None, n_components=2, n_samples=100, color=None):
        data = self.get_uniformally_sampled_posA(n_samples=n_samples)
        data = data.T
        if data.shape[1] != 6:
            raise ValueError("Data shape mismatch: PCA requires 6-dimensional data.")
        if pca is None:
            pca = PCA(n_components=n_components)
            pca.fit(data)
        data = pca.transform(data)
        plt.plot(data[:,0],data[:,1], color=color)
    
    def scatter_pca_trajectory(self, pca, n_components=2, n_samples=100, color=None, label=None):
        data = self.get_uniformally_sampled_posA(n_samples=n_samples)
        if data.shape[0] != 6:
            raise ValueError("Data shape mismatch: PCA requires 6-dimensional data.")
        data = data.reshape((1, -1))
        data = pca.transform(data)
        if label is None:
            plt.scatter(data[:,0],data[:,1], color=color)
        else:
            plt.scatter(data[:,0],data[:,1], color=color, label=label)
            


    def get_uniformally_sampled_posA(self, n_samples=10):
        """
        Get uniformly sampled positions for A.
        output: 6xN array of positions
        """
        posA = np.zeros((6, n_samples))
        for i in range(6):
            posA[i,:] = self.smooth_curve(self.df['secA'], self.df[f'j{i+1}pA'], n_samples)[1]
        return posA
    
    def calc_exec_time(self):
        exec_timeA = self.df['secA'].max() - self.df['secA'].min()
        exec_timeD = self.df['secD'].max() - self.df['secD'].min()
        return exec_timeA, exec_timeD
    
    def calc_error(self):
        """
        output: 6xN array of errors
        """
        posA = np.zeros((6, len(self.df['secA'])))
        posD = np.zeros((6, len(self.df['secD'])))
        for i in range(6):
            posA[i,:] = self.df[f'j{i+1}pA'].to_numpy()
            posD[i,:] = self.df[f'j{i+1}pD'].to_numpy()
        return posA - posD
    
    def calc_mse(self):
        """
        output: 6x1 array of errors
        """
        err = self.calc_error()
        return np.mean(np.square(err), axis=1)
    
    def calc_avg_mse(self):
        mse = self.calc_mse()
        return np.mean(mse)
    
    def get_posA(self):
        posA = np.zeros((6, len(self.df['secA'])))
        for i in range(6):
            posA[i,:] = self.df[f'j{i+1}pA'].to_numpy()
        return posA
    def calc_velA(self):
        """
        output: 6xN array of velocities
        """
        posA = self.get_posA()
        velA = np.zeros((6, len(self.df['secA'])))
        for joint in range(6):
            for i in range (len(self.df['secA'])-1):
                velA[joint, i] = (posA[joint, i+1] - posA[joint, i]) / (self.df['secA'][i+1] - self.df['secA'][i])
        velA[:, -1] = 0
        return velA
    
    def plot_velocities(self, joint):
        # Plot (timeA, joint_1_positionA)
        plt.plot(self.df['secA'], self.calc_velA()[joint-1], label=f'Joint {joint} Velocity A Iteration: {self.id}', color='b', marker='o', linestyle='-')
        plt.plot(self.df['secD'], self.df[f'j{joint}vD'], label=f'Joint {joint} Velocity D Iteration: {self.id}', color='r', marker='x', linestyle='-')

    def calc_avg_velocity(self):
        velA = self.calc_velA()
        velD = np.zeros((6, len(self.df['secD'])))
        for i in range(6):
            velD[i,:] = self.df[f'j{i+1}vD'].to_numpy()
        avg_velA = np.mean(velA, axis=1)
        avg_velD = np.mean(velD, axis=1)
        return avg_velA, avg_velD
    
    def calc_path_length(self, smoothen=False):
        lenA = 0
        lenD = 0
        posA = self.get_posA()
        posD = np.zeros((6, len(self.df['secD'])))
        for i in range(6):
            posD[i,:] = self.df[f'j{i+1}pD'].to_numpy()
        
        for i in range(len(self.df['secA'])-1):
            diffA = posA[:,i+1] - posA[:,i]
            lenA += np.sqrt(diffA.T @ diffA)
            diffD = posD[:,i+1] - posD[:,i]
            lenD += np.sqrt(diffD.T @ diffD)
        return lenA, lenD


    def calc_accA(self):
        velA = self.calc_velA()
        accA = np.zeros((6, len(self.df['secA'])))
        for joint in range(6):
            for i in range (len(self.df['secA'])-1):
                accA[joint, i] = (velA[joint, i+1] - velA[joint, i]) / (self.df['secA'][i+1] - self.df['secA'][i])
        accA[:, -1] = 0
        return accA
    
    def calc_jerk(self):
        accA = self.calc_accA()
        accD = np.zeros((6, len(self.df['secD'])))
        for i in range(6):
            accD[i,:] = self.df[f'j{i+1}aD'].to_numpy()
        jerkA = np.zeros((6, len(self.df['secA'])))
        jerkD = np.zeros((6, len(self.df['secD'])))
        for joint in range(6):
            for i in range (len(self.df['secA'])-1):
                jerkA[joint, i] = (accA[joint, i+1] - accA[joint, i]) / (self.df['secA'][i+1] - self.df['secA'][i])
                dt_D = self.df['secD'][i+1] - self.df['secD'][i]
                if dt_D == 0:
                    dt_D = 1e-30
                jerkD[joint, i] = (accD[joint, i+1] - accD[joint, i]) / dt_D
        jerkA[:, -1] = 0
        jerkD[:, -1] = 0
        return jerkA, jerkD
    
    def plot_accelerations(self, joint):
        accA = self.calc_accA()
        accD = np.zeros((6, len(self.df['secD'])))
        for i in range(6):
            accD[i,:] = self.df[f'j{i+1}aD'].to_numpy()
        # Plot (timeA, joint_1_positionA)
        plt.plot(self.df['secA'], accA[joint-1], label=f'Joint {joint} Acceleration A Iteration: {self.id}', color='b', marker='o', linestyle='-')
        plt.plot(self.df['secD'], accD[joint-1], label=f'Joint {joint} Acceleration D Iteration: {self.id}', color='r', marker='x', linestyle='-')
    
    def plot_jerks(self, joint):
        jerkA, jerkD = self.calc_jerk()
        # Plot (timeA, joint_1_positionA)
        plt.plot(self.df['secA'], jerkA[joint-1], label=f'Joint {joint} Jerk A Iteration: {self.id}', color='b', marker='o', linestyle='-')
        plt.plot(self.df['secD'], jerkD[joint-1], label=f'Joint {joint} Jerk D Iteration: {self.id}', color='r', marker='x', linestyle='-')
        plt.ylim([jerkA[joint-1].min()*1.1, jerkA[joint-1].max()*1.1])

    def calc_effort(self):
        accA = self.calc_accA()
        accD = np.zeros((6, len(self.df['secD'])))
        for i in range(6):
            accD[i,:] = self.df[f'j{i+1}aD'].to_numpy()
        effortA = 0.0
        effortD = 0.0
        for i in range(len(self.df['secA'])-1):
            effortA += (accA[:, i].T @ accA[:, i]) * (self.df['secA'][i+1] - self.df['secA'][i])
            effortD += (accD[:, i].T @ accD[:, i]) * (self.df['secD'][i+1] - self.df['secD'][i])
        return effortA, effortD

    def calc_jerkiness(self):
        """
        Cumulative jerks
        """
        jerkA, jerkD = self.calc_jerk()
        smA = 0
        smD = 0
        for i in range(len(self.df['secA'])-1):
            smA += np.sqrt(jerkA[:,i].T @ jerkA[:,i]) * (self.df['secA'][i+1] - self.df['secA'][i])
            smD += np.sqrt(jerkD[:,i].T @ jerkD[:,i]) * (self.df['secD'][i+1] - self.df['secD'][i])
        return smA, smD
    
    def get_num_samples(self):
        """
        Get the number of samples in the dataframe.
        """
        return self.df.shape[0]

    def get_statistic_vector(self):
        jerkA, jerkD = self.calc_jerkiness()
        plenA, plenD = self.calc_path_length()
        exec_timeA, exec_timeD = self.calc_exec_time()
        mse = self.calc_avg_mse()
        vecA = [jerkA, plenA, exec_timeA, mse]
        vecD = [jerkD, plenD, exec_timeD, mse]
        vecA = np.array(vecA).flatten()
        vecD = np.array(vecD).flatten()
        # print(f"vecA: {vecA}")
        return vecA, vecD

class ExperimentSet:
    """
    This class collects the metrics for each single experiment.
    The metrics include:
        Scalar:
        - average joint space length
        - average jerkiness
        - average execution time
        - average planning time
        - success rate
        
    """
    def __init__(self, dir_name, alg_name):
        self.dir_name = dir_name
        self.alg_name = alg_name
        # load yaml file
        with open (f"{dir_name}/{alg_name}_experiment_config.yaml", 'r') as file:
            config = yaml.safe_load(file)
            self.config = config['experiment_config']
        n_data = self.config['num_iterations']
        self.ex_list = self.load_ex_list(dir_name, alg_name, n_data)
        self.plannning_times = self.load_planning_times(dir_name, alg_name)
        self.hasData = False
        for pl_time in self.plannning_times:
            if pl_time > 0:
                self.hasData = True
                break

    def copy(self):
        """
        Create a copy of the current instance.
        """
        new_instance = ExperimentSet(self.dir_name, self.alg_name)
        new_instance.ex_list = [ex.copy() for ex in self.ex_list]
        new_instance.plannning_times = self.plannning_times.copy()
        return new_instance
    def smoothen_data(self, resolution=500):
        """
        Smoothen all the data in the dataframe.
        """
        for ex in self.ex_list:
            ex.smoothen_data(resolution)
    
    def get_min_max_time(self):
        min_time = np.inf
        max_time = -np.inf
        for ex in self.ex_list:
            if ex.succeeded:
                min_time = min(min_time, ex.df['secA'].min(), ex.df['secD'].min())
                max_time = max(max_time, ex.df['secA'].max(), ex.df['secD'].max())
        return min_time, max_time

    def get_min_max_position(self, joint):
        min_pos = np.inf
        max_pos = -np.inf
        for ex in self.ex_list:
            if ex.succeeded:
                min_pos = min(min_pos, ex.df[f'j{joint}pA'].min(), ex.df[f'j{joint}pD'].min())
                max_pos = max(max_pos, ex.df[f'j{joint}pA'].max(), ex.df[f'j{joint}pD'].max())
        return min_pos, max_pos

    def load_ex_list(self, dir_name, alg_name, n_data):
        ex_list = []
        for i in range(n_data):
            ex_list.append(SingleExperiment(dir_name, alg_name, i))
        return ex_list
    
    def load_planning_times(self, dir_name, alg_name):
        planning_times = []
        df = pd.read_csv(f"{dir_name}/{alg_name}_time.csv")
        planning_times = df.to_numpy()
        planning_times[planning_times < 0] = -1.0
        planning_times = planning_times.flatten()
        return planning_times

    def calc_success_rate(self):
        """ 
        This is the conditional success rate of the planning time.
        with the assumption that the planning was successful
        """
        if len(self.ex_list) == 0:
            return 0.0
        cnt = 0
        for ex in self.ex_list:
            if ex.succeeded:
                cnt += 1
        success_rate = cnt / len(self.ex_list)
        return success_rate
    
    def get_avg_mse_arr(self):
        mse_arr = []
        for ex in self.ex_list:
            if ex.succeeded:
                mse = ex.calc_avg_mse()
                mse_arr.append(mse)
        mse_arr = np.array(mse_arr)
        return mse_arr

    def get_planning_time_arr(self):
        return self.plannning_times
    
    def get_uniformally_sampled_posA_arr(self, n_samples=100):
        """
        Output: N x 6 x n_samples np.array or empty array
        """
        posA_arr = []
        for ex in self.ex_list:
            if ex.succeeded:
                posA = ex.get_uniformally_sampled_posA(n_samples)
                posA_arr.append(posA)
        posA_arr = np.array(posA_arr)
        return posA_arr
    
    def plot_pca_trajectory(self, pca=None, n_components=2, n_samples=100, color=None):
        data_arr = self.get_uniformally_sampled_posA_arr(n_samples=n_samples)
        # swap axis 
        if len(data_arr) == 0:
            print("No data to plot")
            return
        data_arr = data_arr.swapaxes(1,2) # shape is now (N x n_samples x 6)
        shape = data_arr.shape
        data_arr = data_arr.reshape((-1, shape[2])) # N*n_samples x 6 matrix
        if pca is None:
            pca = PCA(n_components=n_components)
            pca.fit(data_arr)
        for i, ex in enumerate(self.ex_list):
            if ex.succeeded:
                ex.plot_pca_trajectory(pca=pca, n_components=n_components, color=color)

    def scatter_pca_trajectory(self, pca=None, n_components=2, n_samples=100, color=None, label=None):
        data_arr = self.get_uniformally_sampled_posA_arr(n_samples=n_samples)
        if len(data_arr) == 0:
            print("No data to plot")
            return
        shape = data_arr.shape
        data_arr = data_arr.reshape((shape[0], shape[1]*shape[2])) # N x 6*n_samples matrix
        if pca is None:
            pca = PCA(n_components=n_components)
            pca.fit(data_arr)
        for i, ex in enumerate(self.ex_list):
            # if i != 0:
            #     label = None
            if ex.succeeded:
                ex.scatter_pca_trajectory(pca=pca, n_components=n_components, color=color, n_samples=n_samples, label=label)
    def calc_path_mean(self, n_samples=100):
        """
        Calculate the path mean for each experiment.
        output: 6 x n_samples array of path mean
        """
        uniPosA_arr = self.get_uniformally_sampled_posA_arr(n_samples=n_samples)
        path_mean = np.zeros((6, n_samples))
        for i in range(6):
            path_mean[i,:] = np.mean(uniPosA_arr[:,i,:], axis=0)
        return path_mean

    def calc_path_variance(self, n_samples=100):
        """
        Calculate the path variance for each experiment.
        output: 6 x n_samples array of path variance
        """
        uniPosA_arr = self.get_uniformally_sampled_posA_arr(n_samples=n_samples) # shape is (N x 6 x n_samples)
        path_variance = np.zeros((6, n_samples))
        for i in range(6):
            path_variance[i,:] = np.var(uniPosA_arr[:,i,:], axis=0, ddof=1)
        return path_variance
    
    def calc_avg_path_mean(self, n_samples=100):
        """
        Calculate the average path mean for each experiment.
        output: 1 x n_samples array of average path mean
        """
        return np.mean(self.calc_path_mean(n_samples=n_samples), axis=0)

    def calc_avg_path_variance(self, n_samples=100):
        """
        Calculate the average path variance for each experiment.
        output: 1 x n_samples array of average path variance
        """
        return np.mean(self.calc_path_variance(n_samples=n_samples), axis=0)

    def get_path_length_arr(self):
        len_arrA = []
        len_arrD = []
        for ex in self.ex_list:
            if ex.succeeded:
                lenA, lenD = ex.calc_path_length()
                len_arrA.append(lenA)
                len_arrD.append(lenD)

        len_arrA = np.array(len_arrA)
        len_arrD = np.array(len_arrD)
        return len_arrA, len_arrD

    def get_effort_arr(self):
        effortA = []
        effortD = []
        for ex in self.ex_list:
            if ex.succeeded:
                eA, eD = ex.calc_effort()
                effortA.append(eA)
                effortD.append(eD)
        effortA = np.array(effortA)
        effortD = np.array(effortD)
        return effortA, effortD

    def get_jerkiness_arr(self):
        smA_arr = []
        smD_arr = []
        for ex in self.ex_list:
            if ex.succeeded:
                smA, smD = ex.calc_jerkiness()
                smA_arr.append(smA)
                smD_arr.append(smD)
        smA_arr = np.array(smA_arr)
        smD_arr = np.array(smD_arr)
        return smA_arr, smD_arr
    
    def get_exec_time_arr(self):
        exec_timeA = []
        exec_timeD = []
        for ex in self.ex_list:
            if ex.succeeded:
                etA, etD = ex.calc_exec_time()
                exec_timeA.append(etA)
                exec_timeD.append(etD)
        return exec_timeA, exec_timeD
    
    def get_num_samples_arr(self):
        num_samples_arr = []
        for ex in self.ex_list:
            if ex.succeeded:
                num_samples = ex.get_num_samples()
                num_samples_arr.append(num_samples)
        num_samples_arr = np.array(num_samples_arr)
        return num_samples_arr

    def calc_avg_path_length(self):
        len_arrA, len_arrD = self.get_path_length_arr()
        avgA = 0.0
        avgD = 0.0
        if len(len_arrA) != 0:
            avgA = np.mean(len_arrA[len_arrA>0])
        if len(len_arrD) != 0:
            avgD = np.mean(len_arrD[len_arrD>0])
        return avgA, avgD
    def calc_avg_jerkiness(self):
        smA_arr, smD_arr = self.get_jerkiness_arr()
        avgA = 0.0
        avgD = 0.0
        if len(smA_arr) != 0:
            avgA = np.mean(smA_arr[smA_arr>0])
        if len(smD_arr) != 0:
            avgD = np.mean(smD_arr[smD_arr>0])
        return avgA, avgD
    
    def get_statistic_vector_arr(self):
        vecA_arr = np.empty((6, len(self.ex_list)))
        vecD_arr = np.empty((6, len(self.ex_list)))
        for ex in self.ex_list:
            if ex.succeeded:
                vecA, vecD = ex.get_statistic_vector()
                for vec in vecA:
                    np.append(vecA_arr, vec, axis=1)
                for vec in vecD:
                    np.append(vecD_arr, vec, axis=1)
        print(f"vecA_arr: {vecA_arr}")
        # vecA_arr = np.array(vecA_arr)
        # vecD_arr = np.array(vecD_arr)

        return vecA_arr, vecD_arr
    
    def box_plot_planning_time(self):
        """
        Plot the planning time box plot.
        """
        plannint_times = self.plannning_times
        plannint_times = plannint_times[plannint_times>0]
        plt.boxplot(plannint_times, label=self.alg_name)

    
    def plot_positions(self, joint):
        for ex in self.ex_list:
            if ex.succeeded:
                ex.plot_positions(joint)
        plt.title(f'Joint {joint} Position')
        plt.xlabel('Time (s)')
        plt.ylabel('Position (rad)')
    


class ExperimentComparison:
    """
    This class compares experiments with different algorithms.
    The metrics include:
        Scalar:
        - average joint space length
        - average jerkiness
        - average execution time
        - average planning time
        - success rate
        on each experiment
    """
    def __init__(self, dir_name, ex_name_list, alg_name_list):
        self.dir_name = dir_name
        self.ex_name_list = ex_name_list
        self.alg_name_list = alg_name_list
        self.experiments = []
        for ex_name, alg_name in zip(ex_name_list, alg_name_list):
            ex_set = ExperimentSet(dir_name + '/' + ex_name, alg_name)
            self.experiments.append(ex_set)
    
    def copy(self):
        """
        Create a copy of the current instance.
        """
        new_instance = ExperimentComparison(self.dir_name, self.ex_name_list, self.alg_name_list)
        new_instance.experiments = [ex.copy() for ex in self.experiments]
        return new_instance
    
    def smoothen_data(self, resolution=500):
        """
        Smoothen all the data in the dataframe.
        """
        for ex in self.experiments:
            ex.smoothen_data(resolution)
    


    def box_plot_joint_space_length(self):
        """
        Plot the joint space length box plot.
        """
        len_arrA_list = []
        len_arrD_list = []
        for ex in self.experiments:
            len_arrA, len_arrD = ex.get_path_length_arr()
            # len_arrA = len_aarA[len_arrA>0]
            # len_arrD = len_aarD[len_arrD>0]
            len_arrA_list.append(len_arrA)
            len_arrD_list.append(len_arrD)
        
        plt.boxplot(len_arrA_list, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Joint Space Length A')
        plt.xlabel('Experiment')
        plt.ylabel('Length')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        plt.show()

        plt.boxplot(len_arrD_list, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Joint Space Length D')
        plt.xlabel('Experiment')
        plt.ylabel('Length')
        plt.grid(True)
        plt.show()

    
    def violin_plot_joint_space_length(self, saveFig=False, fileName=None, show=False):
        """
        Plot the joint space length violin plot.
        """
        len_arrA_list = []
        len_arrD_list = []
        for ex in self.experiments:
            len_arrA, len_arrD = ex.get_path_length_arr()
            len_arrA_list.append(len_arrA[len_arrA > 0])
            len_arrD_list.append(len_arrD[len_arrD > 0])

        # Create DataFrames for the violin plot
        dfA = pd.DataFrame(len_arrA_list).T
        dfD = pd.DataFrame(len_arrD_list).T
        dfA.columns = self.ex_name_list
        dfD.columns = self.ex_name_list

        # Plot violin plot for A
        sns.violinplot(data=dfA, inner=None, color="lightgray", bw_method=0.2, cut=0)

        plot_confidence_intervals(len_arrA_list, self.ex_name_list)

        plt.title('Violin Plot of Joint Space Length A')
        plt.xlabel('Experiment')
        plt.ylabel('Length')
        plt.grid(True)
        plt.legend()
        if saveFig:
            plt.savefig(fileName + '_A.jpg')
        if show:
            plt.show()

        # Plot violin plot for D
        plt.figure()
        sns.violinplot(data=dfD, inner=None, color="lightgray", bw_method=0.2, cut=0)

        plot_confidence_intervals(len_arrD_list, self.ex_name_list)

        plt.title('Violin Plot of Joint Space Length D')
        plt.xlabel('Experiment')
        plt.ylabel('Length')
        plt.grid(True)
        plt.legend()
        if saveFig:
            plt.savefig(fileName + '_D.jpg')
        if show:
            plt.show()

    def box_plot_planning_time(self, saveFig=False, fileName=None, show=False):
        """
        Plot the planning time box plot.
        """
        planning_time_list = []
        for ex in self.experiments:
            pl_time_arr = ex.get_planning_time_arr()
            pl_time_arr = pl_time_arr[pl_time_arr>0]
            planning_time_list.append(pl_time_arr)
        
        plt.boxplot(planning_time_list, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Planning Time')
        plt.xlabel('Experiment')
        plt.ylabel('Time')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        if saveFig:
            plt.savefig(fileName + '.jpg')
        if show:
            plt.show()
    
    def violin_plot_planning_time(self, saveFig=False, fileName=None, show=False):
        planning_time_list = []
        for ex in self.experiments:
            pl_time_arr = ex.get_planning_time_arr()
            pl_time_arr = pl_time_arr[pl_time_arr > 0]
            planning_time_list.append(pl_time_arr)
        # Create a DataFrame for the violin plot
        df = pd.DataFrame(planning_time_list).T
        df.columns = self.ex_name_list
        # Plot violin plot
        sns.violinplot(data=df, inner=None, color="lightgray", bw_method=0.2, cut=0)
        plot_confidence_intervals(planning_time_list, self.ex_name_list)

        plt.title('Violin Plot of Planning Times')
        plt.xlabel('Experiment')
        plt.ylabel('Planning Time')
        plt.grid(True)
        plt.legend()
        if saveFig:
            plt.savefig(fileName + '.jpg')
        if show:
            plt.show()
    
    def box_plot_mse(self, saveFig=False, fileName=None, show=False):
        """
        Plot the mse box plot.
        """
        mse_list = []
        for ex in self.experiments:
            mse_arr = ex.get_avg_mse_arr()
            mse_arr = mse_arr[mse_arr>0]
            mse_list.append(mse_arr)
        
        plt.boxplot(mse_list, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('MSE')
        plt.xlabel('Experiment')
        plt.ylabel('MSE')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        if saveFig:
            plt.savefig(fileName + '.jpg')
        if show:
            plt.show()

    def box_plot_exec_time(self, saveFig=False, fileName=None, show=False):
        execA_arr = []
        execD_arr = []
        for ex in self.experiments:
            exec_timeA, exec_timeD = ex.get_exec_time_arr()
            execA_arr.append(exec_timeA)
            execD_arr.append(exec_timeD)
        plt.boxplot(execA_arr, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Execution Time A')
        plt.xlabel('Experiment')
        plt.ylabel('Time')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        if saveFig:
            plt.savefig(fileName + '_A.jpg')
        plt.show()

        plt.boxplot(execD_arr, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Execution Time D')
        plt.xlabel('Experiment')
        plt.ylabel('Time')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        if saveFig:
            plt.savefig(fileName + '_D.jpg')
        if show:
            plt.show()

    def violin_plot_exec_time(self, saveFig=False, fileName=None, show=False):
        execA_arr = []
        execD_arr = []
        for ex in self.experiments:
            exec_timeA, exec_timeD = ex.get_exec_time_arr()
            execA_arr.append(exec_timeA)
            execD_arr.append(exec_timeD)

        # Create DataFrames for the violin plot
        dfA = pd.DataFrame(execA_arr).T
        dfD = pd.DataFrame(execD_arr).T
        dfA.columns = self.ex_name_list
        dfD.columns = self.ex_name_list

        # Plot violin plot for A
        sns.violinplot(data=dfA, inner=None, color="lightgray", bw_method=0.2, cut=0)

        plot_confidence_intervals(execA_arr, self.ex_name_list)

        plt.title('Violin Plot of Execution Time A')
        plt.xlabel('Experiment')
        plt.ylabel('Time')
        plt.grid(True)
        plt.legend()
        if saveFig:
            plt.savefig(fileName + '_A.jpg')
        if show:
            plt.show()

        # Plot violin plot for D
        plt.figure()
        sns.violinplot(data=dfD, inner=None, color="lightgray", bw_method=0.2, cut=0)

        plot_confidence_intervals(execD_arr, self.ex_name_list)

        plt.title('Violin Plot of Execution Time D')
        plt.xlabel('Experiment')
        plt.ylabel('Time')
        plt.grid(True)
        plt.legend()
        if saveFig:
            plt.savefig(fileName + '_D.jpg')
        if show:
            plt.show()


    def violin_plot_avg_path_variance(self, n_samples=100, saveFig=False, fileName=None, show=False):
        """
        Plot the average path variance violin plot.
        """
        path_variance_list = []
        for ex in self.experiments:
            if ex.hasData == False:
                print(f"Experiment {ex.dir_name}/{ex.alg_name} has no data.")
                path_variance_list.append(np.full(n_samples, np.nan))
                continue
            path_variance = ex.calc_avg_path_variance(n_samples=n_samples)
            # print(f"Path variance: {path_variance}")
            path_variance_list.append(path_variance)
        
        # Create DataFrames for the violin plot
        df = pd.DataFrame(path_variance_list).T
        df.columns = self.ex_name_list

        # Plot violin plot
        sns.violinplot(data=df, inner=None, color="lightgray", bw_method=0.2, cut=0)

        plot_confidence_intervals(path_variance_list, self.ex_name_list)

        plt.title('Violin Plot of Average Path Variance')
        plt.xlabel('Experiment')
        plt.ylabel('Path Variance')
        plt.grid(True)
        plt.legend()
        if saveFig:
            plt.savefig(fileName + '.jpg')
        if show:
            plt.show()

    def box_plot_effort(self):
        """
        Plot the effort box plot.
        """
        effortA_list = []
        effortD_list = []
        for ex in self.experiments:
            effortA, effortD = ex.get_effort_arr()
            effortA_list.append(effortA)
            effortD_list.append(effortD)
        
        plt.boxplot(effortA_list, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Effort A')
        plt.xlabel('Experiment')
        plt.ylabel('Effort')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        plt.show()

        plt.boxplot(effortD_list, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Effort D')
        plt.xlabel('Experiment')
        plt.ylabel('Effort')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        plt.show() 

    def violin_plot_effort(self, saveFig=False, fileName=None, show=False):
        """
        Plot the effort violin plot.
        """
        effortA_list = []
        effortD_list = []
        for ex in self.experiments:
            effortA, effortD = ex.get_effort_arr()
            effortA_list.append(effortA)
            effortD_list.append(effortD)

        # Create DataFrames for the violin plot
        dfA = pd.DataFrame(effortA_list).T
        dfD = pd.DataFrame(effortD_list).T
        dfA.columns = self.ex_name_list
        dfD.columns = self.ex_name_list

        # Plot violin plot for A
        sns.violinplot(data=dfA, inner=None, color="lightgray", bw_method=0.2, cut=0)

        plot_confidence_intervals(effortA_list, self.ex_name_list)

        plt.title('Violin Plot of Effort A')
        plt.xlabel('Experiment')
        plt.ylabel('Effort')
        plt.grid(True)
        plt.legend()
        if saveFig:
            plt.savefig(fileName + '_A.jpg')
        plt.show()

        # Plot violin plot for D
        sns.violinplot(data=dfD, inner=None, color="lightgray", bw_method=0.2, cut=0)

        plot_confidence_intervals(effortD_list, self.ex_name_list)

        plt.title('Violin Plot of Effort D')
        plt.xlabel('Experiment')
        plt.ylabel('Effort')
        plt.grid(True)
        plt.legend()
        if saveFig:
            plt.savefig(fileName + '_D.jpg')
        plt.show()

    def box_plot_jerkiness(self):
        """
        Plot the jerkiness box plot.
        """
        smA_list = []
        smD_list = []
        for ex in self.experiments:
            smA, smD = ex.get_jerkiness_arr()
            smA_list.append(smA)
            smD_list.append(smD)
        
        plt.boxplot(smA_list, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Jerkiness A')
        plt.xlabel('Experiment')
        plt.ylabel('Jerkiness')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        plt.show()
        plt.boxplot(smD_list, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Jerkiness D')
        plt.xlabel('Experiment')
        plt.ylabel('Jerkiness')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        plt.show()

    def plot_statistic_vec_arr(self):
        """
        Plot the statistic vector for each experiment.
        USE principle compoent to plot in 2D.
        """
        vecA_arr = np.empty((6, len(self.experiments)))
        vecD_arr = np.empty((6, len(self.experiments)))
        for ex in self.experiments:
            vecA, vecD = ex.get_statistic_vector_arr()
            if vecA_arr.size == 0 or vecD_arr.size == 0:
                continue
            np.append(vecA_arr, vecA, axis=1)
            np.append(vecD_arr, vecD, axis=1)
        print(vecA_arr[0])
        vecA_arr = vecA_arr.T
        vecD_arr = vecD_arr.T
        # PCA
        pca = PCA(n_components=2)
        pca.fit(vecA_arr[0])
        X_pca = pca.transform(vecA_arr[0])
        
        plt.scatter(X_pca[:, 0], X_pca[:, 1], label=self.ex_name_list)
        plt.title('PCA of Joint Space Length')
        plt.xlabel('PC1')
        plt.ylabel('PC2')
        plt.legend()
        plt.show()


    def plot_pca_trajectory(self, pca=None, n_components=2, n_samples=100):
        if pca is None:
            data = []
            for i, ex in enumerate(self.experiments):
                arr = ex.get_uniformally_sampled_posA_arr(n_samples=n_samples) # N x 6 x n_samples array
                if arr.size == 0:
                    continue
                arr = arr.swapaxes(1,2) # N x n_samples x 6 array
                arr = arr.reshape((-1, arr.shape[2])) # N*n_samples x 6 array
                data.append(arr) 
            # data = np.array(data) # M x n x 6 array
            # data = data.reshape((-1, data.shape[2])) # M*n x 6 array
            data = np.vstack(data)
            pca = PCA(n_components=n_components)
            pca.fit(data)
        # plot data by using the pca transformation
        # plt.figure(figsize=(12, 12))
        for i, ex in enumerate(self.experiments):
            ex_len = len(self.experiments)
            plt.subplots_adjust(hspace=0.5)
            plt.subplot((ex_len+1)//2, 2, i+1)
            # plt.xlim((-2.5,2.5))
            plt.xlim((-3.5,3.0))
            # plt.ylim((-2.5,2.5))
            plt.ylim((-2.5,3.5))
            plt.grid(True)
            ex.plot_pca_trajectory(pca=pca, n_components=n_components, n_samples=n_samples, color=None)
            plt.title(self.ex_name_list[i])

        # for i, ex in enumerate(self.experiments):
        #     # color = plt.cm.tab10(i % 10)  # Use a colormap to assign a unique color for each experiment
        #     color = None
        #     ex.plot_pca_trajectory(pca=pca, n_components=n_components, n_samples=n_samples, color=color)

    def scatter_pca_trajectory(self, pca=None, n_components=2, n_samples=100, color_list=None):
        if pca is None:
            data = []
            for i, ex in enumerate(self.experiments):
                arr = ex.get_uniformally_sampled_posA_arr(n_samples=n_samples) # N x 6 x n_samples array
                if arr.size == 0:
                    continue
                arr = arr.reshape((arr.shape[0], -1)) # N x 6*n_samples array
                data.append(arr) 
            # data = np.array(data) # M x N x 6*n_samples array
            # data = data.reshape((-1, data.shape[2])) # M*N x 6*n_samples array
            data = np.vstack(data)
            # print(f'data shape: {data.shape}')
            pca = PCA(n_components=n_components)
            pca.fit(data)
        # plt.grid(True)
        for i, ex in enumerate(self.experiments):
            color = plt.cm.tab10((i+0) % len(self.experiments))  # Assign a unique color for each experiment
            if color_list is not None:
                color = color_list[i]
            # color = sns.color_palette("husl", len(self.experiments))[i]  # Use a vivid color palette
            label = self.ex_name_list[i]
            ex.scatter_pca_trajectory(pca=pca, n_components=n_components, n_samples=n_samples, color=color, label=label)
        # plt.legend()
        # show the same label only once
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))  # deduplicates by label
        plt.legend(by_label.values(), by_label.keys())

    def box_plot_num_samples(self):
        """
        Plot the number of samples box plot.
        """
        num_samples_list = []
        for ex in self.experiments:
            num_samples_arr = ex.get_num_samples_arr()
            num_samples_arr = num_samples_arr[num_samples_arr>0]
            num_samples_list.append(num_samples_arr)
        
        plt.boxplot(num_samples_list, label=self.ex_name_list)
        plt.xticks(range(1, len(self.ex_name_list)+1), self.ex_name_list)
        plt.title('Number of Samples')
        plt.xlabel('Experiment')
        plt.ylabel('Number of Samples')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        plt.show()

    def compare_success_rate(self, saveFig=False, fileName=None, show=False):
        """
        Compare the success rate of each experiment.
        """
        success_rate_list = []
        for ex in self.experiments:
            success_rate = ex.calc_success_rate()
            success_rate_list.append(success_rate)
        
        plt.bar(self.ex_name_list, success_rate_list)
        plt.title('Success Rate')
        # plt.ylim(0.0, 1.0)
        plt.xlabel('Experiment')
        plt.ylabel('Success Rate')
        plt.grid(True)
        # plt.legend(self.ex_name_list)
        if saveFig:
            plt.savefig(fileName + '.jpg')
        if show:
            plt.show()
    
    def plot_joint_positions(self, joint):
        minTime = 0
        maxTime = 0
        maxPos = 0
        minPos = 0
        for ex in self.experiments:
            minT, maxT = ex.get_min_max_time()
            minTime = min(minTime, minT)
            maxTime = max(maxTime, maxT)
            minP, maxP = ex.get_min_max_position(joint)
            minPos = min(minPos, minP)
            maxPos = max(maxPos, maxP)

        for i, ex in enumerate(self.experiments):
            ex_len = len(self.experiments)
            plt.subplots_adjust(hspace=0.5)
            plt.subplot((ex_len+1)//2, 2, i+1)
            plt.xlim(minTime, maxTime)
            plt.ylim(minPos, maxPos)
            plt.grid(True)
            ex.plot_positions(joint)
            plt.title(f'{self.ex_name_list[i]}')
        # plt.title(f'Joint {joint} Position')

