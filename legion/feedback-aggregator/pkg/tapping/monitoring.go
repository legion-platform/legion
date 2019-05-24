package tapping

import (
	"fmt"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/spf13/viper"
	"net/http"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const (
	CfgMonitoringHost = "monitoring.host"
	CfgMonitoringPort = "monitoring.port"
)

func init() {
	viper.SetDefault(CfgMonitoringHost, "0.0.0.0")
}

var logM = logf.Log.WithName("collector-monitoring")

var (
	collectedRequests = promauto.NewCounter(prometheus.CounterOpts{
		Name: "total_collected_requests",
		Help: "The total number of processed events",
	})
	errorTapping = promauto.NewCounter(prometheus.CounterOpts{
		Name: "total_error_tapping",
		Help: "The total number of processed events",
	})
)

func StartMonitoringServer() error {
	http.Handle("/metrics", promhttp.Handler())

	metricAddr := fmt.Sprintf("%s:%d", viper.GetString(CfgMonitoringHost), viper.GetInt(CfgMonitoringPort))
	logM.Info("Starting monitoring web server.", "address", metricAddr)
	err := http.ListenAndServe(metricAddr, nil)
	if err != nil {
		logM.Error(err, "Monitoring server")
	}

	return err
}
