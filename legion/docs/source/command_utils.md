# Utils

Legion project contains several Command Line utilities:

* **check_jenkins_jobs** is used for triggering Jenkins jobs remotely.

```bash
usage: check_jenkins_jobs [-h] [--jenkins-url JENKINS_URL]
                           [--jenkins-user JENKINS_USER]
                           [--jenkins-password JENKINS_PASSWORD]
                           [--jenkins-run-job JENKINS_RUN_JOB]
                           [--jenkins-run-jobs-prefix JENKINS_RUN_JOBS_PREFIX]
                           [--jenkins-check-job-prefix JENKINS_CHECK_JOB_PREFIX]
                           [--jenkins-check-running-jobs]
                           [--connection-timeout CONNECTION_TIMEOUT]
                           [--socket-timeout SOCKET_TIMEOUT]
                           [--socket-reconnect-sleep SOCKET_RECONNECT_SLEEP]
                           [--run-sleep-sec RUN_SLEEP_SEC]
                           [--iterate-sleep-sec ITERATE_SLEEP_SEC]
                           [--run-timeout RUN_TIMEOUT]
                           [--run-parameter RUN_PARAMETER]

optional arguments:
  -h, --help            show this help message and exit
  --jenkins-url JENKINS_URL
  --jenkins-user JENKINS_USER
  --jenkins-password JENKINS_PASSWORD
  --jenkins-run-job JENKINS_RUN_JOB
                        Run Jenkins Job with specific name
  --jenkins-run-jobs-prefix JENKINS_RUN_JOBS_PREFIX
                        Run Jenkins Jobs with specific name prefix
  --jenkins-check-job-prefix JENKINS_CHECK_JOB_PREFIX
                        Check result of Jenkins Jobs with specific name prefix
  --jenkins-check-running-jobs
                        Check running jobs
  --connection-timeout CONNECTION_TIMEOUT
                        Timeout in sec. for first connection
  --socket-timeout SOCKET_TIMEOUT
                        Connection socket timeout in sec.
  --socket-reconnect-sleep SOCKET_RECONNECT_SLEEP
                        Sleep in sec. between reconnection on start
  --run-sleep-sec RUN_SLEEP_SEC
                        Sleep in sec. after start of job
  --iterate-sleep-sec ITERATE_SLEEP_SEC
                        Sleep in sec. between check of jobs status
  --run-timeout RUN_TIMEOUT
                        Timeout in sec. to finish all jobs
  --run-parameter RUN_PARAMETER
                        Parameters for passing to Jenkins run command
```

* **copyright_scanner** scans files in a path for copyrights and prints them out.

```bash
usage: copyright_scanner [-h] path

Copyright scanner

positional arguments:
  path        path to directory

optional arguments:
  -h, --help  show this help message and exit
```

* **create_example_jobs** is used to import Jenkins jobs into remote Jenkins Server.

```bash
usage: create_example_jobs [-h] [--git-root-key GIT_ROOT_KEY]
                           [--model-host MODEL_HOST]
                           [--jenkins-user JENKINS_USER]
                           [--jenkins-password JENKINS_PASSWORD]
                           [--dynamic-model-prefix DYNAMIC_MODEL_PREFIX]
                           [--perf-test-prefix PERF_TEST_PREFIX]
                           [--connection-timeout CONNECTION_TIMEOUT]
                           [--socket-reconnect-sleep SOCKET_RECONNECT_SLEEP]
                           [--plain-tasks]
                           jenkins_url base_directory git_directory git_url
                           git_branch
```

* **legion_bootstrap_grafana** is used in Grafana Docker image, links Grafana to Graphite storage, creates a Grafana dashboard and other setup.

```bash
usage: legion_bootstrap_grafana [-h] [--user USER] [--password PASSWORD]
                           [--connection-timeout CONNECTION_TIMEOUT]
                           [--socket-reconnect-sleep SOCKET_RECONNECT_SLEEP]
                           base_url graphite_ds_url

positional arguments:
  base_url              Base server url
  graphite_ds_url       Graphite Data Source url

optional arguments:
  -h, --help            show this help message and exit
  --user USER           Server user
  --password PASSWORD   Server password
  --connection-timeout CONNECTION_TIMEOUT
  --socket-reconnect-sleep SOCKET_RECONNECT_SLEEP
```

* **update_version_id** generates Legion version ID based on time, build ID, commit ID.

```bash
usage: update_version_id [-h] [--build-id BUILD_ID] [--use-full-commit-id]
                         [--extended-output]
                         version_file

Version file updater (adds time, build id, commit id to version)

positional arguments:
  version_file          Path to version file

optional arguments:
  -h, --help            show this help message and exit
  --build-id BUILD_ID   Override build id. Default from env.BUILD_NUMBER
  --use-full-commit-id  Use full git sha commits
  --extended-output     Output to stdout extended information
```