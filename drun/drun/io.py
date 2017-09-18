import dill

from drun.model import ScipyModel


def export(filename, prepare, apply, version):
    """
    Exports simple Pandas based model as a bundle
    :param filename: the location to write down the model
    :param prepare: a function to prepare input DF->DF
    :param apply: an apply function DF->DF
    :param version: version designator (optional)
    :return:
    """
    model = ScipyModel(apply=apply,
                       types=None,
                       prepare=prepare,
                       version=version)

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

    assert isinstance(model, model.MLModel)
