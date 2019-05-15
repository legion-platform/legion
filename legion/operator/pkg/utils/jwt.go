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
