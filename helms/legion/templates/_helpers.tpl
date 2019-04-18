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


{{- define "ingress-annotations" }}
{{- end }}

{{- define "legion.application-version" -}}
{{ default .Chart.AppVersion .Values.legionVersion }}
{{- end -}}


{{- define "legion.helm-labels" -}}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service | quote }}
app.kubernetes.io/name: "legion"
helm.sh/chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
app.kubernetes.io/version: "{{ include "legion.application-version" . }}"
{{- end -}}