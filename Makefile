VENV=.venv
PYTHON_MODULES=python-musicpd paho-mqtt

NAMESPACE=default


all: install

install:
	virtualenv $(VENV) --python=python3 && . $(VENV)/bin/activate && pip3 install $(PYTHON_MODULES)
	cp mpd-mqtt-ir-bridge.py $(VENV)/bin/

clean:
	rm -rf $(VENV)

run:
	. $(VENV)/bin/activate && ./mpd-mqtt-ir-bridge.py

export IMAGE=mpd-pulseaudio-mqtt-ir
export BUILDTAG:=$(shell date +%Y%m%d.%H%M%S)
export NAME=$(IMAGE)
HELM_OPTS:=--set image.repository=$(DOCKER_REGISTRY)/$(IMAGE) --set image.tag=$(BUILDTAG) --set image.pullPolicy=Always

image:
	docker build --build-arg BUILDTAG=$(BUILDTAG) -t $(IMAGE) .
	docker tag $(IMAGE) $(DOCKER_REGISTRY)/$(IMAGE):$(BUILDTAG)
	docker push $(DOCKER_REGISTRY)/$(IMAGE):$(BUILDTAG)

imagerun:
	docker build -t $(IMAGE) .
	-docker stop $(IMAGE)
	docker run -p 6605:6600 -v $(HOME)/Music/:/var/lib/mpd/music:ro -it --name $(IMAGE) --rm $(IMAGE)

helm-install-dry:
	helm install --dry-run --debug $(HELM_OPTS) --namespace=$(NAMESPACE) $(NAME) ./helm-chart

helm-install: image
	helm lint ./helm-chart
	helm upgrade --install $(HELM_OPTS) --namespace=$(NAMESPACE) $(NAME) ./helm-chart

helm-uninstall:
	-helm uninstall --namespace=$(NAMESPACE) $(NAME)

.PHONY: all install clean run
