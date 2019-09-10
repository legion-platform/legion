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

package kubernetes

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"k8s.io/api/core/v1"
	"reflect"
	"testing"
)

func TestConvertLegionResourcesToK8s(t *testing.T) {
	type args struct {
		requirements *v1alpha1.ResourceRequirements
	}
	tests := []struct {
		name             string
		args             args
		wantDepResources v1.ResourceRequirements
		wantErr          bool
	}{
		// TODO: Add test cases.
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotDepResources, err := ConvertLegionResourcesToK8s(tt.args.requirements)
			if (err != nil) != tt.wantErr {
				t.Errorf("ConvertLegionResourcesToK8s() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !reflect.DeepEqual(gotDepResources, tt.wantDepResources) {
				t.Errorf("ConvertLegionResourcesToK8s() gotDepResources = %v, want %v", gotDepResources, tt.wantDepResources)
			}
		})
	}
}
