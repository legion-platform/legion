#!/usr/bin/env bash
#
#   Copyright 2017 EPAM Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

cd base-python-image
docker build -t legion/base-python-image:latest .
cd ..

cd edge
docker build -t legion/edge .
cd ..

cd grafana
docker build -t legion/grafana .
cd ..

cd jenkins
docker build -t legion/jenkins-server:latest .
cd ..
