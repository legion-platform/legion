FROM golang:1.10-alpine@sha256:ceed38104630b9daf9584415d0f4295853e7244ecb646687219bf9808dbcef32 as builder

RUN apk update && apk add git

RUN   git config --global user.email "you@example.com" \
&& git config --global user.name "Your Name"

RUN go get -d github.com/bitly/oauth2_proxy
RUN cd /go/src/github.com/bitly/oauth2_proxy \
&& git remote add JoelSpeed https://github.com/JoelSpeed/oauth2_proxy.git \
&& git pull -r JoelSpeed kubernetes \
&& go install

FROM alpine:3.8@sha256:46e71df1e5191ab8b8034c5189e325258ec44ea739bba1e5645cff83c9048ff1

COPY --from=builder /go/bin/oauth2_proxy /oauth2_proxy

RUN apk update && apk add ca-certificates

ENTRYPOINT ["/oauth2_proxy"]
