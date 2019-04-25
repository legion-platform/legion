{{/* vim: set filetype=mustache: */}}

{{/*
Function builds default labels for all components
Arguments:
    - . - root HELM scope
*/}}
{{- define "legion.helm-labels" -}}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service | quote }}
app.kubernetes.io/name: "legion"
helm.sh/chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
{{- end -}}
