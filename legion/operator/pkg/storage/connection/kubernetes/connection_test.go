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

package kubernetes_test

import (
	"testing"
)

// TODO: add more tests

func TestStorageConnection(t *testing.T) {
	//key := types.NamespacedName{
	//	Id:      "foo",
	//	Namespace: "default",
	//}
	//created := &v1alpha1.ConnectionName{
	//	metav1.ObjectMeta: metav1.ObjectMeta{
	//		Id:      "foo",
	//		Namespace: "default",
	//	}}
	//g := gomega.NewGomegaWithT(t)
	//
	//// Test Create
	//fetched := &v1alpha1.ConnectionName{}
	//g.Expect(c.Create(context.TODO(), created)).NotTo(gomega.HaveOccurred())
	//
	//g.Expect(c.GetConnection(context.TODO(), key, fetched)).NotTo(gomega.HaveOccurred())
	//g.Expect(fetched).To(gomega.Equal(created))
	//
	//// Test Updating the Labels
	//updated := fetched.DeepCopy()
	//updated.Labels = map[string]string{"hello": "world"}
	//g.Expect(c.Update(context.TODO(), updated)).NotTo(gomega.HaveOccurred())
	//
	//g.Expect(c.GetConnection(context.TODO(), key, fetched)).NotTo(gomega.HaveOccurred())
	//g.Expect(fetched).To(gomega.Equal(updated))
	//
	//// Test Delete
	//g.Expect(c.Delete(context.TODO(), fetched)).NotTo(gomega.HaveOccurred())
	//g.Expect(c.GetConnection(context.TODO(), key, fetched)).To(gomega.HaveOccurred())
}
