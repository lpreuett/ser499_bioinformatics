'''
@author: Larry Preuett
@version: 4.8.2018
'''

import numpy
import csv
from scipy.spatial import distance
import os
import tarfile
import re

class KNN_Classifier:

    # USE ODD VALUES FOR K
    def __init__(self, knn_k=1):
        self.__GOOD_PAIRS_FILE = 'good_pairs.txt'
        self.__BAD_PAIRS_FILE = 'bad_pairs.txt'
        self.__data = []
        self.PATCH_DOCK_OUTPUT_DIR = './Patch Dock/scores'
        self.PYDOCK_OUTPUT_DIR = './pyDockWEB/output'
        self.SWARM_DOCK_OUTPUT_DIR = './Swarm Dock/output'
        self.__debug = True

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
            rec = pair[0].split(':')[0].upper()
            lig = pair[1].split(':')[0].upper()
            filename = rec + '_' + lig
            if os.path.isfile(self.PATCH_DOCK_OUTPUT_DIR + '/' + filename + '.txt') and \
                os.path.isfile(self.PYDOCK_OUTPUT_DIR + '/' + filename + '.tar.gz') and \
                os.path.isfile(self.SWARM_DOCK_OUTPUT_DIR + '/' + filename + '.tar.gz'):
                # get scores
                patch_dock_score = self.__get_patch_dock_score(filename+'.txt')
                swarm_dock_score = self.__get_swarm_dock_score(filename+'.tar.gz')
                pydock_score = self.__get_pydock_score(filename+'.tar.gz')
                if pair[2] == 'y':
                    value = 1
                else:
                    value = 0
                score = [patch_dock_score] + swarm_dock_score + pydock_score + [value]
                print('Score: {}'.format(score))
                self.__data.append(score)

        # convert data lists to numpy arrays
        self.__data = numpy.array(self.__data)
        # randomize data
        numpy.random.shuffle(self.__data)

        #convert array of strings into array of ints
        self.__data = self.__data.astype(float)

        print(self.__data)

    def __get_pydock_score(self, filename):
        # extract .tar.gz
        tar = tarfile.open(self.PYDOCK_OUTPUT_DIR + '/' + filename)
        tar_members = tar.getmembers()
        RESULTS_FILE = None
        for m in tar_members:
            if re.search('\w+\.ene', m.name):
                RESULTS_FILE = m.name
        results_file = tar.extractfile(RESULTS_FILE)

        results = None
        line_num = 0
        for line in results_file:
            if line_num == 2:
                # top result
                decoded_line = line.decode('utf-8')
                outputs = re.findall('(-?\d+\.\d+)', decoded_line)
                break

            line_num += 1
        if self.__debug:
            print('pydock score for {} is {}'.format(filename, outputs))
        return outputs

    def __get_swarm_dock_score(self, filename):
        RESULTS_FILENAME = 'sds/clusters_standard.txt'
        # extract .tar.gz
        tar = tarfile.open(self.SWARM_DOCK_OUTPUT_DIR + '/' + filename)
        results_file = tar.extractfile(RESULTS_FILENAME)

        results = None
        is_first_line = True
        for line in results_file:
            if is_first_line:
                is_first_line = False
                continue
            # select first result with 3 or less members
            # decode line
            decoded_line = line.decode('utf8')
            # count number of members
            members_start = decoded_line.find('[')
            members_finish = decoded_line.find(']')
            members = decoded_line[members_start + 1:members_finish].split('|')
            if len(members) <= 3:
                results = decoded_line.split(' ')
                results = results[1:3] + results[4:]
                results = ' '.join(results)
                break
        results = results.rstrip().split(' ')
        if self.__debug:
            print('swarm dock score for {} is {}'.format(filename, results))
        return results

    def __get_patch_dock_score(self, filename):
        with open(self.PATCH_DOCK_OUTPUT_DIR + '/' + filename, 'r') as file:
            line = file.readline()
        if self.__debug:
            print('patch dock score for {} is {}'.format(filename, line))
        return line

    def __calc_distance(self, v1, v2):
        print('v1: {}\nv2: {}'.format(v1, v2))
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

classifier = KNN_Classifier(5)
data = numpy.array([[14598, -40.73, 1, 497, 0, 0, -40.730, 0.000, -12.886, -30.628, 21.847, -41.329]])
data = data.astype(float)
outputs = classifier.classify_data(data, 1)

print('Classifier outputs: {}'.format(outputs))