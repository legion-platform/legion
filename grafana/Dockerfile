FROM grafana/grafana

COPY ./entrypoint.sh /entrypoint.sh
COPY ./bootstrap_grafana.sh /bootstrap_grafana.sh

RUN chmod a+rwx /entrypoint.sh
RUN chmod a+rwx /bootstrap_grafana.sh

ENTRYPOINT ["/entrypoint.sh"]

