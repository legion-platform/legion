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
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	. "github.com/onsi/gomega"
	"github.com/spf13/viper"
	"testing"
	"time"
)

func TestCalculateExpirationDate(t *testing.T) {
	g := NewWithT(t)

	currentTime := time.Now()

	unixExpirationDate, err := CalculateExpirationDate(currentTime.Format(expirationDateLayout))
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(currentTime.Unix()).To(Equal(unixExpirationDate))
}

func TestDefaultExpDateTime(t *testing.T) {
	g := NewWithT(t)

	currentTime := time.Now()
	viper.Set(legion.JwtExpDatetime, currentTime.Format(expirationDateLayout))

	unixExpirationDate, err := CalculateExpirationDate("")
	g.Expect(err).NotTo(HaveOccurred())
	g.Expect(currentTime.Unix()).To(Equal(unixExpirationDate))
}

func TestExpDateTimeIncorrectFormat(t *testing.T) {
	g := NewWithT(t)

	_, err := CalculateExpirationDate("2006 01 02")
	g.Expect(err).To(HaveOccurred())
}
