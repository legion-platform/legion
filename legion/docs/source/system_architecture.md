# System architecture
legion contains of many docker containers, including next:
* [graphite](grafana_and_graphite.md) - for saving model timings
* [grafana](grafana_and_graphite.md) - with GUI for model timings
* [jenkins](jenkins.md) - for running model tests
* [edge](edge.md) - with Nginx server for handling all requests
