#
#    Copyright 2017 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
from __future__ import print_function

import legion.model

import pandas


def create_simple_summation_model_by_df(model_id, model_version, path):
    def apply(x):
        a = x.iloc[0]['a']
        b = x.iloc[0]['b']
        return {'x': int(a + b)}

    df = pandas.DataFrame([{
        'a': 1,
        'b': 1,
    }])

    return legion.model.init(model_id, model_version).export_df(apply, df).save(path)


def create_simple_summation_model_by_df_with_prepare(model_id, model_version, path):
    def prepare(x):
        return {
            'a': x.iloc[0]['a'],
            'b': x.iloc[0]['b']
        }

    def apply(x):
        return {'x': int(x['a'] + x['b'])}

    df = pandas.DataFrame([{
        'a': 1,
        'b': 1,
    }])

    legion.model.init(model_id, model_version)
    legion.model.define_property('abc', 20.234)

    return legion.model.export_df(apply, df).save(path)


def create_simple_summation_model_by_types(model_id, model_version, path):
    def apply(x):
        return {'x': int(x['a'] + x['b'])}

    parameters = {
        'a': legion.model.int32,
        'b': legion.model.int32,
    }

    return legion.model.init(model_id, model_version).export(apply, parameters).save(path)


def create_simple_summation_model_untyped(model_id, model_version, path):
    def apply(x):
        keys = sorted(tuple(x.keys()))

        return {'keys': ','.join(keys), 'sum': sum(int(val) for val in x.values())}

    return legion.model.init(model_id, model_version).export_untyped(apply).save(path)


def create_simple_summation_model_lists(model_id, model_version, path):
    def apply(x):
        movie_matrix = dict(zip(x['movie'], x['rate']))

        best = max(movie_matrix, key=movie_matrix.get)
        worth = min(movie_matrix, key=movie_matrix.get)

        return {'best': best, 'worth': worth}

    return legion.model.init(model_id, model_version).export_untyped(apply).save(path)


def create_simple_summation_model_lists_with_files_info(model_id, model_version, path):
    def apply(x):
        movie_matrix = {}

        for file in x['file']:
            name, rate = file.decode('utf-8').strip().split('\n')
            movie_matrix[name] = rate

        best = max(movie_matrix, key=movie_matrix.get)
        worth = min(movie_matrix, key=movie_matrix.get)

        return {'best': best, 'worth': worth}

    return legion.model.init(model_id, model_version).export_untyped(apply).save(path)
