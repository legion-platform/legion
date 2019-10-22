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

package utils

import "testing"

func TestExtractHost(t *testing.T) {
	type args struct {
		gitURL string
	}
	tests := []struct {
		name    string
		args    args
		want    string
		wantErr bool
	}{
		{
			name:    "git_legion",
			args:    args{"git@github.com:legion-platform/legion-jenkins.git"},
			want:    "github.com",
			wantErr: false,
		},
		{
			name:    "ssh",
			args:    args{"ssh://user@server.com/project.git"},
			want:    "server.com",
			wantErr: false,
		},
		{
			name:    "git+ssh",
			args:    args{"git+ssh://user@server.com/project.git"},
			want:    "server.com",
			wantErr: false,
		},
	}
	for _, tt := range tests {
		// pin variable
		tt := tt

		t.Run(tt.name, func(t *testing.T) {
			got, err := extractHost(tt.args.gitURL)
			if (err != nil) != tt.wantErr {
				t.Errorf("extractHost() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if got != tt.want {
				t.Errorf("extractHost() = %v, want %v", got, tt.want)
			}
		})
	}
}
