package feedback

const (
	ModelNameHeaderKey       = "model-name"
	ModelVersionHeaderKey    = "model-version"
	ModelEndpointHeaderKey   = "model-endpoint"
	RequestIdHeaderKey       = "x-request-id"
	LegionRequestIdHeaderKey = "request-id"
	HttpMethodHeaderKey      = ":method"
	OriginalUriHeaderKey     = "x-original-uri"
	StatusHeaderKey          = ":status"
	ForwardedHostHeaderKey   = "x-forwarded-host"
)

type RequestResponse struct {
	RequestID           string            `msg:"request_id"`
	RequestHttpHeaders  map[string]string `msg:"request_http_headers"`
	RequestContent      string            `msg:"request_content"`
	RequestUri          string            `msg:"request_uri"`
	ResponseStatus      string            `msg:"response_status"`
	ResponseHttpHeaders map[string]string `msg:"response_http_headers"`
	RequestHost         string            `msg:"request_host"`
	ModelEndpoint       string            `msg:"model_endpoint"`
	ModelVersion        string            `msg:"model_version"`
	ModelName           string            `msg:"model_name"`
	RequestHttpMethod   string            `msg:"request_http_method"`
}

type ResponseBody struct {
	RequestID       string `msg:"request_id"`
	ModelEndpoint   string `msg:"model_endpoint"`
	ModelVersion    string `msg:"model_version"`
	ModelName       string `msg:"model_name"`
	ResponseContent string `msg:"response_content"`
}

type ModelFeedback struct {
	RequestID    string                 `msg:"request_id"`
	ModelVersion string                 `msg:"model_version"`
	ModelName    string                 `msg:"model_name"`
	Payload      map[string]interface{} `msg:"payload"`
}

type DataLogging interface {
	Post(tag string, message interface{}) error
	Close() error
}
