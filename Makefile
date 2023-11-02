VENV=.venv
PYTHON_MODULES=python-musicpd git+https://github.com/wuub/rxv.git git+https://github.com/matgoebl/nano-dlna.git@dev

NAMESPACE=default


all: install

install:
	virtualenv $(VENV) --python=python3 && . $(VENV)/bin/activate && pip3 install $(PYTHON_MODULES)
	cp mpd-dlna-yamaha-avr.py $(VENV)/bin/

clean:
	rm -rf $(VENV)

run:
	. $(VENV)/bin/activate && ./mpd-dlna-yamaha-avr.py

export IMAGE=mpd-dlna-yamaha-avr
export BUILDTAG:=$(shell date +%Y%m%d.%H%M%S)
export NAME=$(IMAGE)
HELM_OPTS:=--set image.repository=$(DOCKER_REGISTRY)/$(IMAGE) --set image.tag=$(BUILDTAG) --set image.pullPolicy=Always

image:
	docker build --build-arg BUILDTAG=$(BUILDTAG) -t $(IMAGE) .
	docker tag $(IMAGE) $(DOCKER_REGISTRY)/$(IMAGE):$(BUILDTAG)
	docker push $(DOCKER_REGISTRY)/$(IMAGE):$(BUILDTAG)

imagerun:
	docker build -t $(IMAGE) .
	docker run -p 6604:6600 -p 6603:6601 -v $(HOME)/Music/:/var/lib/mpd/music:ro -it $(IMAGE)

helm-install-dry:
	helm install --dry-run --debug $(HELM_OPTS) --namespace=$(NAMESPACE) $(NAME) ./helm-chart

helm-install: image
	helm lint ./helm-chart
	helm upgrade --install $(HELM_OPTS) --namespace=$(NAMESPACE) $(NAME) ./helm-chart

helm-uninstall:
	-helm uninstall --namespace=$(NAMESPACE) $(NAME)

.PHONY: all install clean run
