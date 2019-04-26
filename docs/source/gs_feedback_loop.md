# Feedback loop

**NOTE: Described below requires `feedback` to be enabled in the HELM's chart configuration during deploy.**

Feedback loop allows model's developers to get review how good models work from their users (3rd-party systems or users that ask for prediction).

* When anybody asks model for prediction, `Request-ID` header with random generated value is added to request and response.
* Generating of new value for `Request-ID` header is missing if value is present by requester.
* Request and response of the model are being stored on external storage service (such as AWS S3 or GCS, depending on configuration).
* Later, when feedback about prediction could be made (e.g. action, that is predicted, appeared), [another HTTP request](./ref_feedback_loop_protocol.md) should be sent.
* All feedbacks are persisted on external storage service (depending on configuration) and can be used by models during next (re-) training phase (automatically, without any manual actions).

