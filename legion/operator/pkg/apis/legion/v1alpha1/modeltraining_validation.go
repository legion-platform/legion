package v1alpha1

import (
	"context"
	"errors"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/spf13/viper"
	"go.uber.org/multierr"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	k8stypes "k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var logMT = logf.Log.WithName("model_training")

const (
	mtVcsNotExistsErrorMessage = "Cannot find VCS Credential"
)

var (
	defaultTrainingResources = corev1.ResourceRequirements{
		Limits: corev1.ResourceList{
			"cpu":    resource.MustParse("256m"),
			"memory": resource.MustParse("256Mi"),
		},
		Requests: corev1.ResourceList{
			"cpu":    resource.MustParse("128m"),
			"memory": resource.MustParse("128Mi"),
		},
	}
	defaultModelFileName = "/var/legion/robot.model"
)

func (mt *ModelTraining) ValidatesAndSetDefaults(k8sClient client.Client) (err error) {
	if mt.Spec.Resources == nil {
		logMT.Info("Training resource parameter is nil. Set the default value",
			"name", mt.Name, "resources", defaultTrainingResources)
		mt.Spec.Resources = &defaultTrainingResources
	}

	if len(mt.Spec.ModelFile) == 0 {
		logMT.Info("Model file parameter is nil. Set the default value",
			"name", mt.Name, "model_file", defaultModelFileName)
		mt.Spec.ModelFile = defaultModelFileName
	}

	if len(mt.Spec.Image) == 0 {
		modelImage, toolchainErr := legion.GetToolchainImage(mt.Spec.ToolchainType)

		if toolchainErr != nil {
			err = multierr.Append(err, toolchainErr)
		} else {
			logMT.Info("Toolchain image parameter is nil. Set the default value",
				"name", mt.Name, "image", modelImage)
			mt.Spec.Image = modelImage
		}
	}

	vcsInstanceName := k8stypes.NamespacedName{
		Name:      mt.Spec.VCSName,
		Namespace: viper.GetString(legion.Namespace),
	}
	vcsCR := &VCSCredential{}
	if k8sErr := k8sClient.Get(context.TODO(), vcsInstanceName, vcsCR); k8sErr != nil {
		logMT.Error(err, mtVcsNotExistsErrorMessage)

		err = multierr.Append(err, k8sErr)
	} else {
		if len(mt.Spec.Reference) == 0 {
			if len(vcsCR.Spec.DefaultReference) == 0 {
				err = multierr.Append(err, errors.New(fmt.Sprintf(
					"You should specify a reference of Model Training explicitly. Because %s does not have default reference",
					vcsCR.Name),
				))
			}

			logMT.Info("VCS reference parameter is nil. Set the default value",
				"name", mt.Name, "reference", vcsCR.Spec.DefaultReference)
			mt.Spec.Reference = vcsCR.Spec.DefaultReference
		}
	}

	return
}
