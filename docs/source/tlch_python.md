# Python toolchain

Legion's Python toolchain (SDK) allows to create ML models for Legion platform. It exposes API ([described below](#toolchain-api)) to developers.

## Toolchain API

Each API method uses or changes "Legion Model Context". Context stores information about model, its endpoints, train metrics and other train information.

### General
* `init(model_id: str, model_version: str)` - initializes context of model training. Should be called before any other API method. Can be called once (or after `reset_context`). Returns nothing.
* `get_context()` - returns current state of context as object, depending of realization. **Context should be initialized before.**
* `reset_context()` - resets context object. `init` should be called later (before any other API method).
* `save()` - saves model to file system. It captures context of exported functions and serializes them. **Context should be initialized before, at least one function should be exported.**

### Metrics
**Context should be initialized before calling any of these functions.**
* `send_metric(metric: str, value: float or int)` - sends training metric (e.g. accuracy of trained model). Metrics with same name can be sent only once.

### Export
**Context should be initialized before calling any of these functions.**
Exporting functions allows expose model predictions, defined as functions, as API methods. `apply_func` - function that receives prediction parameters (details in function specification) and returns json-serializable object (like dictionary) to API client. `prepare_func` - optional function, that is called before apply function, if defined. `endpoint` - name of exported endpoint, model may have more then one endpoint. By default endpoint name equals to `"default"`.
* `export_df(apply_func, input_data_frame, prepare_func, endpoint: str)` - exports `apply_func` and `prepare_func` functions that take pandas'es DataFrame as input. `input_data_frame` should be DataFrame with structure similar to input format (Legion validates that input has same structure as `input_data_frame`). `endpoint` - name of exported endpoint, described above.
* `export(apply_func, column_types, prepare_func, endpoint: str)` - exports `apply_func` and `prepare_func` functions that take dictionary as input. `column_types` should be Python's map with keys equal to name of parameters and values that are instances of `legion.model.types.ColumnInformation` (see [supported types](#supported-types)). `endpoint` - name of exported endpoint, described above.
* `export_untyped(apply_func, prepare_func, endpoint: str)` - exports `apply_func` and `prepare_func` functions that take dictionary as input. `endpoint` - name of exported endpoint, described above.

## Supported types
For `export` function Legion provides built-in types, that could be chosen without implementing custom types (custom types are also possible).

* `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`, `int64`, `uint64` - that are wrappers around appropriate NumPy's types
* `float16`, `float32`, `float64` - that are wrappers around appropriate NumPy's types
* `string`, `boolean` - that are wrappers around standard Python's types
* `image` - that allows to send image as string (base64), url (URL of image on external resource) or bytes (image file)

## Examples
1. Exports API with endpoint `default` that takes one argument (`image`) and calls `predict` function for prediction:

```python
from legion.toolchain import model
model.init('test-model', '1.0')  # initialize model with id=test-model and version=1.0

# ... prepare model, results are accuracy_value and predict function

model.send_metric('accuracy', accuracy_value)  # send training metrics

model.export(lambda x: predict(x), {'image': model.image})

model.save()
```

2. Exports API with endpoint `clsf` that takes arguments as in data frame `features_data` and calls `predict` function of scikit's DecisionTreeClassifier for prediction:

```python
from legion.toolchain import model
model.init('classifier-1', '1.2')  # initialize model with id=classifier-1 and version=1.2

clf = DecisionTreeClassifier(max_depth=8)
clf.fit(X=X_train, y=y_train)
model.export_df(apply_func=lambda x : {'result': int(clf.predict(x)[0]) },
                prepare_func=lambda x : prepare(x),
                input_data_frame=features_data)
model.save()
```

For more examples please refer [examples folder](https://github.com/legion-platform/legion/tree/develop/examples).
