# System architecture
legion contains of many docker containers, including next:
* [jupyter](jupyter.md) - with Jupyter notebook
* [legion](legion.md) - with default model HTTP handler
* [graphite](grafana_and_graphite.md) - for saving model timings
* [grafana](grafana_and_graphite.md) - with GUI for model timings
* [jenkins](jenkins.md) - for running model tests
* [edge](edge.md) - with Nginx server for handling all requests
* [consul](consul.md) - for controlling on configuration
