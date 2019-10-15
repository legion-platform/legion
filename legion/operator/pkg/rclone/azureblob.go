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

package rclone

import (
	"fmt"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	_ "github.com/ncw/rclone/backend/azureblob" //nolint
	"github.com/ncw/rclone/fs"
	"github.com/ncw/rclone/fs/config"
	"net/url"
)

func createAzureBlobConfig(configName string, conn *v1alpha1.ConnectionSpec) (*FileDescription, error) {
	_, err := fs.Find("azureblob")
	if err != nil {
		log.Error(err, "")
		return nil, err
	}

	if err := config.CreateRemote(configName, "azureblob", map[string]interface{}{
		"sas_url": conn.KeySecret,
	}); err != nil {
		return nil, err
	}

	parsedURI, err := url.Parse(conn.URI)
	if err != nil {
		log.Error(err, "Parsing data binding URI", "connection uri", conn.URI)

		return nil, err
	}

	return &FileDescription{
		FsName: fmt.Sprintf("%s:%s", configName, parsedURI.Host),
		Path:   parsedURI.Path,
	}, nil
}