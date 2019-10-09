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
	knservingv1alpha1 "github.com/knative/serving/pkg/apis/serving/v1alpha1"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	"github.com/legion-platform/legion/legion/operator/pkg/repository/kubernetes"
	. "github.com/onsi/gomega"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"strconv"
	"testing"
	"time"
)

var (
	timeout          = time.Second * 5
	image            = "test/image:123"
	mdName           = "test-md"
	mdMinReplicas    = int32(1)
	mdMaxReplicas    = int32(2)
	mdReadinessDelay = int32(33)
	mdLivenessDelay  = int32(44)
	mdNamespace      = "default"
)

var (
	c               client.Client
	expectedRequest = reconcile.Request{
		NamespacedName: types.NamespacedName{
			Name:      mdName,
			Namespace: mdNamespace,
		},
	}
	reqMem      = "111Mi"
	reqCPU      = "111m"
	limMem      = "222Mi"
	mdResources = &legionv1alpha1.ResourceRequirements{
		Limits: &legionv1alpha1.ResourceList{
			CPU:    nil,
			Memory: &limMem,
		},
		Requests: &legionv1alpha1.ResourceList{
			CPU:    &reqCPU,
			Memory: &reqMem,
		},
	}
)

func TestReconcile(t *testing.T) {
	g := NewGomegaWithT(t)
	md := &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{Name: mdName, Namespace: mdNamespace},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image:                      image,
			MinReplicas:                &mdMinReplicas,
			MaxReplicas:                &mdMaxReplicas,
			ReadinessProbeInitialDelay: &mdReadinessDelay,
			LivenessProbeInitialDelay:  &mdLivenessDelay,
			Resources:                  mdResources,
		},
	}

	mgr, err := manager.New(cfg, manager.Options{})
	g.Expect(err).NotTo(HaveOccurred())
	c = mgr.GetClient()

	recFn, requests := SetupTestReconcile(newConfigurableReconciler(mgr))
	g.Expect(add(mgr, recFn)).NotTo(HaveOccurred())

	stopMgr, mgrStopped := StartTestManager(mgr, g)

	defer func() {
		close(stopMgr)
		mgrStopped.Wait()
	}()

	err = c.Create(context.TODO(), md)

	g.Expect(err).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), md)

	g.Eventually(requests, timeout).Should(Receive(Equal(expectedRequest)))

	configuration := &knservingv1alpha1.Configuration{}
	configurationKey := types.NamespacedName{Name: knativeConfigurationName(md), Namespace: mdNamespace}
	g.Expect(c.Get(context.TODO(), configurationKey, configuration)).ToNot(HaveOccurred())

	configurationAnnotations := configuration.Spec.Template.ObjectMeta.Annotations
	g.Expect(configurationAnnotations).Should(HaveLen(5))
	g.Expect(configurationAnnotations).Should(HaveKeyWithValue(
		knativeMinReplicasKey, strconv.Itoa(int(mdMinReplicas)),
	))
	g.Expect(configurationAnnotations).Should(HaveKeyWithValue(
		knativeMaxReplicasKey, strconv.Itoa(int(mdMaxReplicas)),
	))
	g.Expect(configurationAnnotations).Should(HaveKeyWithValue(
		knativeAutoscalingTargetKey, knativeAutoscalingTargetDefaultValue,
	))
	g.Expect(configurationAnnotations).Should(HaveKeyWithValue(
		knativeAutoscalingClass, defaultKnativeAutoscalingClass,
	))
	g.Expect(configurationAnnotations).Should(HaveKeyWithValue(
		knativeAutoscalingMetric, defaultKnativeAutoscalingMetric,
	))

	configurationLabels := configuration.Spec.Template.ObjectMeta.Labels
	g.Expect(configurationLabels).Should(HaveLen(1))
	g.Expect(configurationLabels).Should(HaveKeyWithValue(modelNameAnnotationKey, md.Name))

	podSpec := configuration.Spec.Template.Spec
	g.Expect(podSpec.Containers).To(HaveLen(1))
	g.Expect(*podSpec.TimeoutSeconds).To(Equal(defaultTerminationPeriod))

	containerSpec := podSpec.Containers[0]

	mdResources, err := kubernetes.ConvertLegionResourcesToK8s(md.Spec.Resources)
	g.Expect(err).ShouldNot(HaveOccurred())
	g.Expect(containerSpec.Resources).To(Equal(mdResources))

	g.Expect(containerSpec.Image).To(Equal(image))
	g.Expect(containerSpec.Ports).To(HaveLen(1))
	g.Expect(containerSpec.Ports).To(HaveLen(1))
	g.Expect(containerSpec.Ports[0].Name).To(Equal(defaultPortName))
	g.Expect(containerSpec.Ports[0].ContainerPort).To(Equal(defaultModelPort))
	g.Expect(containerSpec.LivenessProbe).NotTo(BeNil())
	g.Expect(containerSpec.LivenessProbe.InitialDelaySeconds).To(Equal(mdLivenessDelay))
	g.Expect(containerSpec.ReadinessProbe).NotTo(BeNil())
	g.Expect(containerSpec.ReadinessProbe.InitialDelaySeconds).To(Equal(mdReadinessDelay))
}
