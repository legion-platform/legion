FROM golang:1.10-alpine as builder

RUN apk update && apk add git

RUN   git config --global user.email "you@example.com" \
&& git config --global user.name "Your Name"

RUN go get -d github.com/bitly/oauth2_proxy
RUN cd /go/src/github.com/bitly/oauth2_proxy \
&& git remote add JoelSpeed https://github.com/JoelSpeed/oauth2_proxy.git \
&& git pull -r JoelSpeed kubernetes \
&& go install

FROM alpine:latest

COPY --from=builder /go/bin/oauth2_proxy /oauth2_proxy

RUN apk update && apk add ca-certificates

ENTRYPOINT ["/oauth2_proxy"]
