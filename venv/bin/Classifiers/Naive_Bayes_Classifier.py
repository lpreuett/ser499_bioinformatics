'''
@Author: Larry Preuett
@Version: 11.30.2017
'''
import numpy
import csv
from scipy.stats import multivariate_normal
import os
import tarfile
import re

class Naive_Bayes_Classifier:
    # USE ODD VALUES FOR K
    def __init__(self):
        self.__GOOD_PAIRS_FILE = '../good_pairs.txt'
        self.__BAD_PAIRS_FILE = '../bad_pairs.txt'
        self.__data = []
        self.__yesData = []
        self.__noData = []
        self.means_no = []
        self.means_yes = []
        self.covar_no = None
        self.covar_yes = None
        self.PATCH_DOCK_OUTPUT_DIR = '../Patch Dock/output'
        self.PYDOCK_OUTPUT_DIR = '../pyDockWEB/output'
        self.SWARM_DOCK_OUTPUT_DIR = '../Swarm Dock/output'
        self.NUM_INPUT_DATA = 0
        self.__debug = True

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

            if os.path.isfile('{}/{}.txt'.format(self.PATCH_DOCK_OUTPUT_DIR, filename)) and \
                    os.path.isfile('{}/{}.tar.gz'.format(self.PYDOCK_OUTPUT_DIR, filename)) and \
                    os.path.isfile('{}/{}.tar.gz'.format(self.SWARM_DOCK_OUTPUT_DIR, filename)):
                # get scores
                patch_dock_score = self.__get_patch_dock_score(filename + '.txt')
                swarm_dock_score = self.__get_swarm_dock_score(filename + '.tar.gz')
                pydock_score = self.__get_pydock_score(filename + '.tar.gz')
                if pair[2] == 'y':
                    value = 1
                else:
                    value = 0
                score = [patch_dock_score] + swarm_dock_score + pydock_score + [value]
                if self.__debug:
                    print('Score: {}'.format(score))
                self.__data.append(score)
                if value == 1:
                    self.__yesData.append(score)
                else:
                    self.__noData.append(score)

        # convert data lists to numpy arrays
        self.__data = numpy.array(self.__data)
        self.__noData = numpy.array(self.__noData)
        self.__yesData = numpy.array(self.__yesData)

        # randomize data
        numpy.random.shuffle(self.__data)

        # convert array of strings into array of ints
        self.__data = self.__data.astype(float)
        self.__noData = self.__noData.astype(float)
        self.__yesData = self.__yesData.astype(float)

        if self.__yesData.size == 0:
            self.means_yes = [0 for i in range(12)]
            self.covar_yes = numpy.zeros((12,12))
        else:
            # calculate means
            for k in range(0, 12):
                self.means_yes.append(numpy.mean(self.__yesData[k]))
            self.covar_yes = numpy.cov(self.__data_yes[:, 0:12], rowvar=False)

        if self.__noData.size == 0:
            self.means_no = [0 for i in range(12)]
            self.covar_no = numpy.zeros((12,12))
        else:
            for k in range(0, 12):
                self.means_no.append(numpy.mean(self.__noData[k]))
            self.covar_no = numpy.cov(self.__noData[:, 0:12], rowvar=False)

        self.NUM_INPUT_DATA = self.__data.size

        if self.__debug:
            print('data: {}'.format(self.__data))
            print('yes data: {}'.format(self.__yesData))
            print('yes means: {}'.format(self.means_yes))
            print('yes covar: {}'.format(self.covar_yes))
            print('no data: {}'.format(self.__noData))
            print('no means: {}'.format(self.means_no))
            print('no covar: {}'.format(self.covar_no))
            print('num input data: {}'.format(self.NUM_INPUT_DATA))

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

    def classify_data(self, input):
        outputs = []
        for point in input[:, 0:12]:
            outputs.append(self.classify_point(point))

        if self.__debug:
            print("Outputs: {}".format(outputs))

        return outputs

    def classify_point(self, point):
        # calc probability of setosa
        print(self.NUM_INPUT_DATA)
        if self.__yesData.size == 0:
            prior_p_yes = 0
            p_yes = 0
        else:
            prior_p_yes = self.__yesData.size / self.NUM_INPUT_DATA
            # product of probability of yes and probability of point given yes
            p_yes = prior_p_yes * multivariate_normal.pdf(point, self.means_yes, self.covar_yes)

        # calc probability of virginica
        if self.__noData.size == 0:
            prior_p_no = 0
            p_no = 0
        else:
            prior_p_no = self.__noData.size / self.NUM_INPUT_DATA
            # product of probability of no and probability of point given no
            p_no = prior_p_no * multivariate_normal.pdf(point, self.means_no, self.covar_no)

        if self.__debug:
            print("Prior no: {} p_no: {}".format(prior_p_no, p_no))
            print("Prior yes: {} p_yes: {}".format(prior_p_yes, p_yes))

        if (p_yes > p_no):
            return 1
        else:
            return 0


######### COVAR RETURNS SINGULAR MATRIX
classifier = Naive_Bayes_Classifier()
data = numpy.array([[14598, -40.73, 1, 497, 0, 0, -40.730, 0.000, -12.886, -30.628, 21.847, -41.329]])
data = data.astype(float)
outputs = classifier.classify_data(data)
print(outputs)