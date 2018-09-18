import time
import legion.pymodel.store

STORE = legion.pymodel.store.SharedStore('complex-model-store')
STORE.time_marker = int(time.time())
