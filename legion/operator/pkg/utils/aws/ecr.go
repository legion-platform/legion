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

package aws

import (
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/endpoints"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/awslabs/amazon-ecr-credential-helper/ecr-login/api"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("legion-ecr")

// Retrieves the docker credentials from ecr registry
func ExtractEcrCreds(connSpec legionv1alpha1.ConnectionSpec) (user string, password string, err error) {
	registry, err := api.ExtractRegistry(connSpec.URI)
	if err != nil {
		log.Error(err, "Error parsing the serverURL", "serverURL", connSpec.URI)
		return
	}

	var client api.Client
	if registry.FIPS {
		client, err = newClientWithFipsEndpoint(connSpec)
		if err != nil {
			log.Error(err, "Error resolving FIPS endpoint")

			return "", "", err
		}
	} else {
		client, err = newClientFromRegion(connSpec)
		if err != nil {
			log.Error(err, "Error creating client")

			return "", "", err
		}
	}

	auth, err := client.GetCredentials(connSpec.URI)
	if err != nil {
		log.Error(err, "Error retrieving credentials")

		return "", "", err
	}
	return auth.Username, auth.Password, nil
}

func newSession(connSpec legionv1alpha1.ConnectionSpec) (*session.Session, error) {
	return session.NewSession(&aws.Config{
		Region:      aws.String(connSpec.Region),
		Credentials: credentials.NewStaticCredentials(connSpec.KeyID, connSpec.KeySecret, ""),
	})
}

// NewClientFromRegion uses the region to create the client
func newClientFromRegion(connSpec legionv1alpha1.ConnectionSpec) (api.Client, error) {
	awsSession, err := newSession(connSpec)
	if err != nil {
		log.Error(err, "Session creation")

		return nil, err
	}

	awsConfig := &aws.Config{Region: aws.String(connSpec.Region)}
	return api.DefaultClientFactory{}.NewClientWithOptions(api.Options{
		Session: awsSession,
		Config:  awsConfig,
	}), nil
}

// NewClientWithFipsEndpoint overrides the default ECR service endpoint in a given region to use the FIPS endpoint
func newClientWithFipsEndpoint(connSpec legionv1alpha1.ConnectionSpec) (api.Client, error) {
	awsSession, err := newSession(connSpec)
	if err != nil {
		log.Error(err, "Session creation")

		return nil, err
	}

	endpoint, err := getServiceEndpoint("ecr-fips", connSpec.Region)
	if err != nil {
		return nil, err
	}

	awsConfig := awsSession.Config.WithEndpoint(endpoint).WithRegion(connSpec.Region)
	return api.DefaultClientFactory{}.NewClientWithOptions(api.Options{
		Session: awsSession,
		Config:  awsConfig,
	}), nil
}

func getServiceEndpoint(service, region string) (string, error) {
	resolver := endpoints.DefaultResolver()
	endpoint, err := resolver.EndpointFor(service, region, func(opts *endpoints.Options) {
		opts.ResolveUnknownService = true
	})

	if err != nil {
		return "", err
	}

	return endpoint.URL, err
}
