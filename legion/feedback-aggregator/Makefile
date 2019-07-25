all: help

## test: Run unit tests
test:
	gotestsum --junitfile feedback-report.xml -- -coverprofile=feedback-cover.out ./pkg/...

## build-all: Buld all services
build-all: build-aggregator build-collector

## build-aggregator: Launch aggregator service
run-aggregator:
	go run ./cmd/aggregator/main.go

## build-aggregator: Build aggregator service
build-aggregator:
	go build -o aggregator cmd/aggregator/main.go

## build-collector: Launch collector service
run-collector:
	go run ./cmd/collector/main.go

## build-collector: Build collector service
build-collector:
	go build -o collector cmd/collector/main.go

## help: Show the help message
help: Makefile
	@echo "Choose a command run in "$(PROJECTNAME)":"
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo