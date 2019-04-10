package legion

import "fmt"

const (
	podNameTemplate = "%s-training-pod"
)

func GenerateVcsSecretName(vcsName string) string {
	return fmt.Sprintf("%s-vcs", vcsName)
}

func GenerateBuildModelName(mtCRName string) string {
	return fmt.Sprintf(podNameTemplate, mtCRName)
}
