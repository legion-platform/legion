FROM golang:1.10.8-alpine@sha256:549535d72baf28b3d1470ef9fcc6d4e0cb52c7fc3012655a659b65eaf942ec63 as builder

RUN apk update && apk add git

COPY ./ /go/src/github.com/legion-platform/kube-elb-security

RUN go get -v github.com/legion-platform/kube-elb-security

FROM alpine:3.8

COPY --from=builder /go/bin/kube-elb-security /kube-elb-security

RUN apk update && apk add ca-certificates

CMD ["/kube-elb-security", "-alsologtostderr"]