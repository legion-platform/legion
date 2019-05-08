//
//    Copyright 2019 EPAM Systems
//
//    Licensed under the Apache License, Version 2.0 (the "License");
//    you may not use this file except in compliance with the License.
//    You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS,
//    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//    See the License for the specific language governing permissions and
//    limitations under the License.
//

package utils

import (
	. "github.com/onsi/gomega"
	"testing"
)

func TestParseDockerImageUrl(t *testing.T) {
	g := NewGomegaWithT(t)

	imageAttributes, err := parseImage(
		"nexus.example.com/legion-test-null-test-summation:1.0-190115092855.1.56ed5f4")
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(*imageAttributes).To(Equal(
		imageAttrs{
			host: "https://nexus.example.com",
			name: "legion-test-null-test-summation",
			tag:  "1.0-190115092855.1.56ed5f4",
		},
	))
}
func TestParseDockerImageUrlWithPort(t *testing.T) {
	g := NewGomegaWithT(t)

	imageAttributes, err := parseImage(
		"nexus.example.com:443/legion-test-null-test-summation:1.0-190115092855.1.56ed5f4")
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(*imageAttributes).To(Equal(
		imageAttrs{
			host: "https://nexus.example.com:443",
			name: "legion-test-null-test-summation",
			tag:  "1.0-190115092855.1.56ed5f4",
		},
	))

}
func TestParseComplexDockerImageUrl(t *testing.T) {
	g := NewGomegaWithT(t)

	imageAttributes, err := parseImage(
		"nexus.example.com/legion/test-bare-model-api-model-6:0.10.0-20190115075121.273.56ed5f4")
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(*imageAttributes).To(Equal(
		imageAttrs{
			host: "https://nexus.example.com",
			name: "legion/test-bare-model-api-model-6",
			tag:  "0.10.0-20190115075121.273.56ed5f4",
		},
	))

}
func TestParseComplexDockerImageUrlWithPort(t *testing.T) {
	g := NewGomegaWithT(t)

	imageAttributes, err := parseImage(
		"nexus.example.com:443/legion/test-bare-model-api-model-6:0.10.0-20190115075121.273.56ed5f4")
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(*imageAttributes).To(Equal(
		imageAttrs{
			host: "https://nexus.example.com:443",
			name: "legion/test-bare-model-api-model-6",
			tag:  "0.10.0-20190115075121.273.56ed5f4",
		},
	))
}
