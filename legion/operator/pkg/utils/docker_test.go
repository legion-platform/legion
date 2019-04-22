package utils

import (
	"github.com/onsi/gomega"
	"testing"
)

func TestParseDockerImageUrl(t *testing.T) {
	g := gomega.NewGomegaWithT(t)

	imageAttributes, err := parseImage(
		"nexus.example.com/legion-test-null-test-summation:1.0-190115092855.1.56ed5f4")
	g.Expect(err).NotTo(gomega.HaveOccurred())
	g.Expect(*imageAttributes).To(gomega.Equal(
		imageAttrs{
			host: "https://nexus.example.com",
			name: "legion-test-null-test-summation",
			tag:  "1.0-190115092855.1.56ed5f4",
		},
	))
}
func TestParseDockerImageUrlWithPort(t *testing.T) {
	g := gomega.NewGomegaWithT(t)

	imageAttributes, err := parseImage(
		"nexus.example.com:443/legion-test-null-test-summation:1.0-190115092855.1.56ed5f4")
	g.Expect(err).NotTo(gomega.HaveOccurred())
	g.Expect(*imageAttributes).To(gomega.Equal(
		imageAttrs{
			host: "https://nexus.example.com:443",
			name: "legion-test-null-test-summation",
			tag:  "1.0-190115092855.1.56ed5f4",
		},
	))

}
func TestParseComplexDockerImageUrl(t *testing.T) {
	g := gomega.NewGomegaWithT(t)

	imageAttributes, err := parseImage(
		"nexus.example.com/legion/test-bare-model-api-model-6:0.10.0-20190115075121.273.56ed5f4")
	g.Expect(err).NotTo(gomega.HaveOccurred())
	g.Expect(*imageAttributes).To(gomega.Equal(
		imageAttrs{
			host: "https://nexus.example.com",
			name: "legion/test-bare-model-api-model-6",
			tag:  "0.10.0-20190115075121.273.56ed5f4",
		},
	))

}
func TestParseComplexDockerImageUrlWithPort(t *testing.T) {
	g := gomega.NewGomegaWithT(t)

	imageAttributes, err := parseImage(
		"nexus.example.com:443/legion/test-bare-model-api-model-6:0.10.0-20190115075121.273.56ed5f4")
	g.Expect(err).NotTo(gomega.HaveOccurred())
	g.Expect(*imageAttributes).To(gomega.Equal(
		imageAttrs{
			host: "https://nexus.example.com:443",
			name: "legion/test-bare-model-api-model-6",
			tag:  "0.10.0-20190115075121.273.56ed5f4",
		},
	))
}
