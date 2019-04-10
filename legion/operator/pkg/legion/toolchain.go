package legion

import (
	"fmt"
	"github.com/pkg/errors"
	"strings"
)

const (
	PythonToolchainName = "python"
	JupiterToolchainName = "jupyter"
)

func GetToolchainImage(toolchainName string, config OperatorConfig) (image string, err error) {

	switch toolchainName {
	case PythonToolchainName:
		return config.PythonToolchainImage, nil
	case JupiterToolchainName:
		return config.PythonToolchainImage, nil
	}

	return "", errors.New(fmt.Sprintf("Can't find %s toolchain", toolchainName))
}

func GenerateModelCommand(toolchainName string, entrypoint string,
	args []string) (string, error) {
	switch toolchainName {
	case PythonToolchainName:
		var pythonCommand strings.Builder
		pythonCommand.WriteString(fmt.Sprintf("python3 %s", entrypoint))

		for _, arg := range args {
			pythonCommand.WriteString(" " + arg)
		}
		return pythonCommand.String(), nil
	case JupiterToolchainName:
		// TODO: need to think about jupyter parameters
		return fmt.Sprintf("jupyter nbconvert --execute %s", entrypoint), nil
	}

	return "", errors.New(fmt.Sprintf("Can't find %s toolchain", toolchainName))
}
