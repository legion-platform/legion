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

package connection_test

import (
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	conn_route "github.com/legion-platform/legion/legion/operator/pkg/webserver/routes/v1/connection"
	. "github.com/onsi/gomega"
	"testing"
)

func TestIDGeneration(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		Spec: v1alpha1.ConnectionSpec{
			Type:      "not-existed",
			URI:       connURI,
			Reference: connReference,
			KeySecret: creds,
		},
	}
	_ = conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(conn.ID).ShouldNot(BeEmpty())
}

func TestEmptyURL(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		Spec: v1alpha1.ConnectionSpec{
			Type:      "not-existed",
			Reference: connReference,
			KeySecret: creds,
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).Should(HaveOccurred())
	g.Expect(err.Error()).Should(ContainSubstring(conn_route.EmptyURIErrorMessage))
}

func TestUnknownTypeType(t *testing.T) {
	g := NewGomegaWithT(t)

	connType := v1alpha1.ConnectionType("not-existed")
	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connType,
			URI:       connURI,
			Reference: connReference,
			KeySecret: creds,
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(fmt.Sprintf(
		conn_route.UnknownTypeErrorMessage, connType, connection.AllConnectionTypes,
	)))
}

func TestGitTypeKeySecretBase64(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.GITType,
			URI:       connURI,
			Reference: connReference,
			KeySecret: "not-base64-encoding",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(fmt.Sprintf(
		conn_route.GitTypeKeySecretErrorMessage, "illegal base64 data",
	)))
}

func TestGitTypePublicKeyBase64(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.GITType,
			URI:       connURI,
			Reference: connReference,
			PublicKey: "not-base64-encoding",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(fmt.Sprintf(
		conn_route.GitTypePublicKeyErrorMessage, "illegal base64 data",
	)))
}

func TestDockerTypeUsername(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:     connection.DockerType,
			URI:      connURI,
			Password: "password",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(conn_route.DockerTypeUsernameErrorMessage))
}

func TestDockerTypePassword(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:     connection.DockerType,
			URI:      connURI,
			Username: "username",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(conn_route.DockerTypePasswordErrorMessage))
}

func TestGcsTypeRegion(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.GcsType,
			URI:       connURI,
			Role:      "role",
			KeySecret: "key-secret",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(conn_route.GcsTypeRegionErrorMessage))
}

func TestGcsTypeRoleAndSecretMissed(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:   connection.GcsType,
			URI:    connURI,
			Region: "username",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(conn_route.GcsTypeRoleAndKeySecretEmptyErrorMessage))
}

func TestGcsTypeRoleAndSecretPresent(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.GcsType,
			URI:       connURI,
			Region:    "username",
			Role:      "role",
			KeySecret: "key-secret",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(conn_route.GcsTypeRoleAndKeySecretEmptyErrorMessage))
}

func TestS3TypeRegion(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.S3Type,
			URI:       connURI,
			Role:      "role",
			KeySecret: "key-secret",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(conn_route.S3TypeRegionErrorMessage))
}

func TestS3TypeRoleAndSecretMissed(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:   connection.S3Type,
			URI:    connURI,
			Region: "username",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(conn_route.S3TypeRoleAndKeySecretEmptyErrorMessage))
}

func TestS3TypeRoleAndSecretPresent(t *testing.T) {
	g := NewGomegaWithT(t)

	conn := &connection.Connection{
		ID: connID,
		Spec: v1alpha1.ConnectionSpec{
			Type:      connection.S3Type,
			URI:       connURI,
			Region:    "username",
			Role:      "role",
			KeySecret: "key-secret",
		},
	}
	err := conn_route.NewConnValidator().ValidatesAndSetDefaults(conn)
	g.Expect(err).To(HaveOccurred())
	g.Expect(err.Error()).To(ContainSubstring(conn_route.S3TypeRoleAndKeySecretEmptyErrorMessage))
}
