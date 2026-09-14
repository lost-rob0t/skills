opencode_capability('1.18.29', run_option(variant)).
opencode_capability('1.18.29', run_format(default)).
opencode_capability('1.18.29', run_format(json)).
logical_model(astra_medium, 'openai/gpt-6-astra', medium).
worker_package(opencode_worker, 'skills/opencode-worker').
worker_verification(opencode_worker, 'python3 -m unittest tests/test_opencode_worker.py -v').
