.PHONY: eval train

# Path to Python
PYTHON = python3

# Paths to scripts
MODEL_TRAINING_SCRIPT = model/model_training.py
MODEL_SCRIPT = model/model_training.py
UNITTEST_SCRIPT = run_tests.py

# Paths to data
TEST_DATA = data/complete_test.csv
EVAL_DATA = data/aki.csv

# Commands
eval:
	$(PYTHON) $(MODEL_TRAINING_SCRIPT) --input $(TEST_DATA) --eval $(EVAL_DATA) --no-infer

train:
	$(PYTHON) $(MODEL_SCRIPT)

mlflow:
	$(PYTHON) $(MODEL_TRAINING_SCRIPT) --input $(TEST_DATA) --eval $(EVAL_DATA) --no-infer --mlflow

unittest:
	$(PYTHON) $(UNITTEST_SCRIPT) 

unittest_coverage:
	$(PYTHON) $(UNITTEST_SCRIPT) --coverage

