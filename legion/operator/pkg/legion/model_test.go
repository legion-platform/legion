package legion

import (
	"github.com/onsi/gomega"
	"testing"
)

func TestNameNormalization(t *testing.T) {
	g := gomega.NewGomegaWithT(t)

	g.Expect(ConvertTok8sName("id", "Test name!")).To(gomega.Equal("model-id-Test-name"))
	g.Expect(ConvertTok8sName("id", "Test-)1+name!")).To(gomega.Equal("model-id-Test-1-name"))
	g.Expect(ConvertTok8sName("id", "abc-_ .")).To(gomega.Equal("model-id-abc----"))
}
