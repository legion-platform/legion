#!/usr/bin/env sh

export DOCKER_RESOLVER=`cat /etc/resolv.conf | grep nameserver | awk -e '{ print($2); }'`

/usr/local/openresty/bin/openresty

consul-template -template="/nginx.conf.ctmpl:/usr/local/openresty/nginx/conf/nginx.conf:/usr/local/openresty/bin/openresty -s reload"
