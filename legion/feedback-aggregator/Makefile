all: help

## test: Run unit tests
test:
	gotestsum --junitfile feedback-report.xml -- -coverprofile=feedback-cover.out ./pkg/...

## build: Launch feedback service
run:
	go run ./cmd/server.go

## build: Build feedback service
build:
	go build -o feedback cmd/server.go

## help: Show the help message
help: Makefile
	@echo "Choose a command run in "$(PROJECTNAME)":"
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo