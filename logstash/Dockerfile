FROM docker.elastic.co/logstash/logstash:5.6.3

# add custom config
COPY logstash.conf /config-dir/logstash.conf

# remove xpack
RUN logstash-plugin remove x-pack
RUN sed -i '/xpack/d' /usr/share/logstash/config/logstash.yml
