package utils

import (
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/onsi/gomega"
	"github.com/spf13/viper"
	"testing"
	"time"
)

func TestCalculateExpirationDate(t *testing.T) {
	g := gomega.NewWithT(t)

	currentTime := time.Now()

	unixExpirationDate, err := CalculateExpirationDate(currentTime.Format(expirationDateLayout))
	g.Expect(err).NotTo(gomega.HaveOccurred())
	g.Expect(currentTime.Unix()).To(gomega.Equal(unixExpirationDate))
}

func TestDefaultExpDateTime(t *testing.T) {
	g := gomega.NewWithT(t)

	currentTime := time.Now()
	viper.Set(legion.JwtExpDatetime, currentTime.Format(expirationDateLayout))

	unixExpirationDate, err := CalculateExpirationDate("")
	g.Expect(err).NotTo(gomega.HaveOccurred())
	g.Expect(currentTime.Unix()).To(gomega.Equal(unixExpirationDate))
}

func TestExpDateTimeIncorrectFormat(t *testing.T) {
	g := gomega.NewWithT(t)

	_, err := CalculateExpirationDate("2006 01 02")
	g.Expect(err).To(gomega.HaveOccurred())
}
