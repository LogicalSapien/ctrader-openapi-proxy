.PHONY: install run install-service

VENV   := venv
PYTHON := $(VENV)/bin/python

install:
	@echo "Setting up virtual environment..."
	@python3 -m venv $(VENV)
	@$(VENV)/bin/pip install --upgrade pip
	@$(VENV)/bin/pip install -r requirements.txt
	@echo "Done. Copy .env.example to .env and fill in your credentials."

run:
	@echo "Starting cTrader OpenAPI Proxy on http://localhost:9009 ..."
	@$(PYTHON) main.py

install-service:
	@echo "Installing systemd service..."
	@sed \
		-e "s|__USER__|$$(whoami)|g" \
		-e "s|__WORKDIR__|$$(pwd)|g" \
		deploy/ctrader-proxy.service > /tmp/ctrader-proxy.service
	@sudo mv /tmp/ctrader-proxy.service /etc/systemd/system/ctrader-proxy.service
	@sudo systemctl daemon-reload
	@sudo systemctl enable ctrader-proxy
	@echo "Service installed. Run: sudo systemctl start ctrader-proxy"
