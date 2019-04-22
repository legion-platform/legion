LEGION_OPERATOR_GENERATED_ENTITIES = ../../helms/legion/templates/operator/generated
LEGION_OPERATOR_CRDS = ../../helms/legion-crds/templates

all: manager

# Run tests
test: generate fmt vet manifests
	gotestsum ./pkg/... ./cmd/...

# Build manager binary
manager: generate fmt vet
	go build -o bin/manager github.com/legion-platform/legion/legion/operator/cmd/manager

# Run against the configured Kubernetes cluster in ~/.kube/config
run: generate fmt vet
	go run ./cmd/manager/main.go

# Install CRDs into a cluster
install: manifests
	kubectl apply -f config/crds

# Generate manifests e.g. CRD, RBAC etc.
manifests:  swag
	go run vendor/sigs.k8s.io/controller-tools/cmd/controller-gen/main.go all
	mkdir -p ${LEGION_OPERATOR_GENERATED_ENTITIES}
	mkdir -p ${LEGION_OPERATOR_CRDS}
	@echo "removing old manifests from HELM's generated dictionary"
	rm -fv ${LEGION_OPERATOR_GENERATED_ENTITIES}/*.yaml
	rm -fv ${LEGION_OPERATOR_CRDS}/*.yaml
	@echo "copying actual manifests to HELM's generated dictionary"
	cp -f ./config/crds/*.yaml ${LEGION_OPERATOR_CRDS}
	sed 's/manager-role/legion-operator/g' ./config/rbac/rbac_role.yaml > ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml

# Run go fmt against code
fmt:
	go fmt ./pkg/... ./cmd/...

# Run go vet against code
vet:
	go vet ./pkg/... ./cmd/...

# Generate swagger files
swag:
	@echo 🤙 🤴
	swag init -g pkg/webserver/server.go

# Generate code
generate:
ifndef GOPATH
	$(error GOPATH not defined, please define GOPATH. Run "go help gopath" to learn more about GOPATH)
endif
	go generate ./pkg/... ./cmd/...

build:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -o builder cmd/builder/main.go
