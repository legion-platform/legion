#
#   Copyright 2018 EPAM Systems
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
FROM python:3.6-alpine3.7@sha256:386ecd80510e1ebecbca17b2efa74f3029fa7dce882b5132cf6ee3bd17cf108a

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

ARG model_id="demo-abc-model"
ARG model_version="1.0"

LABEL com.epam.legion.model.id="$model_id" \
      com.epam.legion.model.version="$model_version" \
      com.epam.legion.container_type="model"

ENTRYPOINT ["python"]
CMD ["app.py"]