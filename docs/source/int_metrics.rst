=============
Metrics
=============

Legion is pluggable and can integrate with a variety of metrics monitoring tools, allowing monitoring for:

* Model training metrics
* Model performance metrics
* System metrics (e.g. operator counters)

Legion's installation :ref:`Helm chart <installation-helm>` boostraps a `Prometheus <https://prometheus.io/>`_ operator 
to persist metrics and `Grafana <https://grafana.com/>`_ dashboard to display them.

For AWS, the integration is defined `here <https://github.com/legion-platform/legion-aws/tree/develop/helms/monitoring>`_.

Alternative integrations can be similarly constructed that swap in other monitoring solutions.
