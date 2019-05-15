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

package modeldeployment

import (
	"context"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	. "github.com/onsi/gomega"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"testing"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

var (
	timeout          = time.Second * 5
	mdImage          = "test/image:123"
	mdName           = "test-md"
	mdReplicas       = int32(2)
	mdReadinessDelay = int32(2)
	mdLivenessDelay  = int32(2)
	mdNamespace      = "default"
	modelId          = "id-1"
	modelVersion     = "2"
	k8sName          = "model-id-1-2"
)

var (
	c               client.Client
	expectedRequest = reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      mdName,
			Namespace: mdNamespace,
		},
	}
	imageLabels = map[string]string{
		legion.DomainModelId:      modelId,
		legion.DomainModelVersion: modelVersion,
	}
	mdResources = &corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("128m"),
			"memory": resource.MustParse("128Mi"),
		},
	}
)

func mockExtractLabel(image string) (map[string]string, error) {
	return imageLabels, nil
}

func TestReconcile(t *testing.T) {
	g := NewGomegaWithT(t)
	instance := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{Name: mdName, Namespace: mdNamespace},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      mdImage,
			Replicas:                   &mdReplicas,
			ReadinessProbeInitialDelay: &mdReadinessDelay,
			LivenessProbeInitialDelay:  &mdLivenessDelay,
			Resources:                  mdResources,
		},
	}

	mgr, err := manager.New(cfg, manager.Options{})
	g.Expect(err).NotTo(HaveOccurred())
	c = mgr.GetClient()

	recFn, requests := SetupTestReconcile(newConfigurableReconciler(mgr, mockExtractLabel))
	g.Expect(add(mgr, recFn)).NotTo(HaveOccurred())

	stopMgr, mgrStopped := StartTestManager(mgr, g)

	defer func() {
		close(stopMgr)
		mgrStopped.Wait()
	}()

	// Create the ModelDeployment object and expect the Reconcile and Deployment to be created
	err = c.Create(context.TODO(), instance)

	g.Expect(err).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), instance)

	g.Eventually(requests, timeout).Should(Receive(Equal(expectedRequest)))

	modelDepKey := types.NamespacedName{
		Name:      k8sName,
		Namespace: mdNamespace,
	}
	modelDep := &appsv1.Deployment{}
	g.Eventually(func() error { return c.Get(context.TODO(), modelDepKey, modelDep) }, timeout).
		Should(Succeed())
	containers := modelDep.Spec.Template.Spec.Containers
	g.Expect(modelDep.Spec.Template.Spec.Containers).To(HaveLen(1))
	g.Expect(containers[0].Image).To(Equal(mdImage))

	modelServiceKey := types.NamespacedName{
		Name:      k8sName,
		Namespace: mdNamespace,
	}
	modelService := &corev1.Service{}
	g.Eventually(func() error { return c.Get(context.TODO(), modelServiceKey, modelService) }, timeout).
		Should(Succeed())
}
