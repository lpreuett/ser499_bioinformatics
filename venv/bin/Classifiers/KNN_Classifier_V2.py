'''
@author: Larry Preuett
@version: 4.8.2018
'''

import numpy
import csv
from scipy.spatial import distance
import os
import sqlite3

class KNN_Classifier:
    # USE ODD VALUES FOR K
    def __init__(self, knn_k=1):
        cwd = os.getcwd()
        cwd_split = cwd.split('/')
        if cwd_split[len(cwd_split) - 1] == 'bin':
            os.chdir('./Classifiers')
        self.__GOOD_PAIRS_FILE = '../good_pairs.txt'
        self.__BAD_PAIRS_FILE = '../bad_pairs.txt'
        self.__data = []
        self.__debug = False
        self.DB_DIR = '../Database'
        self.DB_FILENAME = 'workflow.db'

        if knn_k > 0:
            self.k = knn_k
        else:
            self.knn_k = 1

        rec_lig_pairs = []
        try:
            with open(self.__GOOD_PAIRS_FILE, 'r') as input_file:
                for line in input_file:
                    # remove new line character
                    line = line.strip('\n')
                    line_split = line.split(' ')
                    rec_lig_pairs.append([line_split[0], line_split[1], 'y'])
            with open(self.__BAD_PAIRS_FILE, 'r') as input_file:
                for line in input_file:
                    # remove new line character
                    line = line.strip('\n')
                    line_split = line.split(' ')
                    rec_lig_pairs.append([line_split[0], line_split[1], 'n'])
        except:
            print('Error reading values from input files')

        if self.__debug:
            print('receptor ligand pairs:\n{}\nnumber of pairs: {}'.format(rec_lig_pairs, len(rec_lig_pairs)))

        # exclude pairs for which we do not have data from all tools
        for pair in rec_lig_pairs:
            rec = pair[0].split(':')[0]
            lig = pair[1].split(':')[0]
            tool_ids = self.get_tool_ids()
            have_data = True
            for tool_id in tool_ids:
                if not self.results_exist(rec, lig, tool_id):
                    have_data = False
                    print('Dont have data for tool_id: {} rec: {} lig: {}'.format(tool_id, rec, lig))

            if have_data:
                # get scores
                patch_dock_score = self.get_results(rec, lig, 1)
                swarm_dock_score = self.get_results(rec, lig, 3)
                pydock_score = self.get_results(rec, lig, 2)
                if self.__debug:
                    print('scores: {} {} {}'.format(patch_dock_score, swarm_dock_score, pydock_score))
                if pair[2] == 'y':
                    value = 1
                else:
                    value = 0
                score = patch_dock_score + swarm_dock_score + pydock_score + [value]
                if self.__debug:
                    print('Score: {}'.format(score))
                self.__data.append(score)

        # convert data lists to numpy arrays
        self.__data = numpy.array(self.__data)
        # randomize data
        numpy.random.shuffle(self.__data)

        #convert array of strings into array of ints
        self.__data = self.__data.astype(float)

        if self.__debug:
            print('data: {}'.format(self.__data))
            print('data size: {}'.format(len(self.__data)))

    def get_tool_ids(self):
        # create connection to db
        conn = sqlite3.connect('{}/{}'.format(self.DB_DIR, self.DB_FILENAME))
        # get db cursor
        cursor = conn.cursor()
        query = 'SELECT id FROM Tool'
        results = cursor.execute(query).fetchall()
        return [i[0] for i in results]

    def get_results(self, rec, lig, tool):
        # create connection to db
        conn = sqlite3.connect('{}/{}'.format(self.DB_DIR, self.DB_FILENAME))
        # get db cursor
        cursor = conn.cursor()
        expected_results = self.get_expected_results(tool)

        # get largest feature id
        query = 'SELECT max(feature_id) FROM Result WHERE rec_pdb_id=:rec AND lig_pdb_id=:lig AND tool_id=:tool'
        dictionary = {'rec': rec, 'lig': lig, 'tool': tool}
        results = cursor.execute(query, dictionary).fetchall()
        feature_id = results[0][0]
        if feature_id is None:
            conn.close()
            return None

        while feature_id >= 1:
            # build query
            query = 'SELECT feature_value FROM Result WHERE rec_pdb_id=:rec AND lig_pdb_id=:lig AND tool_id=:tool AND feature_id=:feature_id'
            dictionary = {'rec': rec, 'lig': lig, 'tool': tool, 'feature_id': feature_id}
            # get results
            results = cursor.execute(query, dictionary).fetchall()

            if len(results) == expected_results:
                conn.close()
                return [i[0] for i in results]
            else:
                feature_id -= 1

        conn.close()
        return None

    def get_expected_results(self, tool):
        # set expected results
        if tool == 1 or tool == 4:
            expected_results = 1
        elif tool == 2:
            expected_results = 4
        elif tool == 3:
            expected_results = 7

        return expected_results

    def results_exist(self, rec, lig, tool):
        # create connection to db
        conn = sqlite3.connect('{}/{}'.format(self.DB_DIR, self.DB_FILENAME))
        # get db cursor
        cursor = conn.cursor()
        # build query
        query = 'SELECT * FROM Result WHERE rec_pdb_id=:rec AND lig_pdb_id=:lig AND tool_id=:tool'
        dictionary = {'rec': rec, 'lig': lig, 'tool': tool}
        # get results
        results = cursor.execute(query, dictionary).fetchall()

        # set expected results
        expected_results = self.get_expected_results(tool)

        if len(results) >= expected_results:
            return True
        else:
            return False

    def __calc_distance(self, v1, v2):
        delta = distance.euclidean(v1[:12], v2[:12])
        if self.__debug:
            print('KNN_Classifier.__calc_distance(v1, v2):')
            print('v1: ' + str(v1[:12]))
            print('v2: ' + str(v2[:12]))
            print('distance: ' + str(delta))
        return abs(delta)

    def __calc_k_neighbors(self, input_entry):
        k_neighbors = numpy.empty([self.k]).astype(int)
        k_neighbors_delta = numpy.empty([self.k])
        furthest_neighbor_delta = 0.0
        furthest_neighbor_index = 0
        num_entries = 0

        for classifier_entry in self.__data:
            delta = self.__calc_distance(classifier_entry, input_entry)

            if num_entries < self.k:
                k_neighbors[num_entries] = classifier_entry[12]
                k_neighbors_delta[num_entries] = delta
                num_entries += 1
            elif delta < furthest_neighbor_delta:
                k_neighbors[furthest_neighbor_index] = classifier_entry[12]
                k_neighbors_delta[furthest_neighbor_index] = delta
                furthest_neighbor_delta = delta
            # update furthest_neighbor
            for i in range(0, len(k_neighbors)):
                if k_neighbors_delta[i] > furthest_neighbor_delta:
                    furthest_neighbor_index = i
                    furthest_neighbor_delta = k_neighbors_delta[i]

        if self.__debug:
            print('k_neighbors after __calc_k_neighbors: ' + str(k_neighbors.astype(int)))
        return k_neighbors.astype(int)

    def __get_neighbor_classification(self, k_neighbors):
        yes = 0
        no = 0

        if self.__debug:
            print('KNN_Classifier.__get_neighbor_classification k_neighbor input: ' + str(k_neighbors))

        for i in range(0, len(k_neighbors)):
            if k_neighbors[i] == 0:
                no += 1
            elif k_neighbors[i] == 1:
                yes += 1
            else:
                raise Exception("Invalid k_neighbors value found at index " + str(i) + ' k_neighbors value: ' + str(k_neighbors))

        if yes >= no:
            return 1
        else:
            return 0

    def classify_data(self, input_data, num_vals):
        if len(input_data[0]) != 12:
            raise Exception('Invalid data dimensions: n x 12 required. Data: {}'.format(input_data))

        classified_data = numpy.empty([num_vals])

        for i in range(0, num_vals):
            k_neighbors = self.__calc_k_neighbors(input_data[i])
            classification = self.__get_neighbor_classification(k_neighbors.astype(int))
            classified_data[i] = classification
            print("Step %d of %d" % (i+1, num_vals))


        if self.__debug:
            print('Output of KNN_Classifier.classified_data: ' + str(classified_data.astype(int)))

        return classified_data.astype(int)
'''
classifier = KNN_Classifier(5)
data = numpy.array([[14598, -40.73, 1, 497, 0, 0, -40.730, 0.000, -12.886, -30.628, 21.847, -41.329]])
data = data.astype(float)
outputs = classifier.classify_data(data, 1)

print('Classifier outputs: {}'.format(outputs))
'''