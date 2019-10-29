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

package errors

type NotFoundError struct{}

func (nfe NotFoundError) Error() string {
	return "entity is not found"
}

func IsNotFoundError(err error) bool {
	_, ok := err.(NotFoundError)
	return ok
}

type SerializationError struct{}

func (se SerializationError) Error() string {
	return "serialization is failed"
}

func IsSerializationError(err error) bool {
	_, ok := err.(SerializationError)
	return ok
}

type AlreadyExistError struct{}

func (aee AlreadyExistError) Error() string {
	return "entity already exists"
}

func IsAlreadyExistError(err error) bool {
	_, ok := err.(AlreadyExistError)
	return ok
}

type ForbiddenError struct{}

func (aee ForbiddenError) Error() string {
	return "access forbidden"
}

func IsForbiddenError(err error) bool {
	_, ok := err.(ForbiddenError)
	return ok
}
