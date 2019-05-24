package tapping

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"github.com/legion-platform/legion/legion/feedback-aggregator/pkg/feedback"
	"github.com/spf13/viper"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"net/http"
	"net/url"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"time"
)

const (
	TapUrl                 = "/tap"
	filterHeaderKey        = ":path"
	filterRegexHeaderValue = ".*/api/model/invoke.*"
	defaultBufferSize      = 1024 * 1024
)

var log = logf.Log.WithName("collector")

var (
	prohibitedHeaders = map[string]interface{}{
		"authorization": nil,
	}
)

type RequestCollector struct {
	envoyUrl            string
	feedbackRequestYaml []byte
	logger              feedback.DataLogging
}

func NewRequestCollector(envoyHost string, envoyPort int, configId string, logger feedback.DataLogging) (*RequestCollector, error) {
	feedbackRequest := TapRequest{
		ConfigID: configId,
	}

	feedbackRequest.TapConfig.MatchConfig.HttpRequestHeadersMatch.Headers =
		append(
			feedbackRequest.TapConfig.MatchConfig.HttpRequestHeadersMatch.Headers,
			TapRequestHeader{
				Name:       filterHeaderKey,
				RegexMatch: filterRegexHeaderValue,
			},
		)
	feedbackRequest.TapConfig.OutputConfig.Sinks = append(
		feedbackRequest.TapConfig.OutputConfig.Sinks,
		TapSink{StreamingAdmin: map[string]string{}},
	)
	feedbackRequest.TapConfig.OutputConfig.MaxBufferedRxBytes = defaultBufferSize
	feedbackRequest.TapConfig.OutputConfig.MaxBufferedTxBytes = defaultBufferSize
	feedbackRequestYaml, err := yaml.Marshal(feedbackRequest)
	if err != nil {
		log.Error(err, "Tapping request")

		return nil, err
	}

	return &RequestCollector{
		envoyUrl:            fmt.Sprintf("%s:%d", envoyHost, envoyPort),
		feedbackRequestYaml: feedbackRequestYaml,
		logger:              logger,
	}, nil
}

func parseUrlencodedParams(params url.Values) map[string]interface{} {
	args := make(map[string]interface{}, len(params))

	for k, v := range params {
		if len(v) == 1 {
			args[k] = v[0]
		} else {
			args[k] = v
		}
	}

	return args
}

func convertToFeedback(message *Message) (*feedback.RequestResponse, *feedback.ResponseBody) {
	responseBody := &feedback.ResponseBody{}
	requestResponse := &feedback.RequestResponse{}

	requestHeaders := make(map[string]string, len(message.HttpBufferedTrace.Request.Headers))
	for _, header := range message.HttpBufferedTrace.Request.Headers {
		if _, ok := prohibitedHeaders[header.Key]; ok {
			continue
		}

		switch header.Key {
		case feedback.HttpMethodHeaderKey:
			requestResponse.RequestHttpMethod = header.Value

		case feedback.OriginalUriHeaderKey:
			requestResponse.RequestUri = header.Value

		case feedback.ForwardedHostHeaderKey:
			requestResponse.RequestHost = header.Value

		case feedback.RequestIdHeaderKey:
			if len(responseBody.RequestID) == 0 || len(requestResponse.RequestID) == 0 {
				responseBody.RequestID = header.Value
				requestResponse.RequestID = header.Value
			}

		case feedback.LegionRequestIdHeaderKey:
			responseBody.RequestID = header.Value
			requestResponse.RequestID = header.Value
		}

		requestHeaders[header.Key] = header.Value
	}

	responseHeaders := make(map[string]string, len(message.HttpBufferedTrace.Response.Headers))
	for _, header := range message.HttpBufferedTrace.Response.Headers {
		if _, ok := prohibitedHeaders[header.Key]; ok {
			continue
		}

		switch header.Key {
		case feedback.ModelNameHeaderKey:
			responseBody.ModelName = header.Value
			requestResponse.ModelName = header.Value

		case feedback.ModelVersionHeaderKey:
			responseBody.ModelVersion = header.Value
			requestResponse.ModelVersion = header.Value

		case feedback.ModelEndpointHeaderKey:
			responseBody.ModelEndpoint = header.Value
			requestResponse.ModelEndpoint = header.Value

		case feedback.StatusHeaderKey:
			requestResponse.ResponseStatus = header.Value
		}

		responseHeaders[header.Key] = header.Value
	}

	requestResponse.RequestHttpHeaders = requestHeaders
	requestResponse.ResponseHttpHeaders = responseHeaders

	responseBytes, err := base64.StdEncoding.DecodeString(message.HttpBufferedTrace.Response.Body.AsBytes)
	if err != nil {
		// Impossible situation
		panic(err)
	}
	responseBody.ResponseContent = string(responseBytes)

	if requestResponse.RequestHttpMethod == http.MethodGet {
		uri, err := url.ParseRequestURI(requestResponse.RequestUri)
		if err == nil {
			requestResponse.RequestGetArgs = parseUrlencodedParams(uri.Query())
		}
	} else {
		requestBytes, err := base64.StdEncoding.DecodeString(message.HttpBufferedTrace.Request.Body.AsBytes)
		if err != nil {
			// Impossible situation
			panic(err)
		}
		params, err := url.ParseQuery(string(requestBytes))
		if err == nil {
			requestResponse.RequestPostArgs = parseUrlencodedParams(params)
		}
	}

	return requestResponse, responseBody
}

func (rc *RequestCollector) TraceRequests() error {
	for {
		if err := rc.tapTraffic(); err != nil {
			errorTapping.Add(1)

			log.Error(err, "Traffic tapping")
			time.Sleep(1 * time.Second)
		}
	}
}

func (rc *RequestCollector) tapTraffic() error {
	req := &http.Request{
		Method: http.MethodPost,
		URL: &url.URL{
			Scheme: "http",
			Host:   rc.envoyUrl,
			Path:   TapUrl,
		},
		Body: ioutil.NopCloser(bytes.NewBuffer(rc.feedbackRequestYaml)),
	}
	client := &http.Client{
		Transport: http.DefaultTransport,
		Timeout:   0,
	}

	resp, err := client.Do(req)

	if err != nil {
		return err
	}

	dec := json.NewDecoder(resp.Body)
	for dec.More() {
		collectedRequests.Add(1)
		var message Message

		err := dec.Decode(&message)
		if err != nil {
			return err
		}

		requestResponse, responseBody := convertToFeedback(&message)

		err = rc.logger.Post(viper.GetString(feedback.CfgRequestResponseTag), *requestResponse)
		if err != nil {
			return err
		}

		err = rc.logger.Post(viper.GetString(feedback.CfgResponseBodyTag), *responseBody)
		if err != nil {
			return err
		}
	}

	return err
}
