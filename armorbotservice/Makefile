version=3.1.0
build:
	docker image build --platform linux/amd64 -t armorbot-service .

push:
	docker tag armorbot-service:latest us.gcr.io/starry-academy-177207/armorblox/armorbot:$(version)
	docker push us.gcr.io/starry-academy-177207/armorblox/armorbot:$(version)