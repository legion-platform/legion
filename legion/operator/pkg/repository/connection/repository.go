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

package connection

import (
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
)

const (
	TagKey = "name"
)

type Repository interface {
	GetConnection(id string) (*connection.Connection, error)
	GetDecryptedConnection(id string, token string) (*connection.Connection, error)
	GetConnectionList(options ...ListOption) ([]connection.Connection, error)
	DeleteConnection(id string) error
	UpdateConnection(connection *connection.Connection) error
	CreateConnection(connection *connection.Connection) error
}

type Filter struct {
	Type []string `name:"type"`
}

type ListOptions struct {
	Filter *Filter
	Page   *int
	Size   *int
}

type ListOption func(*ListOptions)

func ListFilter(filter *Filter) ListOption {
	return func(args *ListOptions) {
		args.Filter = filter
	}
}

func Page(page int) ListOption {
	return func(args *ListOptions) {
		args.Page = &page
	}
}

func Size(size int) ListOption {
	return func(args *ListOptions) {
		args.Size = &size
	}
}
