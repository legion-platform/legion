#!/usr/bin/env sh

/usr/local/openresty/bin/openresty
consul-template -template="/nginx.conf.ctmpl:/usr/local/openresty/nginx/conf/nginx.conf:cat /usr/local/openresty/nginx/conf/nginx.conf"

# /usr/local/openresty/bin/openresty -s reload
