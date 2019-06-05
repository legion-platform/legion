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

FROM golang:1.11.6-alpine3.9 as builder

ENV FEEDBACK_DIR="/go/src/github.com/legion-platform/legion/legion/feedback-aggregator"
WORKDIR "${FEEDBACK_DIR}"

RUN apk add -u ca-certificates git gcc musl-dev make && \
    wget https://github.com/golang/dep/releases/download/v0.5.1/dep-linux-amd64 -O /usr/local/bin/dep && \
    chmod +x /usr/local/bin/dep && \
    wget https://github.com/gotestyourself/gotestsum/releases/download/v0.3.4/gotestsum_0.3.4_linux_amd64.tar.gz -O /tmp/gotestsum.tar.gz && \
    tar -zxvf /tmp/gotestsum.tar.gz -C /usr/local/ && mv /usr/local/gotestsum* /usr/bin/gotestsum && \
    go get github.com/t-yuki/gocover-cobertura

COPY legion/feedback-aggregator/Gopkg.toml legion/feedback-aggregator/Gopkg.lock ./
RUN dep ensure -vendor-only

COPY legion/feedback-aggregator/ ./

RUN GOOS=linux GOARCH=amd64 make build && make test

#########################################################
#########################################################
#########################################################

FROM alpine:3.9 as server

ENV LEGION_DIR="/opt/legion"

WORKDIR "${LEGION_DIR}"
COPY --from=builder /go/src/github.com/legion-platform/legion/legion/feedback-aggregator/feedback ./
CMD ["./feedback"]

#########################################################
#########################################################
#########################################################