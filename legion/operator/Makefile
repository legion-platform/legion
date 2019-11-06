LEGION_OPERATOR_GENERATED_ENTITIES = ../../helms/legion/templates/operator/generated
LINTER_ADDITIONAL_ARGS =
KUBEBUILDER_CONTROLPLANE_START_TIMEOUT=600s

LEGION_NAMESPACE=legion
LEGION_SECRET_CONFIG=legion-operator-config

# Hardcoded vault token for local development
TEST_VAULT_ROOT_TOKEN=test_root_token

.EXPORT_ALL_VARIABLES:

all: help

## help: Run unit tests
test: generate fmt vet manifests
	gotestsum --junitfile operator-report.xml -- -coverprofile=operator-cover.out ./pkg/...

## build-operator: Build operator executable binary
build-operator: generate  fmt vet
	go build -o operator github.com/legion-platform/legion/legion/operator/cmd/operator

## build-edi: Build edi executable binary
build-edi: fmt vet
	go build -o edi github.com/legion-platform/legion/legion/operator/cmd/edi

## build-model-trainer: Build model trainer executable binary
build-model-trainer: fmt vet
	go build -o trainer github.com/legion-platform/legion/legion/operator/cmd/trainer

## build-model-packager: Build model packager executable binary
build-model-packager: fmt vet
	go build -o packager github.com/legion-platform/legion/legion/operator/cmd/packager

## build-model-packager: Build model packager executable binary
build-service-catalog: fmt vet
	go build -o service-catalog github.com/legion-platform/legion/legion/operator/cmd/service_catalog

## build-all: Build all executable binyries
build-all: build-edi build-model-trainer build-model-packager build-operator build-service-catalog

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

	sed -i '/^  labels:$$/a \ \ \ \ {{- include "legion.helm-labels" (dict "component" "operator" "root" .) | nindent 4 }}' ${LEGION_OPERATOR_GENERATED_ENTITIES}/*.yaml
	sed -i '/^  annotations:$$/a \ \ \ \ "helm.sh/hook": "crd-install"' ${LEGION_OPERATOR_GENERATED_ENTITIES}/*v1alpha1*.yaml

	sed -i 's/manager-role/"{{ .Release.Name }}-operator"/g' ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml
	sed -i '1i{{- if .Values.rbac }}' ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml
	sed -i '$$a{{- end }}' ${LEGION_OPERATOR_GENERATED_ENTITIES}/operator-rbac-role.yaml

## fmt: Run go fmt against code
fmt:
	go fmt ./pkg/... ./cmd/...

## vet: Run go vet against code
vet:
	go vet ./pkg/... ./cmd/...

## run-vault: Start vault in dev model for local development
run-value:
	vault server -dev -dev-root-token-id $TEST_VAULT_ROOT_TOKEN

## swag: Generate swagger files
swag:
	swag init -g pkg/webserver/server.go
	# Remove the line with generated timestamp
	sed -i '3d' docs/docs.go
	sed -i 's/connection\.//g' docs/*
	sed -i 's/routes\.//g' docs/*
	sed -i 's/deployment\.//g' docs/*
	sed -i 's/training\.//g' docs/*
	sed -i 's/packaging\.//g' docs/*
	sed -i 's/configuration\.//g' docs/*
	sed -i 's/v1alpha1\.//g' docs/*

## apply-crds: Apply all legion crds
apply-crds:
	kubectl apply -f config/crds/

## delete-crds: Delete all legion crds
delete-crds:
	kubectl delete -f config/crds/

## recreate-crds: Recreate all legion crds
recreate-crds: delete-crds apply-crds

## generate: Generate golang codes
generate:
ifndef GOPATH
	$(error GOPATH not defined, please define GOPATH. Run "go help gopath" to learn more about GOPATH)
endif
	go generate ./pkg/... ./cmd/...

## generate-all: Execute all code generators
generate-all: generate manifests swag

## export-config-from-k8s: Export operator config from k8s secret. It helps to run operator or edi locally with properly set of config options
export-config-from-k8s:
	kubectl get -n ${LEGION_NAMESPACE} secrets ${LEGION_SECRET_CONFIG} -o=jsonpath="{$$.data['config\\.yaml']}" | base64 -d > config.yaml

## turn-off-legion-operator: The command scales down the legion operator to the zero number of pods.
turn-off-legion-operator:
	kubectl scale --replicas 0 -n ${LEGION_NAMESPACE} statefulset/legion-operator

## turn-on-legion-operator: The command scales up the legion operator to the one number of pods.
turn-on-legion-operator:
	kubectl scale --replicas 1 -n ${LEGION_NAMESPACE} statefulset/legion-operator

## lint: Start golangci-lint linter
lint:
	golangci-lint run ${LINTER_ADDITIONAL_ARGS}

## help: Show the help message
help: Makefile
	@echo "Choose a command run in "$(PROJECTNAME)":"
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo
