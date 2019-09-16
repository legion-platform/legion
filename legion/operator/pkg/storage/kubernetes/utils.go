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
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"go.uber.org/multierr"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/selection"
	"reflect"
)

func TransformFilter(filter interface{}, tagKey string) (selector labels.Selector, err error) {
	if filter == nil {
		return nil, nil
	}

	labelSelector := labels.NewSelector()

	elem := reflect.ValueOf(filter).Elem()
	for i := 0; i < elem.NumField(); i++ {
		value := elem.Field(i).Interface().([]string)
		var operator selection.Operator
		if len(value) > 1 {
			operator = selection.In
		} else if len(value) == 1 {
			if value[0] == "*" {
				continue
			}
			operator = selection.Equals
		} else {
			continue
		}

		name := elem.Type().Field(i).Tag.Get(tagKey)
		requirement, err := labels.NewRequirement(name, operator, value)
		if err != nil {
			return nil, err
		}

		labelSelector = labelSelector.Add(*requirement)
	}

	return labelSelector, nil
}

type ListOptions struct {
	Filter interface{}
	Page   *int
	Size   *int
}

type ListOption func(*ListOptions)

func ListFilter(filter interface{}) ListOption {
	return func(args *ListOptions) {
		args.Filter = filter
	}
}

func Page(page int) ListOption {
	return func(args *ListOptions) {
		args.Page = &page
	}
}

func Size(size int) ListOption {
	return func(args *ListOptions) {
		args.Size = &size
	}
}

func ConvertLegionResourcesToK8s(requirements *v1alpha1.ResourceRequirements) (depResources corev1.ResourceRequirements, err error) {
	if requirements != nil {
		reqLimits := requirements.Limits
		if reqLimits != nil {
			depResources.Limits = corev1.ResourceList{}

			if reqLimits.Memory != nil {
				var validationErr error
				depResources.Limits[corev1.ResourceMemory], validationErr = resource.ParseQuantity(*reqLimits.Memory)

				if validationErr != nil {
					err = multierr.Append(err, fmt.Errorf("validation of memory request is failed: %s", validationErr.Error()))
				}
			}

			if reqLimits.Cpu != nil {
				var validationErr error
				depResources.Limits[corev1.ResourceCPU], validationErr = resource.ParseQuantity(*reqLimits.Cpu)

				if validationErr != nil {
					err = multierr.Append(err, fmt.Errorf("validation of cpu request is failed: %s", validationErr.Error()))
				}
			}

			if reqLimits.Gpu != nil {
				// TODO: remove hardcode
				var validationErr error
				depResources.Limits["nvidia.com/gpu"], validationErr = resource.ParseQuantity(*reqLimits.Gpu)

				if validationErr != nil {
					err = multierr.Append(err, fmt.Errorf("validation of gpu request is failed: %s", validationErr.Error()))
				}
			}
		}

		reqRequests := requirements.Requests
		if reqLimits != nil {
			depResources.Requests = corev1.ResourceList{}

			if reqRequests.Memory != nil {
				var validationErr error
				depResources.Requests[corev1.ResourceMemory], validationErr = resource.ParseQuantity(*reqRequests.Memory)

				if validationErr != nil {
					err = multierr.Append(err, fmt.Errorf("validation of memory limit is failed: %s", validationErr.Error()))
				}
			}

			if reqRequests.Cpu != nil {
				var validationErr error
				depResources.Requests[corev1.ResourceCPU], validationErr = resource.ParseQuantity(*reqRequests.Cpu)

				if validationErr != nil {
					err = multierr.Append(err, fmt.Errorf("validation of cpu limit is failed: %s", validationErr.Error()))
				}
			}

			if reqRequests.Gpu != nil {
				// TODO: remove hardcode
				var validationErr error
				depResources.Limits["nvidia.com/gpu"], validationErr = resource.ParseQuantity(*reqRequests.Gpu)

				if validationErr != nil {
					err = multierr.Append(err, fmt.Errorf("validation of gpu limit is failed: %s", validationErr.Error()))
				}
			}
		}
	}

	return
}
