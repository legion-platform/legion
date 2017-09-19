import dill

from drun.model import ScipyModel, IMLModel


def export(filename, apply_func, prepare_func=None, param_types=None, version=None):
    """
    Exports simple Pandas based model as a bundle
    :param filename: the location to write down the model
    :param apply_func: an apply function DF->DF
    :param prepare_func: a function to prepare input DF->DF
    :param param_types:
    :return:
    """
    if prepare_func is None:
        prepare_func = lambda x : x

    model = ScipyModel(apply_func=apply_func,
                       column_types=param_types,
                       prepare_func=prepare_func,
                       version=None)

    with open(filename, 'wb') as f:
        dill.dump(model, f, recurse=True)


def load_model(filename):
    """
    Loads a model bundle from the given file
    :param filename: A name of the model bundle
    :return: an implementation of drun.model.IMLModel
    """
    with open(filename, 'rb') as f:
        model = dill.load(f)
        return model
