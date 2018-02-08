from surprise import Dataset, Reader
from surprise import KNNBasic, SVD
from surprise.builtin_datasets import download_builtin_dataset, BuiltinDataset, get_dataset_dir
import surprise.builtin_datasets

from collections import defaultdict
import pandas as pd
import os, io, os.path

import legion.model.model_id
import legion.io
import time

use_built_in = True
legion.model.model_id.init('movie-lens')

surprise.builtin_datasets.BUILTIN_DATASETS['ml-latest-cut'] = BuiltinDataset(
    url='https://s3.us-east-2.amazonaws.com/iqvia-epam-test/ml-latest-cut.zip',
    path=os.path.join(get_dataset_dir(), 'ml-latest-cut/ml-latest-cut/ratings.csv'),
    reader_params=dict(line_format='user item rating timestamp',
                       rating_scale=(1, 5),
                       skip_lines=1,
                       sep=',')
)


class Profiler(object):
    """
    Profile time for functions
    """

    def __init__(self, name='', logger=None):
        """
        Construct profiler
        :param name:
        :param logger:
        :return:
        """
        self._name = name

    def __enter__(self):
        self._start_time = time.time()

    def __exit__(self, type, value, traceback):
        print("Name: " + self._name + " Elapsed time: {:.3f} sec".format(time.time() - self._start_time))


# get item names for built-in 100k dataset
def read_movies_100k():
    """Read the u.item file from MovieLens 100-k dataset and returns a
    mapping to convert raw ids into movie names.
    """
    file_name = (os.path.expanduser('~') +
                 '/.surprise_data/ml-100k/ml-100k/u.item')
    movieData = {}
    with io.open(file_name, 'r', encoding='ISO-8859-1') as f:
        for line in f:
            line = line.split('|')
            movieData[line[0]] = line[1]
    print("Loaded movie ")
    return movieData


# get item names for custom dataset
def read_movies_custom():
    """Read the u.item file from MovieLens custom dataset and returns a
    mapping to convert raw ids into movie names.
    """
    file_name = (os.path.expanduser('~') +
                 '/.surprise_data/ml-latest-cut/ml-latest-cut/movies.csv')
    movies = pd.read_csv(file_name, index_col='movieId')
    movies.index = movies.index.astype(str)
    movieData = movies.title.to_dict()
    print("Loaded movie ")
    return movieData


# get movie data from latest file
def read_movies_latest():
    file_path = os.path.expanduser('~/OneDrive - Quintiles/data/testing/ml-latest/movies.csv')
    movies = pd.read_csv(file_path, index_col='movieId')
    movies.index = movies.index.astype(str)
    movieData = movies.title.to_dict()
    print("Loaded movie ")
    return movieData


# get training data
def get_data():
    # get data
    if use_built_in:
        download_builtin_dataset("ml-latest-cut")
        data = Dataset.load_builtin("ml-latest-cut")
        movie_names = read_movies_custom()
    return data, movie_names


# generate recommendations
def get_top_recommendations(predictions, topN=3):
    try:
        top_recs = defaultdict(list)
        for uid, iid, true_r, est, _ in predictions:
            top_recs[uid].append((iid, est))

        for uid, user_ratings in top_recs.items():
            user_ratings.sort(key=lambda x: x[1], reverse=True)
            top_recs[uid] = user_ratings[:topN]
        print("Generated top movie ")
        return top_recs
    except:
        raise


# run the training
def run_train(trainingSet):
    try:
        # build training set
        # KNN model
        sim_options = {
            'name': 'cosine',
            'user_based': False
        }
        knn = KNNBasic(sim_options=sim_options)
        knn.train(trainingSet)
        return knn
    except:
        raise


# if you want to print top3 call this
def print_recommendations(recommendations):
    for uid, user_ratings in recommendations.items():
        print(uid, [movie_names[iid] for (iid, _) in user_ratings if iid in movie_names])


# limit to top3 recommendations
data, movie_names = get_data()

with Profiler('Training'):
    trainingSet = data.build_full_trainset()
    knn = run_train(trainingSet)

with_optimisation = True

if with_optimisation:
    with Profiler('Generate predictions'):
        recs = {}

        for u in trainingSet.all_users():
            user_items = set([j for (j, _) in trainingSet.ur[u]])
            request = [(trainingSet.to_raw_uid(u), trainingSet.to_raw_iid(i), 0) for
                       i in trainingSet.all_items() if
                       i not in user_items]
            user_predictions = get_top_recommendations(knn.test(request))
            recs[u] = user_predictions


    def parse_input(input):
        return input


    def recommend(input):
        return recs[input['uid']]
else:
    with Profiler('Cross-validation'):
        # get predictions based on training set
        testSet = trainingSet.build_anti_testset()
        testPredictions = knn.test(testSet)

    top3_recommendations = get_top_recommendations(testPredictions)
    print_recommendations(top3_recommendations)


    def parse_input(input):
        return input


    def recommend(input):
        return top3_recommendations[input['uid']]

df = pd.DataFrame([{
    'uid': 1,
}])

legion.io.export(
    prepare_func=lambda x: x,
    apply_func=recommend,
    input_data_frame=df,
    use_df=False,
    version='1.0'
)

# Additional memory workload
file_path = (os.path.expanduser('~') + '/.surprise_data/ml-100k/ml-100k/u.data')
reader = Reader(line_format='user item rating timestamp', sep='\t', skip_lines=0)
data = Dataset.load_from_file(file_path, reader=reader)
