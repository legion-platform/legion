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

package configuration

// For now it is very limited configuration.
// The main future to expose external links to Legion resources.
// But it will represent the full legion services configuration in the future.
// TODO: support all legion configuration
type Configuration struct {
	// Common secretion of configuration
	CommonConfiguration CommonConfiguration `json:"common"`
	// Configuration describe training process
	TrainingConfiguration TrainingConfiguration `json:"training"`
}

type CommonConfiguration struct {
	// The collection of external urls, for example: metrics, edge, service catalog and so on
	ExternalUrls []ExternalUrl `json:"externalUrls"`
}

type ExternalUrl struct {
	// Human readable name
	Name string `json:"name"`
	// Link to a resource
	URL string `json:"url"`
}

type TrainingConfiguration struct {
	MetricUrl string `json:"metricUrl"`
}
