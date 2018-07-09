RUN apk add --update \
    ca-certificates curl openrc docker \
    nginx pcre pcre-dev supervisor py-gunicorn

EXPOSE 5000

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

# Make NGINX run on the foreground
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/
COPY uwsgi.ini /etc/uwsgi/
COPY app_uwsgi.ini /usr/lib/python3.6/site-packages/legion/uwsgi.ini
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV UWSGI_INI /usr/lib/python3.6/site-packages/legion/uwsgi.ini

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf" ]

ARG pip_extra_index_params=""
ARG pip_legion_version_string=""

RUN pip install --disable-pip-version-check $pip_extra_index_params legion$pip_legion_version_string
