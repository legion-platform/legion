import requests

requests.packages.urllib3.disable_warnings()

API_ENDPOINT = '/api/v1/workload/{namespace}?filterBy=&itemsPerPage=15&name=&page=1&sortBy=d,creationTimestamp'


class Dashboard:
    def __init__(self):
        self._information = None

    def gather_kubernetes_dashboard_info(self, domain, namespace):
        url = domain + API_ENDPOINT.format(namespace=namespace)
        result = requests.get(url, verify=False)
        self._information = result.json()

        return url

    def _get_resource_by_name(self, name, *levels):
        local_data = self._information
        for level in levels:
            local_data = local_data.get(level)

        items = {x['objectMeta']['name']: x for x in local_data}

        for item_name, item in items.items():
            if not item_name.startswith(name):
                continue

            if item_name == name or (len(item_name) > len(item) and item_name[len(name)] == '-'):
                return item

        raise Exception('Cannot find {}'.format(name))

    @staticmethod
    def _check_resource_pods(object_information):
        pods_state = object_information.get('pods')
        if pods_state.get('pending') != 0 or pods_state.get('failed') != 0:
            raise Exception('Some pods failed or pending')

    def replica_set_is_running(self, replica_set_name):
        if not self._information:
            raise Exception('Information has not been gathered')

        replica_set = self._get_resource_by_name(replica_set_name, 'replicaSetList', 'replicaSets')
        self._check_resource_pods(replica_set)

    def stateful_set_is_running(self, replica_set_name):
        if not self._information:
            raise Exception('Information has not been gathered')

        replica_set = self._get_resource_by_name(replica_set_name, 'statefulSetList', 'statefulSets')
        self._check_resource_pods(replica_set)

    def replication_controller_is_running(self, replica_set_name):
        if not self._information:
            raise Exception('Information has not been gathered')

        replica_set = self._get_resource_by_name(replica_set_name, 'replicationControllerList', 'replicationControllers')
        self._check_resource_pods(replica_set)
