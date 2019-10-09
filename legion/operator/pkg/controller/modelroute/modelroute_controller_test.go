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

package modelroute

import (
	v1alpha3_istio_api "github.com/aspenmesh/istio-client-go/pkg/apis/networking/v1alpha3"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	. "github.com/onsi/gomega"
	"golang.org/x/net/context"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sync"
	"testing"
	"time"
)

const (
	mrName  = "test-mr"
	mrURL   = "/test/url"
	timeout = time.Second * 5
)

var (
	testNamespace = "default"
	md1           = &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "md-1-for-tests",
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image: "test/image:1",
		},
		Status: legionv1alpha1.ModelDeploymentStatus{
			ServiceURL:       "md-1-for-tests.default.svc",
			LastRevisionName: "md-1-for-tests-rev",
			State:            legionv1alpha1.ModelDeploymentStateReady,
		},
	}
	md2 = &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "md-2-for-tests",
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image: "test/image:1",
		},
		Status: legionv1alpha1.ModelDeploymentStatus{
			ServiceURL:       "md-2-for-tests.default.svc",
			LastRevisionName: "md-2-for-tests-rev",
			State:            legionv1alpha1.ModelDeploymentStateReady,
		},
	}
	mdNotReady = &legionv1alpha1.ModelDeployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "md-not-ready",
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelDeploymentSpec{
			Image: "test/image:1",
		},
		Status: legionv1alpha1.ModelDeploymentStatus{
			ServiceURL:       "",
			LastRevisionName: "",
		},
	}
	c               client.Client
	expectedRequest = reconcile.Request{NamespacedName: types.NamespacedName{Name: mrName, Namespace: testNamespace}}
	mrKey           = types.NamespacedName{Name: mrName, Namespace: testNamespace}
)

func setUp(g *GomegaWithT) (chan struct{}, *sync.WaitGroup, chan reconcile.Request) {
	mgr, err := manager.New(cfg, manager.Options{})
	g.Expect(err).NotTo(HaveOccurred())
	c = mgr.GetClient()

	md1.ObjectMeta.ResourceVersion = ""
	md2.ObjectMeta.ResourceVersion = ""
	mdNotReady.ObjectMeta.ResourceVersion = ""

	if err := c.Create(context.TODO(), md1); err != nil {
		panic(err)
	}

	if err := c.Create(context.TODO(), md2); err != nil {
		panic(err)
	}

	if err := c.Create(context.TODO(), mdNotReady); err != nil {
		panic(err)
	}

	recFn, requests := SetupTestReconcile(newReconciler(mgr))
	g.Expect(add(mgr, recFn)).NotTo(HaveOccurred())

	stopMgr, mgrStopped := StartTestManager(mgr, g)

	return stopMgr, mgrStopped, requests
}

func teardown(stopMgr chan struct{}, mgrStopped *sync.WaitGroup) {
	_ = c.Delete(context.TODO(), mdNotReady)
	_ = c.Delete(context.TODO(), md2)
	_ = c.Delete(context.TODO(), md1)

	close(stopMgr)
	mgrStopped.Wait()
}

func TestBasicReconcile(t *testing.T) {
	g := NewGomegaWithT(t)
	stopMgr, mgrStopped, requests := setUp(g)
	defer teardown(stopMgr, mgrStopped)

	weight := int32(100)
	mr := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelRouteSpec{
			URLPrefix: mrURL,
			Mirror:    &md1.ObjectMeta.Name,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{
				{
					Name:   md2.ObjectMeta.Name,
					Weight: &weight,
				},
			},
		},
	}

	err := c.Create(context.TODO(), mr)
	g.Expect(err).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mr)

	g.Eventually(requests, timeout).Should(Receive(Equal(expectedRequest)))

	g.Expect(c.Get(context.TODO(), mrKey, mr)).ToNot(HaveOccurred())
	g.Expect(mr.Status.State).To(Equal(legionv1alpha1.ModelRouteStateReady))

	vs := &v1alpha3_istio_api.VirtualService{}
	vsKey := types.NamespacedName{Name: VirtualServiceName(mr), Namespace: testNamespace}
	g.Expect(c.Get(context.TODO(), vsKey, vs)).ToNot(HaveOccurred())

	g.Expect(vs.Spec.Http).To(HaveLen(2))

	for _, host := range vs.Spec.Http {
		g.Expect(host.Mirror).ToNot(BeNil())
		g.Expect(host.Mirror.Host).To(Equal(md1.Status.ServiceURL))

		g.Expect(host.Route).To(HaveLen(1))
		g.Expect(host.Route[0].Destination.Host).To(Equal(md2.Status.ServiceURL))
		g.Expect(host.Route[0].Weight).To(Equal(weight))
	}
}

func TestEmptyMirror(t *testing.T) {
	g := NewGomegaWithT(t)
	stopMgr, mgrStopped, requests := setUp(g)
	defer teardown(stopMgr, mgrStopped)

	weight := int32(100)
	mr := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelRouteSpec{
			URLPrefix: mrURL,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{
				{
					Name:   md2.ObjectMeta.Name,
					Weight: &weight,
				},
			},
		},
	}

	err := c.Create(context.TODO(), mr)
	g.Expect(err).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mr)

	g.Eventually(requests, timeout).Should(Receive(Equal(expectedRequest)))

	g.Expect(c.Get(context.TODO(), mrKey, mr)).ToNot(HaveOccurred())
	g.Expect(mr.Status.State).To(Equal(legionv1alpha1.ModelRouteStateReady))

	vs := &v1alpha3_istio_api.VirtualService{}
	vsKey := types.NamespacedName{Name: VirtualServiceName(mr), Namespace: testNamespace}
	g.Expect(c.Get(context.TODO(), vsKey, vs)).ToNot(HaveOccurred())

	g.Expect(vs.Spec.Http).To(HaveLen(2))

	for _, host := range vs.Spec.Http {
		g.Expect(host.Mirror).To(BeNil())
	}
}

func TestNotReadyEmptyMirror(t *testing.T) {
	g := NewGomegaWithT(t)
	stopMgr, mgrStopped, requests := setUp(g)
	defer teardown(stopMgr, mgrStopped)

	weight := int32(100)
	mr := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelRouteSpec{
			URLPrefix: mrURL,
			Mirror:    &mdNotReady.ObjectMeta.Name,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{
				{
					Name:   md2.ObjectMeta.Name,
					Weight: &weight,
				},
			},
		},
	}

	err := c.Create(context.TODO(), mr)
	g.Expect(err).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mr)

	g.Eventually(requests, timeout).Should(Receive(Equal(expectedRequest)))

	g.Expect(c.Get(context.TODO(), mrKey, mr)).ToNot(HaveOccurred())
	g.Expect(mr.Status.State).To(Equal(legionv1alpha1.ModelRouteStateProcessing))

	vs := &v1alpha3_istio_api.VirtualService{}
	vsKey := types.NamespacedName{Name: VirtualServiceName(mr), Namespace: testNamespace}
	g.Expect(c.Get(context.TODO(), vsKey, vs)).ToNot(HaveOccurred())

	g.Expect(vs.Spec.Http).To(HaveLen(2))

	for _, host := range vs.Spec.Http {
		g.Expect(host.Mirror).To(BeNil())
	}
}

func TestMultipleTargets(t *testing.T) {
	g := NewGomegaWithT(t)
	stopMgr, mgrStopped, requests := setUp(g)
	defer teardown(stopMgr, mgrStopped)

	weight := int32(50)
	mr := &legionv1alpha1.ModelRoute{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mrName,
			Namespace: testNamespace,
		},
		Spec: legionv1alpha1.ModelRouteSpec{
			URLPrefix: mrURL,
			ModelDeploymentTargets: []legionv1alpha1.ModelDeploymentTarget{
				{
					Name:   md1.ObjectMeta.Name,
					Weight: &weight,
				},
				{
					Name:   md2.ObjectMeta.Name,
					Weight: &weight,
				},
			},
		},
	}

	err := c.Create(context.TODO(), mr)
	g.Expect(err).NotTo(HaveOccurred())
	defer c.Delete(context.TODO(), mr)

	g.Eventually(requests, timeout).Should(Receive(Equal(expectedRequest)))

	g.Expect(c.Get(context.TODO(), mrKey, mr)).ToNot(HaveOccurred())
	g.Expect(mr.Status.State).To(Equal(legionv1alpha1.ModelRouteStateReady))

	vs := &v1alpha3_istio_api.VirtualService{}
	vsKey := types.NamespacedName{Name: VirtualServiceName(mr), Namespace: testNamespace}
	g.Expect(c.Get(context.TODO(), vsKey, vs)).ToNot(HaveOccurred())

	g.Expect(vs.Spec.Http).To(HaveLen(2))

	for _, host := range vs.Spec.Http {
		g.Expect(host.Route).To(HaveLen(2))

		g.Expect(host.Route[0].Destination.Host).To(Equal(md1.Status.ServiceURL))
		g.Expect(host.Route[0].Weight).To(Equal(weight))

		g.Expect(host.Route[1].Destination.Host).To(Equal(md2.Status.ServiceURL))
		g.Expect(host.Route[1].Weight).To(Equal(weight))
	}
}
