'''
@author: Larry Preuett
@version: 11.3.2017

Citation Request:
  This dataset is publicly available for research. The details are described in [Moro et al., 2014].
  Please include this citation if you plan to use this database:

  [Moro et al., 2014] S. Moro, P. Cortez and P. Rita. A Data-Driven Approach to Predict the Success of Bank Telemarketing. Decision Support Systems, In press, http://dx.doi.org/10.1016/j.dss.2014.03.001

  Available at: [pdf] http://dx.doi.org/10.1016/j.dss.2014.03.001
                [bib] http://www3.dsi.uminho.pt/pcortez/bib/2014-dss.txt

1. Title: Bank Marketing (with social/economic context)

2. Sources
   Created by: Sérgio Moro (ISCTE-IUL), Paulo Cortez (Univ. Minho) and Paulo Rita (ISCTE-IUL) @ 2014

3. Past Usage:

  The full dataset (bank-additional-full.csv) was described and analyzed in:

  S. Moro, P. Cortez and P. Rita. A Data-Driven Approach to Predict the Success of Bank Telemarketing. Decision Support Systems (2014), doi:10.1016/j.dss.2014.03.001.

4. Relevant Information:

   This dataset is based on "Bank Marketing" UCI dataset (please check the description at: http://archive.ics.uci.edu/ml/datasets/Bank+Marketing).
   The data is enriched by the addition of five new social and economic features/attributes (national wide indicators from a ~10M population country), published by the Banco de Portugal and publicly available at: https://www.bportugal.pt/estatisticasweb.
   This dataset is almost identical to the one used in [Moro et al., 2014] (it does not include all attributes due to privacy concerns).
   Using the rminer package and R tool (http://cran.r-project.org/web/packages/rminer/), we found that the addition of the five new social and economic attributes (made available here) lead to substantial improvement in the prediction of a success, even when the duration of the call is not included. Note: the file can be read in R using: d=read.table("bank-additional-full.csv",header=TRUE,sep=";")

   The zip file includes two datasets:
      1) bank-additional-full.csv with all examples, ordered by date (from May 2008 to November 2010).
      2) bank-additional.csv with 10% of the examples (4119), randomly selected from bank-additional-full.csv.
   The smallest dataset is provided to test more computationally demanding machine learning algorithms (e.g., SVM).

   The binary classification goal is to predict if the client will subscribe a bank term deposit (variable y).

5. Number of Instances: 41188 for bank-additional-full.csv

6. Number of Attributes: 20 + output attribute.

7. Attribute information:

   For more information, read [Moro et al., 2014].

   Input variables:
   # bank client data:
   1 - age (numeric)
   2 - job : type of job (categorical: "admin.","blue-collar","entrepreneur","housemaid","management","retired","self-employed","services","student","technician","unemployed","unknown")
   3 - marital : marital status (categorical: "divorced","married","single","unknown"; note: "divorced" means divorced or widowed)
   4 - education (categorical: "basic.4y","basic.6y","basic.9y","high.school","illiterate","professional.course","university.degree","unknown")
   5 - default: has credit in default? (categorical: "no","yes","unknown")
   6 - housing: has housing loan? (categorical: "no","yes","unknown")
   7 - loan: has personal loan? (categorical: "no","yes","unknown")
   # related with the last contact of the current campaign:
   8 - contact: contact communication type (categorical: "cellular","telephone")
   9 - month: last contact month of year (categorical: "jan", "feb", "mar", ..., "nov", "dec")
  10 - day_of_week: last contact day of the week (categorical: "mon","tue","wed","thu","fri")
  11 - duration: last contact duration, in seconds (numeric). Important note:  this attribute highly affects the output target (e.g., if duration=0 then y="no"). Yet, the duration is not known before a call is performed. Also, after the end of the call y is obviously known. Thus, this input should only be included for benchmark purposes and should be discarded if the intention is to have a realistic predictive model.
   # other attributes:
  12 - campaign: number of contacts performed during this campaign and for this client (numeric, includes last contact)
  13 - pdays: number of days that passed by after the client was last contacted from a previous campaign (numeric; 999 means client was not previously contacted)
  14 - previous: number of contacts performed before this campaign and for this client (numeric)
  15 - poutcome: outcome of the previous marketing campaign (categorical: "failure","nonexistent","success")
   # social and economic context attributes
  16 - emp.var.rate: employment variation rate - quarterly indicator (numeric)
  17 - cons.price.idx: consumer price index - monthly indicator (numeric)
  18 - cons.conf.idx: consumer confidence index - monthly indicator (numeric)
  19 - euribor3m: euribor 3 month rate - daily indicator (numeric)
  20 - nr.employed: number of employees - quarterly indicator (numeric)

  Output variable (desired target):
  21 - y - has the client subscribed a term deposit? (binary: "yes","no")

8. Missing Attribute Values: There are several missing values in some categorical attributes, all coded with the "unknown" label. These missing values can be treated as a possible class label or using deletion or imputation techniques.

'''

### CONVERT DATA TO NUMPY.ARRAY
### CREATE ENUM VALUES OF EACH CATEGORICAL ATTRIBUTE
### UPDATE CATEGORICAL ATTRIBUTES WITH NUMERICAL EQUIVALENT

import numpy
import csv
import Bank_Data_Enum
import math
from scipy.spatial import distance

class KNN_Classifier:

    # USE ODD VALUES FOR K
    def __init__(self, knn_k=1, k_fold_k=2):
        self.__DATA_FILE_PATH = 'bank-additional/bank-additional-full-randomized.csv'
        self.__data = []
        self.__data_labels = []
        self.__debug = False
        self.__NUM_INPUT_DATA = 10000  # number between 1 and 45211

        if knn_k > 0:
            self.k = knn_k
        else:
            self.knn_k = 1
        if k_fold_k > 2:
            self.k_fold_k = k_fold_k
        else:
            self.k_fold_k = 2

        self.__k_folds = numpy.zeros((self.k_fold_k, math.ceil(float(self.__NUM_INPUT_DATA / self.k_fold_k)), 8), int)
        with open(self.__DATA_FILE_PATH, newline='') as dataFile:
            reader = csv.reader(dataFile, delimiter=';')
            first_row = True
            for row in reader:
                # first line of file contains the labels
                if first_row:
                    self.__data_labels.append(row)
                    first_row = False
                else:
                    self.__data.append(row)

        # convert data lists to numpy arrays
        self.__data = numpy.array(self.__data)
        self.__data_labels = numpy.array(self.__data_labels)
        # randomize data
        numpy.random.shuffle(self.__data)

        # keep only the first 7 columns of data
        self.__data = numpy.insert(self.__data[:, 0:7], 7, self.__data[:, 20], axis=1)
        self.__data_labels = numpy.insert(self.__data_labels[:, 0:7], 7, self.__data_labels[:, 20], axis=1)

        self.__replace_categorical_data()

        #convert array of strings into array of ints
        self.__data = self.__data.astype(int)

        # determine if data can be divided into k even sets
        num_uneven_sets = int(self.__NUM_INPUT_DATA % self.k_fold_k)
        uneven_sets_remaining = num_uneven_sets
        set_size = int(self.__NUM_INPUT_DATA / self.k_fold_k)
        # data divides evenly
        if num_uneven_sets == 0:
            for k in range(0, self.k_fold_k):
                i = 0
                while (i < set_size):
                    self.__k_folds[k][i] = self.__data[k*set_size + i]
                    i += 1
        else: # uneven sets
            for k in range(0, self.k_fold_k):
                i = 0
                uneven_sets_stored = num_uneven_sets - uneven_sets_remaining
                if uneven_sets_remaining > 0:
                    while (i < set_size + 1):
                        if i == 588:
                            print('set_size {}'.format(set_size))
                        self.__k_folds[k][i] = self.__data[uneven_sets_stored * (set_size+1) + (k-uneven_sets_stored) * (set_size) + i]
                        i += 1
                    # remove one from uneven sets remaining
                    uneven_sets_remaining -= 1
                else: # uneven sets stored
                    while (i < set_size):
                        self.__k_folds[k][i] = self.__data[uneven_sets_stored * (set_size + 1) + (k - uneven_sets_stored) * (set_size) + i]
                        i += 1

        print(self.__data)
        print(self.__data_labels)

    def __replace_categorical_data(self):
        for row in self.__data:
            row[1] = self.__replace_job(row[1])
            row[2] = self.__replace_marital(row[2])
            row[3] = self.__replace_education(row[3])
            row[4] = self.__replace_default(row[4])
            row[5] = self.__replace_housing(row[5])
            row[6] = self.__replace_loan(row[6])
            row[7] = self.__replace_y(row[7])

    def __replace_job(self, job_str):
        #job: type of job(categorical: "admin.", "blue-collar", "entrepreneur", "housemaid", "management",
        # "retired", "self-employed", "services", "student", "technician", "unemployed", "unknown")
        if job_str == 'admin':
            return Bank_Data_Enum.Job.ADMIN.value
        elif job_str == 'blue-collar':
            return Bank_Data_Enum.Job.BLUE_COLLAR.value
        elif job_str == 'entrepreneur':
            return Bank_Data_Enum.Job.ENTREPRENEUR.value
        elif job_str == 'housemaid':
            return Bank_Data_Enum.Job.HOUSEMAID.value
        elif job_str == 'management':
            return Bank_Data_Enum.Job.MANAGEMENT.value
        elif job_str == 'retired':
            return Bank_Data_Enum.Job.RETIRED.value
        elif job_str == 'self-employed':
            return Bank_Data_Enum.Job.SELF_EMPLOYED.value
        elif job_str == 'services':
            return Bank_Data_Enum.Job.SERVICES.value
        elif job_str == 'student':
            return Bank_Data_Enum.Job.STUDENT.value
        elif job_str == 'technician':
            return Bank_Data_Enum.Job.TECHNICIAN.value
        elif job_str == 'unemployed':
            return Bank_Data_Enum.Job.UNEMPLOYED.value
        else:
            return Bank_Data_Enum.Job.UNKNOWN.value

    def __replace_marital(self, marital_str):
        # marital : marital status (categorical: "divorced","married","single","unknown";
        if marital_str == 'divorced':
            return Bank_Data_Enum.Marital.DIVORCED.value
        elif marital_str == 'married':
            return Bank_Data_Enum.Marital.MARRIED.value
        elif marital_str == 'single':
            return Bank_Data_Enum.Marital.SINGLE.value
        else:
            return Bank_Data_Enum.Marital.UNKNOWN.value

    def __replace_education(self, education_str):
        # education (categorical: "basic.4y","basic.6y","basic.9y","high.school",
        # "illiterate","professional.course","university.degree","unknown")
        if education_str == 'basic.4y':
            return Bank_Data_Enum.Education.BASIC_4Y.value
        elif education_str == 'basic.6y':
            return Bank_Data_Enum.Education.BASIC_6Y.value
        elif education_str == 'basic.9y':
            return Bank_Data_Enum.Education.BASIC_9Y.value
        elif education_str == 'high.school':
            return Bank_Data_Enum.Education.HIGH_SCHOOL.value
        elif education_str == 'illiterate':
            return Bank_Data_Enum.Education.ILLITERATE.value
        elif education_str == 'professional.course':
            return Bank_Data_Enum.Education.PROFESSIONAL_COURSE.value
        elif education_str == 'university.degree':
            return Bank_Data_Enum.Education.UNIVERSITY_DEGREE.value
        else:
            return Bank_Data_Enum.Education.UNKNOWN.value

    def __replace_default(self, default_str):
        # default: has credit in default? (categorical: "no","yes","unknown")
        if default_str == 'no':
            return Bank_Data_Enum.Default.NO.value
        elif default_str == 'yes':
            return Bank_Data_Enum.Default.YES.value
        else:
            return Bank_Data_Enum.Default.UNKNOWN.value

    def __replace_housing(self, housing_str):
        # housing: has housing loan? (categorical: "no","yes","unknown")
        if housing_str == 'no':
            return Bank_Data_Enum.Housing.NO.value
        elif housing_str == 'yes':
            return Bank_Data_Enum.Housing.YES.value
        else:
            return Bank_Data_Enum.Housing.UNKNOWN.value

    def __replace_loan(self, loan_str):
        # loan: has personal loan? (categorical: "no","yes","unknown")
        if loan_str == 'no':
            return Bank_Data_Enum.Loan.NO.value
        elif loan_str == 'yes':
            return Bank_Data_Enum.Loan.YES.value
        else:
            return Bank_Data_Enum.Loan.UNKNOWN.value

    def __replace_y(self, y_str):
        if y_str == 'yes':
            return Bank_Data_Enum.Y.YES.value
        else:
            return Bank_Data_Enum.Y.NO.value

    def __calc_distance(self, v1, v2):
        delta = distance.euclidean(v1[0:7], v2[0:7])
        if self.__debug:
            print('KNN_Classifier.__calc_distance(v1, v2):')
            print('v1: ' + str(v1[0:7]))
            print('v2: ' + str(v2[0:7]))
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
            '''
            print('Delta: ' + str(delta))
            print('k_neighbors: ' + str(k_neighbors))
            print('k_neighbors_delta: ' + str(k_neighbors_delta))
            print('furthest_neighbor_delta: ' + str(furthest_neighbor_delta))
            print('furthest_neighbor_index: ' + str(furthest_neighbor_index))
            '''
            if num_entries < self.k:
                k_neighbors[num_entries] = classifier_entry[7]
                k_neighbors_delta[num_entries] = delta
                num_entries += 1
            elif delta < furthest_neighbor_delta:
                k_neighbors[furthest_neighbor_index] = classifier_entry[7]
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
            if k_neighbors[i] == Bank_Data_Enum.Y.YES.value:
                yes += 1
            elif k_neighbors[i] == Bank_Data_Enum.Y.NO.value:
                no += 1
            else:
                raise Exception("Invalid k_neighbors value found at index " + str(i) + ' k_neighbors value: ' + str(k_neighbors))

        # assume odd
        if yes > no:
            return Bank_Data_Enum.Y.YES.value
        else:
            return Bank_Data_Enum.Y.NO.value

    def classify_data(self, input_data, num_vals):
        if len(input_data[0]) != 7 and len(input_data[0]) != 8:
            raise Exception('Invalid data dimensions: n x 7 required')

        classified_data = numpy.empty([num_vals])

        for i in range(0, num_vals):
            k_neighbors = self.__calc_k_neighbors(input_data[i])
            classification = self.__get_neighbor_classification(k_neighbors.astype(int))
            classified_data[i] = classification
            print("Step %d of %d" % (i+1, num_vals))


        if self.__debug:
            print('Output of KNN_Classifier.classified_data: ' + str(classified_data.astype(int)))

        return classified_data.astype(int)

    def k_fold_analysis(self):
        num_uneven_sets = self.__NUM_INPUT_DATA % self.k_fold_k
        outputs = []
        accuracies = []
        if num_uneven_sets == 0:
            for k in range(0, self.k_fold_k):
                print('Train set: {}'.format(k+1))
                # test set is k
                test_set = self.__k_folds[k]
                train = []
                for i in range(0, self.k_fold_k):
                    if i == k:
                        continue # skip the test set
                    for j in range(0, len(self.__k_folds[i])):
                        #print('i: ' + str(i) + ' j: ' + str(j))
                        train.append(self.__k_folds[i][j])
                self.__data = numpy.array(train)
                outputs.append(self.classify_data(test_set, len(test_set)))
                print('Output: ' + str(outputs[k]))

                # get accuracies
                correctly_classified = 0
                for i in range(0,len(self.__k_folds[0])):
                    if self.__k_folds[k][i][7] == outputs[k][i]:
                        correctly_classified += 1
                accuracies.append(correctly_classified/len(self.__k_folds[0]))

        else: # uneven sets
            for k in range(0, self.k_fold_k):
                print('Train set: {}'.format(k+1))
                # test set is k
                test_set = self.__k_folds[k]
                train = []
                for i in range(0, self.k_fold_k):
                    if i == k:
                        continue # skip the test set
                    for j in range(0, len(self.__k_folds[i])):
                        #print('i: ' + str(i) + ' j: ' + str(j))
                        train.append(self.__k_folds[i][j])
                self.__data = numpy.array(train)
                if k <= num_uneven_sets-1: # if set has extra data point
                    outputs.append(self.classify_data(test_set, len(test_set)))
                else: # skip last data point
                    outputs.append(self.classify_data(test_set, len(test_set)-1))
                print('Output: ' + str(outputs[k]))

                # get accuracies
                correctly_classified = 0
                for i in range(0, len(self.__k_folds[0])):
                    if k > num_uneven_sets-1 and i == len(test_set)-1:
                        break
                    if self.__k_folds[k][i][7] == outputs[k][i]:
                        correctly_classified += 1
                if k <= num_uneven_sets-1:
                    accuracies.append(correctly_classified / len(self.__k_folds[0]))
                else:
                    accuracies.append(correctly_classified / (len(self.__k_folds[0])-1))

        for k in range(0,self.k_fold_k):
            print('Accuracy of train_set: {} is {:.2f}'.format(k, accuracies[k]))

        print('K Fold Cross Validation Model Analysis: {:.2f}'.format(numpy.average(accuracies)))