FROM fluent/fluentd-kubernetes-daemonset:v1.2.6-debian-syslog

RUN gem install fluent-plugin-forest -v 0.3.3 && gem install fluent-plugin-s3 -v 1.1.6

ADD fluent.conf /fluentd/etc/fluent.conf