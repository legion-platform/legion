package v1alpha1

import (
	"context"
	"errors"
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/legion"
	"github.com/spf13/viper"
	"go.uber.org/multierr"
	k8stypes "k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
	"strings"
)

const (
	mrUrlPrefixEmptyErrorMessage = "URL Prefix must not be empty"
	mrEmptyTargetErrorMessage    = "model deployment targets must contain at least one element"
	mrOneTargetErrorMessage      = "it must have 100 weight or nil value if there is only one target"
	mrMissedWeightErrorMessage   = "weights must be present if there are more than one model deployment targets"
	mrTotalWeightErrorMessage    = "total target weight does not equal 100"
	mrUrlPrefixSlashErrorMessage = "the URL prefix must start with slash"
	mrForbiddenPrefix            = "the URL prefix %s is forbidden"
)

var (
	maxWeight         = int32(100)
	forbiddenPrefixes = []string{
		"/model", "/feedback",
	}
)

var logMR = logf.Log.WithName("model_route")

func (mr *ModelRoute) ValidatesAndSetDefaults(k8sClient client.Client) (err error) {
	if len(mr.Spec.UrlPrefix) == 0 {
		err = multierr.Append(err, errors.New(mrUrlPrefixEmptyErrorMessage))
	} else {
		if !strings.HasPrefix(mr.Spec.UrlPrefix, "/") {
			err = multierr.Append(err, errors.New(mrUrlPrefixSlashErrorMessage))
		} else {
			annotationValue, ok := mr.ObjectMeta.Annotations[SkipUrlValidationKey]
			if !ok || annotationValue != SkipUrlValidationValue {
				for _, prefix := range forbiddenPrefixes {
					if strings.HasPrefix(mr.Spec.UrlPrefix, prefix) {
						err = multierr.Append(err, errors.New(fmt.Sprintf(mrForbiddenPrefix, prefix)))
						break
					}
				}
			}
		}
	}

	if mr.Spec.Mirror != nil && len(*mr.Spec.Mirror) != 0 {
		md := &ModelDeployment{}
		if k8sError := k8sClient.Get(context.TODO(), k8stypes.NamespacedName{
			Name:      *mr.Spec.Mirror,
			Namespace: viper.GetString(legion.Namespace),
		}, md); k8sError != nil {
			err = multierr.Append(err, k8sError)
		}
	}

	switch len(mr.Spec.ModelDeploymentTargets) {
	case 0:
		err = multierr.Append(err, errors.New(mrEmptyTargetErrorMessage))
	case 1:
		mdt := mr.Spec.ModelDeploymentTargets[0]

		md := &ModelDeployment{}
		if k8sError := k8sClient.Get(context.TODO(), k8stypes.NamespacedName{
			Name:      mdt.Name,
			Namespace: viper.GetString(legion.Namespace),
		}, md); k8sError != nil {
			err = multierr.Append(err, k8sError)
		}
		if mdt.Weight == nil {
			logMD.Info("Weight parameter is nil. Set the default value",
				"Model Route name", mr.Name, "weight", maxWeight)
			mr.Spec.ModelDeploymentTargets[0].Weight = &maxWeight
		} else {
			if *mdt.Weight != 100 {
				err = multierr.Append(err, errors.New(mrOneTargetErrorMessage))
			}
		}
	default:
		weightSum := int32(0)

		for _, mdt := range mr.Spec.ModelDeploymentTargets {
			md := &ModelDeployment{}
			if k8sError := k8sClient.Get(context.TODO(), k8stypes.NamespacedName{
				Name:      mdt.Name,
				Namespace: viper.GetString(legion.Namespace),
			}, md); k8sError != nil {
				err = multierr.Append(err, k8sError)
			}

			if mdt.Weight == nil {
				err = multierr.Append(err, errors.New(mrMissedWeightErrorMessage))
				continue
			}

			weightSum += *mdt.Weight
		}

		if weightSum != 100 {
			err = multierr.Append(err, errors.New(mrTotalWeightErrorMessage))
		}
	}

	return
}
