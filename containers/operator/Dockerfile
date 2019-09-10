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

ENV OPERATOR_DIR="/go/src/github.com/legion-platform/legion/legion/operator"
ENV GOPATH="/go"
ENV PATH "$PATH:/go/bin:/usr/lib/go-1.11/bin"
WORKDIR "${OPERATOR_DIR}"

RUN apt-get update -qq && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:gophers/archive && \
    apt-get update -qq && \
    apt-get install -y git gcc make golang-1.11-go wget && \
    wget https://github.com/golangci/golangci-lint/releases/download/v1.17.1/golangci-lint-1.17.1-linux-amd64.tar.gz -O /tmp/golangci-lint.tar.gz && \
    tar -zxvf /tmp/golangci-lint.tar.gz -C /usr/local/ && mv /usr/local/golangci-lint*/golangci-lint /usr/bin/golangci-lint && \
    wget https://github.com/golang/dep/releases/download/v0.5.1/dep-linux-amd64 -O /usr/local/bin/dep && \
    chmod +x /usr/local/bin/dep && \
    wget https://github.com/kubernetes-sigs/kubebuilder/releases/download/v1.0.8/kubebuilder_1.0.8_linux_amd64.tar.gz -O /tmp/kubebuilder.tar.gz && \
    tar -zxvf /tmp/kubebuilder.tar.gz -C /usr/local/ && mv /usr/local/kubebuilder_* /usr/local/kubebuilder && \
    wget https://github.com/swaggo/swag/releases/download/v1.5.0/swag_1.5.0_Linux_x86_64.tar.gz -O /tmp/swag.tar.gz && \
    tar -zxvf /tmp/swag.tar.gz -C /usr/local/ && mv /usr/local/swag /usr/bin/ && \
    wget https://github.com/gotestyourself/gotestsum/releases/download/v0.3.4/gotestsum_0.3.4_linux_amd64.tar.gz -O /tmp/gotestsum.tar.gz && \
    tar -zxvf /tmp/gotestsum.tar.gz -C /usr/local/ && mv /usr/local/gotestsum* /usr/bin/gotestsum && \
    go get github.com/t-yuki/gocover-cobertura

COPY legion/operator/Gopkg.toml legion/operator/Gopkg.lock ./
RUN dep ensure -vendor-only

COPY legion/operator/ ./

RUN GOOS=linux GOARCH=amd64 make build-all && (make test ; make LINTER_ADDITIONAL_ARGS='--out-format checkstyle > linter-output.xml' lint || true)

#########################################################
#########################################################
#########################################################

FROM ubuntu:18.04 as operator

ENV LEGION_DIR="/opt/legion"
RUN  apt-get -yq update && \
     apt-get -yqq install openssh-client

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

RUN apt-get update && apt-get install -y ca-certificates

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/operator/service-catalog "${LEGION_DIR}/"
COPY legion/operator/templates "${TEMPLATE_FOLDER}/"

WORKDIR "${LEGION_DIR}"
CMD ["./edi"]

#########################################################
#########################################################
#########################################################

FROM ubuntu:18.04 as model-trainer

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LANGUAGE C:en
ENV LC_ALL C.UTF-8

ENV WORK_DIR="/opt/legion"
WORKDIR "${WORK_DIR}/"

RUN apt-get update -qq && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:projectatomic/ppa && \
    apt-get update -qq && \
    apt-get -qq -y install runc buildah iptables libdevmapper-event1.02.1 uidmap

COPY containers/operator/registries.conf \
     containers/operator/storage.conf \
     /etc/containers/

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/operator/trainer "${WORK_DIR}/"

CMD ["./trainer"]

#########################################################
#########################################################
#########################################################

FROM ubuntu:18.04 as model-packager

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LANGUAGE C:en
ENV LC_ALL C.UTF-8

ENV WORK_DIR="/opt/legion"
WORKDIR "${WORK_DIR}/"

RUN apt-get update -qq && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:projectatomic/ppa && \
    apt-get update -qq && \
    apt-get -qq -y install runc buildah iptables libdevmapper-event1.02.1 uidmap

COPY containers/operator/registries.conf \
     containers/operator/storage.conf \
     /etc/containers/

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/operator/packager "${WORK_DIR}/"

CMD ["./packager"]
