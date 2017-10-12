#!/usr/bin/env bash
#
#   Copyright 2017 EPAM Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

curl -s -H "Content-Type: application/json" \
	-XPOST http://admin:admin@localhost:3000/api/datasources \
	-d @- <<EOF
{
	"id": 1,
	"orgId": 1,
	"name": "graphite",
	"type": "graphite",
	"typeLogoUrl": "public/app/plugins/datasource/graphite/img/graphite_logo.png",
	"access": "proxy",
	"url": "${GF_GRAPHITE_DATASOURCE}",
	"password": "",
	"user": "",
	"database": "",
	"basicAuth": false,
	"isDefault": true,
	"jsonData": {
	  "graphiteVersion": "1.0"
	}
}
EOF


curl -s -H "Content-Type: application/json" \
    -XPOST http://admin:admin@localhost:3000/api/dashboards/db \
    -d @- <<EOF
{
    "overwrite": false,
    "dashboard": {
        "annotations": {
            "list": []
        },
        "editable": true,
        "gnetId": null,
        "graphTooltip": 0,
        "hideControls": false,
        "id": null,
        "links": [],
        "rows": [
            {
                "collapse": false,
                "height": "250px",
                "panels": [{
                    "headings": false,
                    "id": 1,
                    "limit": 10,
                    "links": [],
                    "query": "",
                    "recent": false,
                    "search": true,
                    "span": 12,
                    "starred": false,
                    "tags": [
                        "model"
                    ],
                    "title": "Models list",
                    "type": "dashlist"
                }],
                "repeat": null,
                "repeatIteration": null,
                "repeatRowId": null,
                "showTitle": false,
                "title": "Dashboard Row",
                "titleSize": "h6"
            }
        ],
        "schemaVersion": 14,
        "style": "dark",
        "tags": [],
        "templating": {
            "list": []
        },
        "time": {
            "from": "now-6h",
            "to": "now"
        },
        "timepicker": {
            "refresh_intervals": [
                "5s",
                "10s",
                "30s",
                "1m",
                "5m",
                "15m",
                "30m",
                "1h",
                "2h",
                "1d"
            ],
            "time_options": [
                "5m",
                "15m",
                "1h",
                "6h",
                "12h",
                "24h",
                "2d",
                "7d",
                "30d"
            ]
        },
        "timezone": "",
        "title": "Models",
        "version": 6
    }
}
EOF


curl -s -H "Content-Type: application/json" \
    -XPOST http://admin:admin@localhost:3000/api/user/stars/dashboard/1


curl -s -H "Content-Type: application/json" \
    -XPOST http://admin:admin@localhost:3000/api/preferences/set-home-dash \
    -d @- <<EOF
{
    "theme": "",
    "homeDashboardId":1,
    "timezone":""
}
EOF