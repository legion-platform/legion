#
#    Copyright 2019 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

FROM ubuntu:18.04 as builder

ENV OPERATOR_DIR="/go/src/github.com/legion-platform/legion/legion/operator" \
    PATH="$PATH:/go/bin:/usr/lib/go-1.12/bin" \
    GOPATH="/go"

WORKDIR "${OPERATOR_DIR}"

RUN apt-get update -qq && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:longsleep/golang-backports && \
    apt-get update -qq && \
    apt-get install -y git gcc make golang-1.12-go wget && \
    wget -q https://github.com/golangci/golangci-lint/releases/download/v1.17.1/golangci-lint-1.17.1-linux-amd64.tar.gz -O /tmp/golangci-lint.tar.gz && \
    tar -zxvf /tmp/golangci-lint.tar.gz -C /usr/local/ && mv /usr/local/golangci-lint*/golangci-lint /usr/bin/golangci-lint && \
    wget -q https://github.com/golang/dep/releases/download/v0.5.1/dep-linux-amd64 -O /usr/local/bin/dep && \
    chmod +x /usr/local/bin/dep && \
    wget -q https://github.com/kubernetes-sigs/kubebuilder/releases/download/v1.0.8/kubebuilder_1.0.8_linux_amd64.tar.gz -O /tmp/kubebuilder.tar.gz && \
    tar -zxvf /tmp/kubebuilder.tar.gz -C /usr/local/ && mv /usr/local/kubebuilder_* /usr/local/kubebuilder && \
    wget -q https://github.com/swaggo/swag/releases/download/v1.6.3/swag_1.6.3_Linux_x86_64.tar.gz -O /tmp/swag.tar.gz && \
    tar -zxvf /tmp/swag.tar.gz -C /usr/local/ && mv /usr/local/swag /usr/bin/ && \
    wget -q https://github.com/gotestyourself/gotestsum/releases/download/v0.3.4/gotestsum_0.3.4_linux_amd64.tar.gz -O /tmp/gotestsum.tar.gz && \
    tar -zxvf /tmp/gotestsum.tar.gz -C /usr/local/ && mv /usr/local/gotestsum* /usr/bin/gotestsum && \
    go get github.com/t-yuki/gocover-cobertura

COPY legion/operator/Gopkg.toml legion/operator/Gopkg.lock ./
RUN dep ensure -v -vendor-only

COPY legion/operator/ ./

RUN GOOS=linux GOARCH=amd64 make build-all && (make test ; make LINTER_ADDITIONAL_ARGS='> linter-output.txt' lint || true)

#########################################################
#########################################################
#########################################################

FROM ubuntu:18.04 as operator

ENV LEGION_DIR="/opt/legion"
RUN  apt-get -yq update && \
     apt-get -yqq install ca-certificates

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/operator/operator "${LEGION_DIR}/"
WORKDIR "${LEGION_DIR}"
CMD ["./operator"]

#########################################################
#########################################################
#########################################################

FROM ubuntu:18.04 as edi

ENV LEGION_DIR="/opt/legion" \
    TEMPLATE_FOLDER="/opt/legion/templates" \
    GIN_MODE="release"
RUN  apt-get -yq update && \
     apt-get -yqq install openssh-client ca-certificates

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/operator/edi "${LEGION_DIR}/"
COPY legion/operator/templates "${TEMPLATE_FOLDER}/"

WORKDIR "${LEGION_DIR}"
CMD ["./edi"]

#########################################################
#########################################################
#########################################################

FROM ubuntu:18.04 as service-catalog

ENV LEGION_DIR="/opt/legion" \
    TEMPLATE_FOLDER="/opt/legion/templates" \
    GIN_MODE="release"

RUN  apt-get -yq update && \
     apt-get -yqq install ca-certificates

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/operator/service-catalog "${LEGION_DIR}/"
COPY legion/operator/templates "${TEMPLATE_FOLDER}/"

WORKDIR "${LEGION_DIR}"
CMD ["./edi"]

#########################################################
#########################################################
#########################################################

FROM ubuntu:18.04 as model-trainer

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 LANGUAGE=en_US.UTF-8 \
    WORK_DIR="/opt/legion"

WORKDIR "${WORK_DIR}/"

RUN  apt-get -yq update && \
     apt-get -yqq install ca-certificates

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/operator/trainer "${WORK_DIR}/"

CMD ["./trainer"]

#########################################################
#########################################################
#########################################################

FROM ubuntu:18.04 as model-packager

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 LANGUAGE=en_US.UTF-8 \
    WORK_DIR="/opt/legion"

RUN  apt-get -yq update && \
     apt-get -yqq install ca-certificates

WORKDIR "${WORK_DIR}/"

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/operator/packager "${WORK_DIR}/"

CMD ["./packager"]
