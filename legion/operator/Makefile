LEGION_OPERATOR_GENERATED_ENTITIES = ../../helms/legion/templates/operator/generated

all: help

## help: Run unit tests
test: generate fmt vet manifests
	gotestsum --junitfile operator-report.xml -- -coverprofile=operator-cover.out ./pkg/...

## build-operator: Build operator executable binary
build-operator: generate  fmt vet
	go build -o operator github.com/legion-platform/legion/legion/operator/cmd/manager

## build-edi: Build edi executable binary
build-edi: fmt vet
	go build -o edi github.com/legion-platform/legion/legion/operator/cmd/edi

## build-model-builder: Build model builder executable binary
build-model-builder: fmt vet
	go build -o builder github.com/legion-platform/legion/legion/operator/cmd/builder

## build-all: Build all executable binyries
build-all: build-edi build-model-builder build-operator

## run-operator: Start operator
run-operator:
	go run ./cmd/operator/main.go

## run-edi: Start edi server
run-edi:
	go run ./cmd/operator/main.go

## install-crds: Install CRDs into a cluster
install-crds: manifests
	kubectl apply -f config/crds

## manifests: Generate manifests e.g. CRD, RBAC etc.
manifests:  swag
	go run vendor/sigs.k8s.io/controller-tools/cmd/controller-gen/main.go all

	mkdir -p ${LEGION_OPERATOR_GENERATED_ENTITIES}
	@echo "removing old manifests from HELM's generated dictionary"

	rm -fv ${LEGION_OPERATOR_GENERATED_ENTITIES}/*.yaml
	@echo "copying actual manifests to HELM's generated dictionary"
	cp -f ./config/crds/*.yaml ${LEGION_OPERATOR_GENERATED_ENTITIES}
	cp config/rbac/rbac_role.yaml ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml

	# All Legion CRD's and operator role are generated resources.
	# We cannot add, for example, a custom label during the generation process.
	# That's why we add them using sed tool after generation.

	sed -i '/^  name:.*$$/a \ \ labels:' ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml
	sed -i '/^  name:.*$$/a \ \ annotations:' ${LEGION_OPERATOR_GENERATED_ENTITIES}/*v1alpha1*.yaml

	sed -i '/^  labels:$$/a \ \ \ \ {{- include "legion.helm-labels" . | nindent 4 }}' ${LEGION_OPERATOR_GENERATED_ENTITIES}/*.yaml
	sed -i '/^  annotations:$$/a \ \ \ \ "helm.sh/hook": "crd-install"' ${LEGION_OPERATOR_GENERATED_ENTITIES}/*v1alpha1*.yaml

	sed -i '/^  labels:$$/a \ \ \ \ component: "legion-operator"' ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml
	sed -i 's/manager-role/"{{ .Release.Name }}-operator"/g' ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml
	sed -i '1i{{- if .Values.rbac }}' ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml
	sed -i '$$a{{- end }}' ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml

## fmt: Run go fmt against code
fmt:
	go fmt ./pkg/... ./cmd/...

## vet: Run go vet against code
vet:
	go vet ./pkg/... ./cmd/...

## swag: Generate swagger files
swag:
	swag init -g pkg/webserver/server.go
	# Remove the line with generated timestamp
	sed -i '3d' docs/docs.go

## generate: Generate golang codes
generate:
ifndef GOPATH
	$(error GOPATH not defined, please define GOPATH. Run "go help gopath" to learn more about GOPATH)
endif
	go generate ./pkg/... ./cmd/...

## help: Show the help message
help: Makefile
	@echo "Choose a command run in "$(PROJECTNAME)":"
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo