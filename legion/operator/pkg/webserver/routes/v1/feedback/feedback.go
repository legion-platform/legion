/*
 * Copyright 2019 EPAM Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package feedback

// Currently we can not aggregate swagger documentation from multiply services
// TODO: need to implement it

type FeedbackRequest struct{}
type FeedbackResponse struct{}

// @Summary Send feedback about previously made prediction
// @Description Send feedback about previously made prediction
// @Tags Feedback
// @Param feedback body feedback.FeedbackRequest true "Feedback Request"
// @Accept  json
// @Produce  json
// @Param model-name header string true "Model name"
// @Param model-version header string true "Model version"
// @Param request-id header string true "Request ID"
// @Success 200 {object} feedback.FeedbackResponse
// @Router /api/v1/feedback [post]
func stubFeedback() {
	panic("must be never invoked!")
}
