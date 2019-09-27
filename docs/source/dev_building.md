# How to build docker images
## Using Makefile
To build Legion images you may use Makefile from the root repository's folder.

* To build all images call `make build-all-docker-images`
* To build some images call `make build-docker-edi` (`build-docker-<name of ./containers folder>`)

## Manually
If you want to build these images without Make, you have to run `docker build` command from the root repository's context (e.g. `docker build -t legionplatform/k8s-edi:latest -f containers/edi/Dockerfile .`)

## On CI/CD server
Legion provides ready-to-use Jenkins pipeline file `build-legion.Jenkinsfile` in [scripts folder](https://github.com/legion-platform/legion/blob/develop/scripts/build-legion.Jenkinsfile) of main repository.
