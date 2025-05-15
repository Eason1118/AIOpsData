
init:
	pip3 install -U ops_sdk -i https://pypi.huanle.com/simple

get_config:
	python get_config.py

run_processor:
	python projects/$(codo_config_path)/processor.py

run_ai:
	python main.py --prompt projects/$(codo_config_path)/prompt.yaml
