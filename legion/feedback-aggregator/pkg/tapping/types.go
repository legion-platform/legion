package tapping

const (
	CfgEnvoyHost     = "envoy.host"
	CfgEnvoyPort     = "envoy.port"
	CfgEnvoyConfigId = "envoy.config_id"
)

type TapRequestHeader struct {
	Name       string `yaml:"name"`
	RegexMatch string `yaml:"regex_match"`
}

type TapSink struct {
	StreamingAdmin map[string]string `yaml:"streaming_admin"`
}

type TapRequest struct {
	ConfigID  string `yaml:"config_id"`
	TapConfig struct {
		MatchConfig struct {
			HttpRequestHeadersMatch struct {
				Headers []TapRequestHeader `yaml:"headers"`
			} `yaml:"http_request_headers_match"`
		} `yaml:"match_config"`
		OutputConfig struct {
			Sinks []TapSink `yaml:"sinks"`
			MaxBufferedTxBytes int32 `yaml:"max_buffered_tx_bytes"`
			MaxBufferedRxBytes int32 `yaml:"max_buffered_rx_bytes"`
		} `yaml:"output_config"`
	} `yaml:"tap_config"`
}

type Trace struct {
	Headers []struct {
		Key   string `json:"key"`
		Value string `json:"value"`
	} `json:"headers"`
	Body struct {
		Truncated bool   `json:"truncated"`
		AsBytes   string `json:"as_bytes"`
	} `json:"body"`
}

type Message struct {
	HttpBufferedTrace struct {
		Request  Trace `json:"request,omitempty"`
		Response Trace `json:"response,omitempty"`
	} `json:"http_buffered_trace"`
}
