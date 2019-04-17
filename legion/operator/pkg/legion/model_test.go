package legion

import (
	"archive/zip"
	"io/ioutil"
	"os"
	"testing"
)

func createZipFile(content string, t *testing.T) {
	tmpFile, err := ioutil.TempFile(os.TempDir(), "prefix-")
	if err != nil {
		t.Error(err)
	}
	defer tmpFile.Close()

	zipWriter := zip.NewWriter(tmpFile)
	defer zipWriter.Close()

}

func TestExtractFromModelFile(t *testing.T) {
	// createZipFile("Sdsd", t)

}
