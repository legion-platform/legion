{{/* vim: set filetype=mustache: */}}

{{/*
----------- VERSIONING -----------
*/}}

{{/*
Function builds application (not HELM) version string
This section is under control by .legionVersion section
By default value from $.Chart.AppVersion is used
Arguments:
    - . - root HELM scope
*/}}
{{- define "legion.application-version" -}}
{{ default .Chart.AppVersion .Values.legionVersion }}
{{- end -}}

{{/*
Function builds default labels for all components
It section uses "legion.application-version"
Arguments:
    - . - root HELM scope
*/}}
{{- define "legion.helm-labels" -}}
app.kubernetes.io/component: {{ .component | quote }}
app.kubernetes.io/version: "{{ include "legion.application-version" .root }}"
app: {{ .component | quote }}
version: "{{ include "legion.application-version" .root }}"
app.kubernetes.io/instance: {{ .root.Release.Name | quote }}
app.kubernetes.io/managed-by: {{ .root.Release.Service | quote }}
app.kubernetes.io/name: "legion"
helm.sh/chart: "{{ .root.Chart.Name }}-{{ .root.Chart.Version }}"
{{- end -}}

{{/*
Function builds additional search labels
Arguments:
    - . - root HELM scope
*/}}
{{- define "legion.helm-labels-for-search" -}}
app.kubernetes.io/component: {{ .component | quote }}
app: {{ .component | quote }}
app.kubernetes.io/instance: {{ .root.Release.Name | quote }}
{{- end -}}

{{/*
----------- INGRESS -----------
*/}}

{{/*
Build ingress auth annotations
This section is under control by next sections / fields:
- .security - enables this section
- .security.integration - selects building algorithm
- .security.<oauth2_proxy|etc..> - controlls building of this section
- .ingress.tlsEnabled and .ingress.globalDomain - does default auth URL creations
Arguments:
    - . - root HELM scope
*/}}
{{- define "legion.ingress-auth-annotations" -}}
{{- if .Values.security.enabled }}
{{- if eq .Values.security.integration "oauth2_proxy" -}}
nginx.ingress.kubernetes.io/configuration-snippet: |
    # This is used for redirection user to oauth2 address
    set_escape_uri $escaped_request_uri $request_uri;

    # These collect headers from oauth2
    auth_request_set $user   $upstream_http_x_auth_request_user;
    auth_request_set $email  $upstream_http_x_auth_request_email;
    auth_request_set $jwt    $upstream_http_x_auth_request_access_token;

    # This is a fix for really big sized Cookies (that we have with JWTs inside).
    auth_request_set ${{ .Values.security.oauth2_proxy.cookieName }}_1 $upstream_cookie_{{ .Values.security.oauth2_proxy.cookieName }}_1;

    # These are a headers for upstreams to get information about current user
    proxy_set_header X-User            $user;
    proxy_set_header X-Email           $email;
    proxy_set_header X-JWT             $jwt;
    proxy_set_header Authorization     "Bearer $jwt";

    # This is a fix for really big sized Cookies (that we have with JWTs inside).
    access_by_lua_block {
        if ngx.var.{{ .Values.security.oauth2_proxy.cookieName }}_1 ~= "" then
            ngx.header["Set-Cookie"] = "{{ .Values.security.oauth2_proxy.cookieName }}_1=" .. ngx.var.{{ .Values.security.oauth2_proxy.cookieName }}_1 .. ngx.var.auth_cookie:match("(; .*)")
        end
    }
{{- if hasKey .Values.security.oauth2_proxy "public_url" }}
nginx.ingress.kubernetes.io/auth-signin: {{ .Values.security.oauth2_proxy.public_url }}
{{- else }}
nginx.ingress.kubernetes.io/auth-signin: {{ ternary "https" "http" .Values.ingress.tlsEnabled }}://auth.{{ .Values.ingress.globalDomain }}/oauth2/start?rd=https://$host$escaped_request_uri
{{- end }}
nginx.ingress.kubernetes.io/auth-url: {{ .Values.security.oauth2_proxy.url }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Function builds default (root) ingress annotations
This section is under control by .ingress.annoations section
Arguments:
    - . - root HELM scope
*/}}
{{- define "legion.ingress-default-root-annotations" -}}
{{ range $key, $value := .Values.ingress.annotations }}
{{- $key }}: {{ $value | quote }}
{{ end -}}
{{- end -}}

{{/*
Function builds final ingress annotations for specific service
This section uses "legion.ingress-default-root-annotations" and "legion.ingress-auth-annotations"
 and it's under control by .ingress.annoations section
Arguments:
    - .root - root HELM scope
    - .local - service's ingress section (e.g. .Values.edi.ingress)
*/}}
{{- define "legion.ingress-aggregated-annotations" -}}
{{- include "legion.ingress-default-root-annotations" .root }}
{{- include "legion.ingress-auth-annotations" .root }}
{{ range $key, $value := .local.annotations }}
{{- $key }}: {{ $value | quote }}
{{ end -}}
{{- end -}}

{{/*
Function builds domain name for service or use custom
This section is under control by .ingress.globalDomain and service-specific .ingress.domain
Arguments:
    - .root - root HELM scope
    - .local - service's ingress section (e.g. .Values.edi.ingress)
    - .tpl - template for URI
*/}}
{{- define "legion.ingress-domain-name" -}}
{{ ternary .local.domain (printf .tpl .root.Values.ingress.globalDomain) (hasKey .local "domain") }}
{{- end -}}

{{/*
Function builds name of TLS secret
This section is under control by .ingress.tlsSecretName and service-specific .ingress.tlsSecretName
Arguments:
    - .root - root HELM scope
    - .local - service's ingress section (e.g. .Values.edi.ingress)
*/}}
{{- define "legion.ingress-tls-secret-name" -}}
{{ required "TLS Secret name is required" (ternary .local.tlsSecretName .root.Values.ingress.tlsSecretName (hasKey .local "tlsSecretName")) }}
{{- end -}}



{{/*
----------- IMAGES -----------
*/}}
{{/*
Function builds default image name for Kubernetes Pod
Arguments:
    - .root - root HELM scope
    - .tpl - template for building default URI of image
*/}}
{{- define "legion.default-image-name" -}}
{{ printf .tpl .root.Values.imagesRegistry (include "legion.application-version" .root) }}
{{- end -}}

{{/*
Function builds image name for Kubernetes Pod
Arguments:
    - .root - root HELM scope
    - .service - service's scope with desired image field
    - .tpl - template for building default URI of image
*/}}
{{- define "legion.image-name" -}}
{{- if .service }}
{{- if (hasKey .service "image") }}
{{ .service.image  }}
{{- else -}}
{{- include "legion.default-image-name" . -}}
{{ end }}
{{- else }}
{{- include "legion.default-image-name" . -}}
{{ end }}
{{- end -}}