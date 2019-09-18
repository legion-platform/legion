# Feedback loop usage protocol
**NOTE: Described below requires `feedback` to be enabled in the HELM's chart configuration during deploy.**

## Request
To send feedback about previously made prediction, HTTP POST request should be sent on EDGE's HTTP endpoint.

URI of HTTP POST request: `/api/model/:model_id/:model_version/feedback`

Where `:model_id` and `:model_version` are the model for which prediction (response) you want to send feedback.

Each feedback request should contain `Request-ID` HTTP header that is equal to prediction's (response's) ID you want send feedback to.

Feedback data structure is not limited and may be send in next payloads of HTTP request:
1. In [form-data](https://tools.ietf.org/html/rfc7578). Data will be placed in `post` group of log entry.
2. In [URL query](https://tools.ietf.org/html/rfc3986#section-3.4) using `key1=value1&key2=valuey2&...` syntax. Data will be placed in `uri` group of log entry.
3. In JSON format in HTTP body for HTTP requests with header `Content-Type` equals `application/json`. Data will be placed in `json` group of log entry.

Each feedback query may contain more then one group (`post`, `uri`, `json`) depending on requests.

**NOTE: Feedback requires JWT authorization (as model invocation) if it is enabled**

## Response
HTTP response code 200 should be returned if request has been parsed and has been sent to storage.

Also, next JSON structure should be returned:
* Field `error` equals to `false`.
* Field `registered` equals to `true`.
* Field `message` equals to data sent on storage.

Non 200 HTTP code indicates about parsing / persisting / another error.

## Example
Example of sending feedback for `income`'s model (version `0.01`) response with ID `9f5a1c74-620f-4b13-993d-842ccd9a7cff`
 with field `"income"` equal to `5000`.

```bash
curl -X POST \
  'http://edge.example.com/api/model/anomaly/0.01/feedback' \
  -H 'Content-Type: application/json' \
  -H 'Request-ID: 9f5a1c74-620f-4b13-993d-842ccd9a7cff' \
  -d '[{"income": 5000}]'
```