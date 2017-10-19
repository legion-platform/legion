FROM docker.elastic.co/logstash/logstash:5.6.3

# add custom config
COPY logstash.conf /config-dir/logstash.conf

# add templates
COPY ./templates/ /config-dir/templates/

# remove xpack
RUN logstash-plugin remove x-pack
RUN sed -i '/xpack/d' /usr/share/logstash/config/logstash.yml
