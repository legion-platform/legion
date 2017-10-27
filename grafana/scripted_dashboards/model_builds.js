/* global _ */
'use strict';

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
    }
};


return function(callback) {
    getMetricsList(function(data) {
        var metrics = data;
        var metric = null;
        for (metric in metrics) {
             var targets =[{
                        "hide": false,
                        "refId": "A_" + metric,
                        "target": "alias(removeBelowValue(" + metrics[metric] + ", 0), '" + metric + "')",
                        "textEditor": true
                    },{
                        "hide": false,
                        "refId": "B_" + metric,
                        "target": "alias(removeBelowValue(stats.legion.model.image_recognize.metrics.build, 0), 'Build #')",
                        "textEditor": true
                    }];
            console.log(targets);

            dashboard.rows.push({
                title: metric,
                height: '300px',
                panels: [{
                    "aliasColors": {},
                    "bars": true,
                    "datasource": "graphite",
                    "fill": 1,
                    "id": 5,
                    "lines": false,
                    "nullPointMode": "null",
                    "renderer": "flot",
                    "seriesOverrides": [],
                    "spaceLength": 10,
                    "span": 12,
                    "targets": targets,
                    "title": metric,
                    "tooltip": {
                        "shared": false,
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
                            "label": null,
                            "logBase": 1,
                            "max": null,
                            "min": null,
                            "show": true
                        },
                        {
                            "format": "short",
                            "label": null,
                            "logBase": 1,
                            "max": null,
                            "min": null,
                            "show": true
                        }
                    ]
                }]
            });
        }

        callback(dashboard);
    });
}