.PHONY: eval train

# Path to Python
PYTHON = python3

# Paths to scripts
MODEL_TRAINING_SCRIPT = model/train.py
MODEL_EVAL_SCRIPT = model/eval.py
UNITTEST_SCRIPT = run_tests.py

# Paths to data
TEST_DATA = data/test.csv
TRAIN_DATA = data/training.csv


# Commands
eval:
	$(PYTHON) $(MODEL_EVAL_SCRIPT) --input $(TEST_DATA) 

train:
	$(PYTHON) $(MODEL_TRAINING_SCRIPT) --train  $(TRAIN_DATA)  --no-infer

mlflow:
	$(PYTHON) $(MODEL_EVAL_SCRIPT) --input $(TEST_DATA)  --mlflow

unittest:
	$(PYTHON) $(UNITTEST_SCRIPT) 

unittest_coverage:
	$(PYTHON) $(UNITTEST_SCRIPT) --coverage

