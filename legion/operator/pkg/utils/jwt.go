package utils

import (
	"github.com/dgrijalva/jwt-go"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/spf13/viper"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"time"
)

const (
	expirationDateLayout = "2006-01-02T15:04:05"
)

var (
	logJwt = logf.Log.WithName("jwt")
)

func CalculateExpirationDate(expirationDateStr string) (unixExpirationDate int64, err error) {
	if expirationDateStr == "" {
		expirationDateStr = viper.GetString(viper.GetString(legion.JwtExpDatetime))
	}

	var expirationDate time.Time
	if expirationDateStr != "" {
		expirationDate, err := time.Parse(expirationDateLayout, expirationDateStr)

		if err != nil {
			return 0, err
		}

		maxExpirationDate := time.Now().Add(viper.GetDuration(legion.JwtMaxTtlMinutes) * time.Minute)

		if expirationDate.After(maxExpirationDate) {
			expirationDate = maxExpirationDate
		}

		return expirationDate.Unix(), nil
	}

	expirationDate = time.Now().Add(viper.GetDuration(legion.JwtTtlMinutes) * time.Minute)

	return expirationDate.Unix(), err
}

// HS256 algorithm
func GenerateModelToken(modelId, modelVersion string, expirationDateUnix int64) (string, error) {
	token, err := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"model_id":      []string{modelId},
		"model_version": []string{modelVersion},
		"exp":           expirationDateUnix,
	}).SignedString([]byte(viper.GetString(legion.JwtSecret)))
	if err != nil {
		return "", err
	}

	return token, nil
}
