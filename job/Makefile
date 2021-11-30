.PHONY: check-env
check-env:
ifndef DOCKER_IMAGE
	$(error DOCKER_IMAGE is undefined, try export DOCKER_IMAGE=yourdockerhubname/flowlog:1.0)
endif

docker-build: check-env
	docker build . -t $(DOCKER_IMAGE)

docker-run:
	docker run -it $(DOCKER_IMAGE)

docker-push:
	docker push $(DOCKER_IMAGE)
