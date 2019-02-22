FROM fluent/fluentd-kubernetes-daemonset:v1.2.6-debian-syslog@sha256:a7c386043d2413d2b8cc1ccde5f0ed6b438958c29f8057d2efadca4b692c8c80

RUN gem install fluent-plugin-forest -v 0.3.3 && gem install fluent-plugin-s3 -v 1.1.6

ADD fluent.conf /fluentd/etc/fluent.conf