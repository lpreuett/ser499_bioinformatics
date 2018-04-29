'''
@Author: Larry Preuett
@Version: 11.30.2017
'''
import numpy
import csv
from scipy.stats import multivariate_normal
import os
import sqlite3

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
        self.DB_DIR = '../Database'
        self.DB_FILENAME = 'workflow.db'
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
            rec = pair[0].split(':')[0]
            lig = pair[1].split(':')[0]
            tool_ids = self.get_tool_ids()
            have_data = True
            for tool_id in tool_ids:
                if not self.results_exist(rec, lig, tool_id):
                    have_data = False

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
            self.covar_yes = numpy.cov(self.__yesData[:, 0:12], rowvar=False)

        if self.__noData.size == 0:
            self.means_no = [0 for i in range(12)]
            self.covar_no = numpy.zeros((12,12))
        else:
            for k in range(0, 12):
                self.means_no.append(numpy.mean(self.__noData[k]))
            self.covar_no = numpy.cov(self.__noData[:, 0:12], rowvar=False)

        self.NUM_INPUT_DATA = len(self.__data)

        if self.__debug:
            print('data: {}'.format(self.__data))
            print('yes data: {}'.format(self.__yesData))
            print('yes means: {}'.format(self.means_yes))
            print('yes covar: {}'.format(self.covar_yes))
            print('no data: {}'.format(self.__noData))
            print('no means: {}'.format(self.means_no))
            print('no covar: {}'.format(self.covar_no))
            print('num input data: {}'.format(self.NUM_INPUT_DATA))

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

    def classify_data(self, input):
        outputs = []
        for point in input[:, 0:12]:
            outputs.append(self.classify_point(point))

        if self.__debug:
            print("Outputs: {}".format(outputs))

        return outputs

    def classify_point(self, point):
        # calc probability of setosa
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