all: build

test:
	go test ./cmd ./pkg/... -coverprofile cover.out

run:
	go run ./cmd/server.go

build:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -o builder cmd/server.go
