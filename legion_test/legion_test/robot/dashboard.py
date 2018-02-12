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
"""
Robot test library - kubernetes dashboard
"""
import requests
import json

requests.packages.urllib3.disable_warnings()

API_ENDPOINT = '/api/v1/workload/{namespace}?filterBy=&itemsPerPage=15&name=&page=1&sortBy=d,creationTimestamp'


class Dashboard:
    """
    Kubernetes dashboard client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self):
        """
        Init client
        """
        self._information = None

    def gather_kubernetes_dashboard_info(self, domain, namespace):
        """
        Gather dashboard information through HTTP/HTTPS

        :param domain: dashboard host
        :type domain: str
        :param namespace: target kubernetes namespace
        :type namespace: str
        :return: str -- url from which information has been gathered
        """
        url = domain + API_ENDPOINT.format(namespace=namespace)
        result = requests.get(url, verify=False)
        data = result.text
        try:
            self._information = json.loads(data)
        except Exception as json_decode_exception:
            print('Data: {}'.format(data))
            raise

        return url

    def _get_resource_by_name(self, name, *levels):
        """
        Get specific resource information from already gathered data

        :param name: resource name
        :type name: str
        :param levels: keys in JSON tree to locate resource list
        :type levels: list[str] -- keys in JSON tree
        :raises Exception
        :return: dict -- part of JSON tree with resource
        """
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
        """
        Check that all resource pods is running (no one pending or failed pod)

        :param object_information: part of JSON tree with resource
        :type object_information: dict
        :raises: Exception
        :return: None
        """
        pods_state = object_information.get('pods')
        if pods_state.get('pending') != 0 or pods_state.get('failed') != 0:
            raise Exception('Some pods failed or pending')

    def replica_set_is_running(self, replica_set_name):
        """
        Check that specific named replica set is okay (no one pending or failed pod)

        :param replica_set_name: name of replica set
        :type replica_set_name: str
        :raises: Exception
        :return: None
        """
        if not self._information:
            raise Exception('Information has not been gathered')

        replica_set = self._get_resource_by_name(replica_set_name, 'replicaSetList', 'replicaSets')
        self._check_resource_pods(replica_set)

    def stateful_set_is_running(self, stateful_set_name):
        """
        Check that specific named stateful set is okay (no one pending or failed pod)

        :param stateful_set_name: name of stateful set
        :type stateful_set_name: str
        :raises: Exception
        :return: None
        """
        if not self._information:
            raise Exception('Information has not been gathered')

        replica_set = self._get_resource_by_name(stateful_set_name, 'statefulSetList', 'statefulSets')
        self._check_resource_pods(replica_set)

    def replication_controller_is_running(self, replication_controller_name):
        """
        Check that specific named replication controller is okay (no one pending or failed pod)

        :param replication_controller_name: name of replication controller
        :type replication_controller_name: str
        :raises: Exception
        :return: None
        """
        if not self._information:
            raise Exception('Information has not been gathered')

        replica_set = self._get_resource_by_name(replication_controller_name, 'replicationControllerList', 'replicationControllers')
        self._check_resource_pods(replica_set)
