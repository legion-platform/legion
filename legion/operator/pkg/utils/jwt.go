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
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	gojwt "github.com/dgrijalva/jwt-go"
	config_deployment "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	"github.com/lestrrat-go/jwx/jwa"
	"github.com/lestrrat-go/jwx/jwk"
	"github.com/lestrrat-go/jwx/jwt"
	"github.com/spf13/viper"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"sync"
	"time"
)

const (
	expirationDateLayout = "2006-01-02T15:04:05"
	defaultJwtKeyName    = "model"
	defaultIss           = "edi"
	defaultSub           = "edi"
)

var (
	logJwt      = logf.Log.WithName("jwt")
	jwks        = ""
	initJwks    sync.Once
	signKey     *rsa.PrivateKey
	initSignKey sync.Once
)

func Jwks() string {
	initJwks.Do(func() {
		if !viper.GetBool(config_deployment.SecurityJwtEnabled) {
			logJwt.Info("Jwt integration is disabled")
			return
		}

		logJwt.Info("Jwt integration is enabled")

		publicKey, err := base64.StdEncoding.DecodeString(viper.GetString(config_deployment.SecurityJwtPublicKey))
		if err != nil {
			logJwt.Error(err, "base64 decoding")
			panic(err)
		}
		block, _ := pem.Decode(publicKey)
		parseResult, _ := x509.ParsePKIXPublicKey(block.Bytes)

		key, err := jwk.New(parseResult)
		if err != nil {
			logJwt.Error(err, "Parse key")
			panic(err)
		}

		err = key.Set(jwk.KeyIDKey, defaultJwtKeyName)
		if err != nil {
			logJwt.Error(err, "Set key")
			panic(err)
		}

		jsonbuf, err := json.Marshal(key)
		if err != nil {
			logJwt.Error(err, "Marshal key")
			panic(err)
		}

		jwks = `{"keys": [` + string(jsonbuf) + `]}`
	})

	return jwks
}

func SignKey() *rsa.PrivateKey {
	initSignKey.Do(func() {
		if !viper.GetBool(config_deployment.SecurityJwtEnabled) {
			logJwt.Info("Jwt integration is disabled")
			return
		}

		logJwt.Info("Jwt integration is enabled")

		privateKey, err := base64.StdEncoding.DecodeString(viper.GetString(config_deployment.SecurityJwtPrivateKey))
		if err != nil {
			logJwt.Error(err, "base64 decoding")
			panic(err)
		}

		signKey, err = gojwt.ParseRSAPrivateKeyFromPEM(privateKey)
		if err != nil {
			logJwt.Error(err, "Parse key")
			panic(err)
		}
	})

	return signKey
}

func CalculateExpirationDate(expirationDateStr string) (unixExpirationDate int64, err error) {
	if expirationDateStr == "" {
		expirationDateStr = viper.GetString(viper.GetString(config_deployment.SecurityJwtExpDatetime))
	}

	var expirationDate time.Time
	if expirationDateStr != "" {
		expirationDate, err = time.Parse(expirationDateLayout, expirationDateStr)

		if err != nil {
			return 0, err
		}

		maxExpirationDate := time.Now().Add(viper.GetDuration(config_deployment.SecurityJwtMaxTtlMinutes) * time.Minute)

		if expirationDate.After(maxExpirationDate) {
			expirationDate = maxExpirationDate
		}

		return expirationDate.Unix(), nil
	}

	expirationDate = time.Now().Add(viper.GetDuration(config_deployment.SecurityJwtTtlMinutes) * time.Minute)

	return expirationDate.Unix(), err
}

func GenerateModelToken(roleName string, expirationDateUnix int64) (string, error) {
	token := jwt.New()

	if err := token.Set(jwt.IssuerKey, defaultIss); err != nil {
		return "", err
	}
	if err := token.Set(jwt.SubjectKey, defaultSub); err != nil {
		return "", err
	}
	if err := token.Set(jwt.AudienceKey, roleName); err != nil {
		return "", err
	}
	if err := token.Set(jwt.ExpirationKey, expirationDateUnix); err != nil {
		return "", err
	}
	if err := token.Set(jwt.IssuedAtKey, time.Now()); err != nil {
		return "", err
	}

	bytesToken, err := token.Sign(jwa.RS256, SignKey())
	if err != nil {
		panic(err)
	}

	return string(bytesToken), nil
}
