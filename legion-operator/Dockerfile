# Load dependencies
FROM instrumentisto/dep:0.5 as fetcher
WORKDIR /go/src/github.com/legion-platform/legion/legion-operator
COPY Gopkg.lock \
     Gopkg.toml \
       ./
RUN dep ensure --vendor-only

# Build the manager binary
FROM golang:1.10.3 as builder

# Copy in the go src
WORKDIR /go/src/github.com/legion-platform/legion/legion-operator
# Copy requirements from prev. layer
COPY --from=fetcher /go/src/github.com/legion-platform/legion/legion-operator/vendor/ vendor/
# Download kubebuilder binaries for testing purposes
ADD https://github.com/kubernetes-sigs/kubebuilder/releases/download/v1.0.8/kubebuilder_1.0.8_linux_amd64.tar.gz /temp/kubebuilder.tar.gz
RUN tar -zxvf /temp/kubebuilder.tar.gz -C /usr/local/ && mv /usr/local/kubebuilder_* /usr/local/kubebuilder
# Copy source code
COPY pkg/    pkg/
COPY cmd/    cmd/
COPY config/    config/

# Run tests
RUN go test ./pkg/... ./cmd/... -coverprofile cover.out

# Build
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -o manager github.com/legion-platform/legion/legion-operator/cmd/manager

# Copy the controller-manager into a thin image
FROM alpine:3.6
WORKDIR /
COPY --from=builder /go/src/github.com/legion-platform/legion/legion-operator/manager .
ENTRYPOINT ["/manager"]
