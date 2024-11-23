setup:
	brew install poppler
	brew install azure-cli
	pip install google-cloud-sdk
	mkdir tmp

lint:
	black .
	deptry .