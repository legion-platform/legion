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

package legion

import (
	"crypto/sha512"
	"encoding/base64"
	"encoding/json"
	"fmt"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	knservingv1alpha1 "github.com/knative/serving/pkg/apis/serving/v1alpha1"
)

const (
	LastAppliedHashAnnotation = "operator.legion.org/last-applied-hash"
)

func GenerateConnectionSecretName(vcsName string) string {
	return fmt.Sprintf("%s-vcs", vcsName)
}

func GeneratePackageResultCMName(mpID string) string {
	return fmt.Sprintf("%s-result", mpID)
}

// Compute hash and store it in the annotations
func StoreHash(obj metav1.Object) error {
	h := sha512.New()
	jsonData, err := json.Marshal(obj)
	if err != nil {
		return err
	}
	_, err = h.Write(jsonData)
	if err != nil {
		return err
	}

	annotations := map[string]string{}
	if obj.GetAnnotations() != nil {
		for k, v := range obj.GetAnnotations() {
			annotations[k] = v
		}
	}
	annotations[LastAppliedHashAnnotation] = base64.StdEncoding.EncodeToString(h.Sum(nil))

	obj.SetAnnotations(annotations)

	return nil
}

// Compute hash and store it in the annotations
func StoreHashKnative(obj *knservingv1alpha1.Configuration) error {
	h := sha512.New()
	jsonData, err := json.Marshal(obj)
	if err != nil {
		return err
	}

	_, err = h.Write(jsonData)
	if err != nil {
		return err
	}

	annotations := map[string]string{}
	if obj.GetAnnotations() != nil {
		for k, v := range obj.GetAnnotations() {
			annotations[k] = v
		}
	}
	annotations[LastAppliedHashAnnotation] = base64.StdEncoding.EncodeToString(h.Sum(nil))

	obj.SetAnnotations(annotations)

	return nil
}

func ObjsEqualByHash(firstObj, secondObj metav1.Object) bool {
	return firstObj.GetAnnotations()[LastAppliedHashAnnotation] == secondObj.GetAnnotations()[LastAppliedHashAnnotation]
}
