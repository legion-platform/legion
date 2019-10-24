/*
 * Copyright 2019 EPAM Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package modeldeployment

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/go-logr/logr"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	dep_conf "github.com/legion-platform/legion/legion/operator/pkg/config/deployment"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/legion-platform/legion/legion/operator/pkg/utils/aws"
	"github.com/spf13/viper"
	corev1 "k8s.io/api/core/v1"
	k8serrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"net/url"
	"reflect"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"time"
)

const (
	DockerConfigSecretKey                = ".dockercfg"
	PeriodUpdatingDockerConnectionToken  = 6 * time.Hour
	PeriodVerifyingDockerConnectionToken = 10 * time.Minute
)

type DockerSecret struct {
	Email    string `json:"email"`
	Username string `json:"username"`
	Password string `json:"password"`
}

// If deployment image is stored on a private Docker repository,
// then we should create a secret for this repository.
// Read more about it:
// https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/
func (r *ReconcileModelDeployment) reconcileDeploymentPullConnection(
	log logr.Logger,
	md *legionv1alpha1.ModelDeployment,
) error {
	mdConnID := *md.Spec.ImagePullConnectionID
	if len(*md.Spec.ImagePullConnectionID) == 0 {
		log.Info("Model deployment connection name is empty. Skip reconcile deployment secrets")

		return nil
	}

	log = log.WithValues(legion.ConnectionIDLogPrefix, mdConnID)

	mdConn, err := r.connRepo.GetConnection(mdConnID)
	if err != nil {
		log.Error(err, "Cannot retrieve connection")

		return err
	}

	switch mdConn.Spec.Type {
	case connection.DockerType:
		return r.reconcileDockerDeploymentSecret(log, md, mdConn, DockerSecret{
			Email:    "",
			Username: mdConn.Spec.Username,
			Password: mdConn.Spec.Password,
		})
	case connection.EcrType:
		// Check whether the credentials needs to be updated.
		if md.Status.LastCredsUpdatedTime != nil &&
			time.Until(md.Status.LastCredsUpdatedTime.Add(
				PeriodUpdatingDockerConnectionToken,
			)) < PeriodUpdatingDockerConnectionToken {

			log.Info("Skip updating token", "last_updated_time", md.Status.LastCredsUpdatedTime)

			return nil
		}

		user, password, err := aws.ExtractEcrCreds(mdConn.Spec)
		if err != nil {
			log.Error(err, "Can not create a token for ecr")

			return err
		}

		log.Info("Deployment token was updated")

		err = r.reconcileDockerDeploymentSecret(log, md, mdConn, DockerSecret{
			Email:    "",
			Username: user,
			Password: password,
		})
		if err != nil {
			return err
		}

		md.Status.LastCredsUpdatedTime = &metav1.Time{Time: time.Now()}

		return r.Update(context.TODO(), md)
	default:
		// impossible situation
		return fmt.Errorf("unexpected connection type: %s", mdConn.Spec.Type)
	}
}

func (r *ReconcileModelDeployment) reconcileDockerDeploymentSecret(
	log logr.Logger,
	md *legionv1alpha1.ModelDeployment,
	conn *connection.Connection,
	dockerSecret DockerSecret,
) error {
	// We assume that docker connection URI does not contains schema
	// Golang URI parser fails if URI doesn't contain schema. So we add it manually
	dockerURI, err := url.Parse("https://" + conn.Spec.URI)
	if err != nil {
		log.Error(err, "can not parse the connection URI", "URI", conn.Spec.URI)

		return err
	}

	encodedDockerSecret := map[string]DockerSecret{
		dockerURI.Host: dockerSecret,
	}

	dockerSecretBytes, err := json.Marshal(encodedDockerSecret)
	if err != nil {
		log.Error(err, "json unmarshal docker secret")

		return err
	}

	depSecretName := legion.GenerateDeploymentConnectionSecretName(md.Name)
	expectedSecret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      depSecretName,
			Namespace: viper.GetString(dep_conf.Namespace),
		},
		Data: map[string][]byte{
			DockerConfigSecretKey: dockerSecretBytes,
		},
		Type: corev1.SecretTypeDockercfg,
	}

	if err := controllerutil.SetControllerReference(md, expectedSecret, r.scheme); err != nil {
		return err
	}

	var foundSecret = &corev1.Secret{}
	secretNamespacedName := types.NamespacedName{Name: depSecretName, Namespace: viper.GetString(dep_conf.Namespace)}
	err = r.Get(context.TODO(), secretNamespacedName, foundSecret)
	switch {
	case err != nil && k8serrors.IsNotFound(err):
		err = r.Create(context.TODO(), expectedSecret)
		if err != nil {
			// If error during secret creation
			log.Error(err, "Kubernetes secret creation")
			return err
		}

		log.Info(fmt.Sprintf("Created %s deployment secret", expectedSecret.Name))
	case err != nil:
		log.Error(err, "Fetching Secret")

		return err
	case !reflect.DeepEqual(foundSecret.Data, expectedSecret.Data):
		foundSecret.Data = expectedSecret.Data

		log.Info("Updating Secret")
		err = r.Update(context.TODO(), foundSecret)
		if err != nil {
			return err
		}
	}

	return r.reconcileDockerServiceAccount(log, md)
}

func (r *ReconcileModelDeployment) reconcileDockerServiceAccount(
	log logr.Logger,
	md *legionv1alpha1.ModelDeployment,
) error {
	depSecretName := legion.GenerateDeploymentConnectionSecretName(md.Name)
	dockerServiceAccount := &corev1.ServiceAccount{
		ObjectMeta: metav1.ObjectMeta{
			Name:      depSecretName,
			Namespace: viper.GetString(dep_conf.Namespace),
		},
		ImagePullSecrets: []corev1.LocalObjectReference{
			{
				Name: depSecretName,
			},
		},
	}

	if err := controllerutil.SetControllerReference(md, dockerServiceAccount, r.scheme); err != nil {
		return err
	}

	var foundDockerServiceAccount = &corev1.ServiceAccount{}
	dockerServiceAccountName := types.NamespacedName{
		Name:      depSecretName,
		Namespace: viper.GetString(dep_conf.Namespace),
	}
	if err := r.Get(
		context.TODO(),
		dockerServiceAccountName,
		foundDockerServiceAccount,
	); err != nil && k8serrors.IsNotFound(err) {
		err = r.Create(context.TODO(), dockerServiceAccount)
		if err != nil {
			// If error during secret creation
			log.Error(err, "Kubernetes service account creation")
			return err
		}

		log.Info(fmt.Sprintf("Created %s service account", dockerServiceAccount.Name))

		return nil
	} else if err != nil {
		log.Error(err, "Fetching Service account")
		return err
	}

	if !reflect.DeepEqual(dockerServiceAccount.ImagePullSecrets, foundDockerServiceAccount.ImagePullSecrets) {
		foundDockerServiceAccount.ImagePullSecrets = dockerServiceAccount.ImagePullSecrets

		log.Info("Updating Service account")
		err := r.Update(context.TODO(), foundDockerServiceAccount)
		if err != nil {
			return err
		}
	}

	return nil
}
