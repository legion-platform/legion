package aggregator

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	collectedFeedback = promauto.NewCounter(prometheus.CounterOpts{
		Name: "total_collected_feedback",
		Help: "The total number of processed events",
	})
)
