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

import legion.io

import pandas


def create_simple_summation_model_by_df(path, version):
    def prepare(x):
        return x

    def apply(x):
        a = x.iloc[0]['a']
        b = x.iloc[0]['b']
        return {'x': int(a + b)}

    df = pandas.DataFrame([{
        'a': 1,
        'b': 1,
    }])

    return legion.io.export_df(apply,
                               df,
                               filename=path,
                               prepare_func=prepare,
                               version=version)


def create_simple_summation_model_by_types(path, version):
    pass


def create_simple_summation_model_untyped(path, version):
    pass


def create_simple_summation_model_lists(path, version):
    pass
