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

RUN wget https://github.com/golang/dep/releases/download/v0.5.1/dep-linux-amd64 -O /usr/local/bin/dep && \
    chmod +x /usr/local/bin/dep

RUN apk add -u git gcc musl-dev

WORKDIR /go/src/github.com/legion-platform/legion/legion/feedback-aggregator

COPY legion/feedback-aggregator/Gopkg.toml legion/feedback-aggregator/Gopkg.lock ./
RUN dep ensure -vendor-only

COPY legion/feedback-aggregator/pkg/    pkg/
COPY legion/feedback-aggregator/cmd/    cmd/

RUN GOOS=linux GOARCH=amd64 go build -a -o server github.com/legion-platform/legion/legion/feedback-aggregator/cmd

#########################################################
#########################################################
#########################################################

FROM alpine:3.9 as server

ENV LEGION_DIR="/opt/legion"

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/feedback-aggregator/server "${LEGION_DIR}/"
WORKDIR "${LEGION_DIR}"
CMD ["./server"]

#########################################################
#########################################################
#########################################################

FROM golang:1.11.6-alpine3.9 as tests

COPY --from=builder /go/src/github.com/legion-platform/legion/legion/feedback-aggregator/server /go/src/github.com/legion-platform/legion/legion/feedback-aggregator/server
WORKDIR /go/src/github.com/legion-platform/legion/legion/feedback-aggregator
RUN go test ./cmd ./pkg/... -coverprofile cover.out