/* global _ */
'use strict';
/**
 *   Copyright 2017 EPAM Systems
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */

// accessible variables
var window, document, ARGS, $, jQuery, moment, kbn;

// get parameters
var modelId = 'UNKNOWN_MODEL';

if (!_.isUndefined(ARGS.model)) {
    modelId = ARGS.model;
}

var dataSource = services.datasourceSrv.getAll().graphite;
var baseUrl = grafanaBootData.settings.appSubUrl;

function getMetricsList(callback) {
    var metricsLabel = 'stats.legion.model.' + modelId + '.metrics.*';
    var metricsUrl = baseUrl + dataSource.url + '/metrics/find';

    var data = jQuery.getJSON(
        metricsUrl, {
            query: metricsLabel
        },
        function(data) {
            var metrics = {};
            for (var _ in data) {
                var item = data[_];
                if (item.text != 'build')
                    metrics[item.text] = item.id;
            }

            callback(metrics);
        }
    );
}

// Create dashboard
var dashboard;
dashboard = {
    rows: [],
    title: 'Builds of ' + modelId,
    time: {
        from: "now-6h",
        to: "now"
    },
    style: "light",
    editMode: false,
    editable: false,
    hideControls: true
};

return function(callback) {
    getMetricsList(function(data) {
        var metrics = data;
        var metric = null;
        var i = 1;
        for (metric in metrics) {
            dashboard.rows.push({
                "collapse": false,
                "height": 250,
                "panels": [{
                    "aliasColors": {},
                    "bars": false,
                    "dashLength": 10,
                    "dashes": false,
                    "datasource": "graphite",
                    "fill": 1,
                    "id": i,
                    "legend": {
                        "avg": false,
                        "current": false,
                        "max": false,
                        "min": false,
                        "show": true,
                        "total": false,
                        "values": false
                    },
                    "lines": true,
                    "linewidth": 1,
                    "nullPointMode": "connected",
                    "percentage": false,
                    "pointradius": 4,
                    "points": true,
                    "renderer": "flot",
                    "seriesOverrides": [{
                        "alias": "Build #",
                        "lines": false,
                        "pointradius": 1,
                        "points": false,
                        "yaxis": 2
                    }],
                    "spaceLength": 10,
                    "span": 12,
                    "stack": false,
                    "steppedLine": false,
                    "targets": [{
                        "refId": "A_" + metric,
                        "target": "alias(stats.legion.model." + modelId + ".metrics." + metric + ", '" + metric + "')"
                    }, {
                        "refId": "B_" + metric,
                        "target": "alias(stats.legion.model." + modelId + ".metrics.build, 'Build #')"
                    }],
                    "thresholds": [],
                    "timeFrom": null,
                    "timeShift": null,
                    "title": metric,
                    "tooltip": {
                        "shared": true,
                        "sort": 0,
                        "value_type": "individual"
                    },
                    "type": "graph",
                    "xaxis": {
                        "buckets": null,
                        "mode": "time",
                        "name": null,
                        "show": true,
                        "values": []
                    },
                    "yaxes": [{
                        "format": "short",
                        "label": "",
                        "logBase": 1,
                        "max": null,
                        "min": null,
                        "show": true
                    }, {
                        "format": "short",
                        "label": "Build #",
                        "logBase": 1,
                        "max": "10000000",
                        "min": null,
                        "show": false
                    }]
                }],
                "repeat": null,
                "repeatIteration": null,
                "repeatRowId": null,
                "showTitle": false,
                "title": metric,
                "titleSize": "h6"
            });

            i += 1;
        }

        callback(dashboard);
    });
}