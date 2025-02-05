run:
	@echo "Starting simulator..."
	python simulator.py &  # Runs in the background
	sleep 2  # Wait for 2 seconds
	@echo "Starting controller after delay..."
	python controller.py  # Runs after sleep