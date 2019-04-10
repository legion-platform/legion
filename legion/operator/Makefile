
# Image URL to use all building/pushing image targets
LEGION_SRC_ROOT = ../../
CONTAINERS = ${LEGION_SRC_ROOT}/build/containers
TARGET_HELM_CHART = ${LEGION_SRC_ROOT}/helms/legion/
TARGET_YAML_STORAGE = ${TARGET_HELM_CHART}/templates/operator/generated

all: manager

# Run tests
test: generate fmt vet manifests
	go test ./pkg/... ./cmd/... -coverprofile cover.out

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
manifests:
	go run vendor/sigs.k8s.io/controller-tools/cmd/controller-gen/main.go all
	mkdir -p ${TARGET_YAML_STORAGE}
	@echo "removing old manifests from HELM's generated dictionary"
	rm -fv ${TARGET_YAML_STORAGE}/*.yaml
	@echo "copying actual manifests to HELM's generated dictionary"
	cp -f ./config/crds/*.yaml ${TARGET_YAML_STORAGE}
	cp -f ./config/rbac/rbac_role.yaml ${TARGET_YAML_STORAGE}
	# sed -i '' -e 's@manager-role@"{{ .Release.Name }}-manager-role"@' ${TARGET_YAML_STORAGE}/rbac_role.yaml

# Run go fmt against code
fmt:
	go fmt ./pkg/... ./cmd/...

# Run go vet against code
vet:
	go vet ./pkg/... ./cmd/...

# Generate code
generate:
ifndef GOPATH
	$(error GOPATH not defined, please define GOPATH. Run "go help gopath" to learn more about GOPATH)
endif
	go generate ./pkg/... ./cmd/...

build:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -o builder cmd/builder/main.go
