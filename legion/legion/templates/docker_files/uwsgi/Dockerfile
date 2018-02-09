# Standard set up Nginx
ENV NGINX_VERSION 1.13.7-1~stretch
ENV NJS_VERSION   1.13.7.0.1.15-1~stretch

RUN set -x \
	&& apt-get update \
	&& apt-get install --no-install-recommends --no-install-suggests -y nginx libpcre3 libpcre3-dev

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 5000

# Install uWSGI
RUN pip install uwsgi

# Make NGINX run on the foreground
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

COPY nginx.conf /etc/nginx/conf.d/
COPY uwsgi.ini /etc/uwsgi/

RUN apt-get update && apt-get install -y supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV UWSGI_INI /usr/local/lib/python3.5/dist-packages/legion/uwsgi.ini

ENV NGINX_MAX_UPLOAD 0

ENV LISTEN_PORT 5000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

COPY app_uwsgi.ini /usr/local/lib/python3.5/dist-packages/legion/uwsgi.ini
RUN rm /etc/nginx/sites-enabled/default

CMD ["/usr/bin/supervisord"]
