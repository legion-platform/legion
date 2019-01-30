FROM golang:1.10-alpine@sha256:ceed38104630b9daf9584415d0f4295853e7244ecb646687219bf9808dbcef32 as builder

RUN apk update && apk add git

COPY ./ /go/src/github.com/legion-platform/kube-elb-security

RUN go get -v github.com/legion-platform/kube-elb-security

FROM alpine:3.8@sha256:46e71df1e5191ab8b8034c5189e325258ec44ea739bba1e5645cff83c9048ff1

COPY --from=builder /go/bin/kube-elb-security /kube-elb-security

RUN apk update && apk add ca-certificates

CMD ["/kube-elb-security", "-alsologtostderr"]