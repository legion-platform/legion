{{/* vim: set filetype=mustache: */}}

{{/*
Create dex Ingress auth annotations
*/}}
{{- define "dex-ingress-annotations" }}
    {{- if .Values.auth.enabled -}}
    {{- range $key, $value := .Values.auth.annotations }}
    {{ $key }}: {{ $value | quote }}
    {{- end }}
    {{- end }}
{{- end }}
