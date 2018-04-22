'''
@Author: Larry Preuett
@Version: 11.30.2017
'''
import numpy
import csv
from scipy.stats import multivariate_normal

class Naive_Bayes_Classifier_V2:
    # USE ODD VALUES FOR K
    def __init__(self):
        self.__DATA_FILE_PATH = 'Iris_Dataset/bezdekIris.data'
        self.__data = []

        self.__debug = True
        self.__NUM_INPUT_DATA = 150  # number between 1 and 45211
        self.__data_setosa = []
        self.__data_versicolor = []
        self.__data_virginica = []
        self.means_setosa = []
        self.means_versicolor = []
        self.means_virginica = []
        self.covar_setosa = None
        self.covar_versicolor = None
        self.covar_virginica = None

        with open(self.__DATA_FILE_PATH, newline='') as dataFile:
            reader = csv.reader(dataFile, delimiter=',')
            for row in reader:
                self.__data.append(row)

        # convert data lists to numpy arrays
        self.__data = numpy.array(self.__data)
        # randomize data
        numpy.random.shuffle(self.__data)

        self.__replace_categorical_data()

        # convert array of strings into array of ints
        self.__data = self.__data.astype(float)

        # store yes/no datasets
        for i in range(0, self.__NUM_INPUT_DATA):
            if self.__data[i][4] == 0:
                self.__data_setosa.append(self.__data[i])
            elif self.__data[i][4] == 1:
                self.__data_versicolor.append(self.__data[i])
            elif self.__data[i][4] == 2:
                self.__data_virginica.append(self.__data[i])

        #convert to numpy array
        self.__data_setosa = numpy.array(self.__data_setosa).astype(float)
        self.__data_versicolor = numpy.array(self.__data_versicolor).astype(float)
        self.__data_virginica = numpy.array(self.__data_virginica).astype(float)


        # calculate means
        for k in range(0, 4):
            self.means_setosa.append(numpy.mean(self.__data_setosa[k]))
            self.means_versicolor.append(numpy.mean(self.__data_versicolor[k]))
            self.means_virginica.append(numpy.mean(self.__data_virginica[k]))

        self.covar_setosa = numpy.cov(self.__data_setosa[:, 0:4], rowvar=False)
        self.covar_versicolor = numpy.cov(self.__data_versicolor[:, 0:4], rowvar=False)
        self.covar_virginica = numpy.cov(self.__data_virginica[:, 0:4], rowvar=False)

        print(self.__data)

    def __replace_categorical_data(self):
        for row in self.__data:
            row[4] = self.__replace_y(row[4])

    def __replace_y(self, y_str):
        if y_str == 'Iris-setosa':
            return 0
        elif y_str == 'Iris-versicolor':
            return 1
        elif y_str == 'Iris-virginica':
            return 2

    def classify_data(self, input):
        outputs = []
        for point in input[:, 0:4]:
            outputs.append(self.classify_point(point))

        if self.__debug:
            print("Outputs: {}".format(outputs))

        return outputs

    def classify_point(self, point):
        # calc probability of setosa
        prior_p_setosa = len(self.__data_setosa) / self.__NUM_INPUT_DATA
        # product of probability of yes and probability of point given yes
        p_setosa = prior_p_setosa * multivariate_normal.pdf(point, self.means_setosa, self.covar_setosa)

        # calc probability of virginica
        prior_p_virginica = len(self.__data_virginica) / self.__NUM_INPUT_DATA
        # product of probability of no and probability of point given no
        p_virginica = prior_p_virginica * multivariate_normal.pdf(point, self.means_virginica, self.covar_virginica)

        # calc probability of versicolor
        prior_p_versicolor = len(self.__data_versicolor) / self.__NUM_INPUT_DATA
        # product of probability of no and probability of point given no
        p_versicolor = prior_p_versicolor * multivariate_normal.pdf(point, self.means_versicolor, self.covar_versicolor)

        if self.__debug:
            print("Prior setosa: {} p_setosa: {}".format(prior_p_setosa, p_setosa))
            print("Prior virginica: {} p_virginica: {}".format(prior_p_virginica, p_virginica))
            print("Prior versicolor: {} p_versicolor: {}".format(prior_p_versicolor, p_versicolor))

        if (p_versicolor > p_virginica and p_versicolor > p_setosa):
            return 1
        elif (p_setosa > p_virginica and p_setosa > p_versicolor):
            return 0
        elif (p_virginica > p_setosa and p_virginica > p_versicolor):
            return 2
