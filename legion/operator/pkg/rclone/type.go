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
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	legionv1alpha1 "github.com/legion-platform/legion/legion/operator/pkg/apis/legion/v1alpha1"
	_ "github.com/ncw/rclone/backend/local"
	"github.com/ncw/rclone/fs"
	"github.com/ncw/rclone/fs/operations"
	"github.com/pkg/errors"
	uuid "github.com/satori/go.uuid"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("rclone")

type ObjectStorage struct {
	name       string
	localFs    fs.Fs
	remoteFs   fs.Fs
	RemotePath string
}

type FileDescription struct {
	FsName string
	Path   string
}

func NewObjectStorage(conn *legionv1alpha1.ConnectionSpec) (obj *ObjectStorage, err error) {
	var config *FileDescription
	name := uuid.NewV4()

	switch conn.Type {
	case connection.S3Type:
		config, err = createS3config(name.String(), conn)
	case connection.GcsType:
		config, err = createGcsConfig(name.String(), conn)
	default:
		return nil, errors.New(fmt.Sprintf("Unxpected connection type: %s", conn.Type))
	}

	log.Info("Extract FileDescription", "file description", config)

	if err != nil {
		return nil, err
	}

	remoteFs, err := fs.NewFs(config.FsName)
	if err != nil {
		return nil, err
	}

	localFs, err := fs.NewFs("")
	if err != nil {
		return nil, err
	}

	if config.Path[0] == '/' {
		config.Path = config.Path[1:]
	}

	return &ObjectStorage{localFs: localFs, remoteFs: remoteFs, RemotePath: config.Path}, nil
}

func (os *ObjectStorage) Download(localPath, remotePath string) error {
	return operations.CopyFile(os.localFs, os.remoteFs, localPath, remotePath)
}

func (os *ObjectStorage) Upload(localPath string) error {
	return operations.CopyFile(os.remoteFs, os.localFs, fmt.Sprintf("%s/%s", os.RemotePath, localPath), localPath)
}
