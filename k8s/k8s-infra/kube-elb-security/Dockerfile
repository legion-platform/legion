FROM golang:1.10.8-alpine as builder

RUN apk update && apk add git

COPY ./ /go/src/github.com/legion-platform/kube-elb-security

RUN go get -v github.com/legion-platform/kube-elb-security

FROM alpine:3.8

COPY --from=builder /go/bin/kube-elb-security /kube-elb-security

RUN apk update && apk add ca-certificates

CMD ["/kube-elb-security", "-alsologtostderr"]