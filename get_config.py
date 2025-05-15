#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/3/4 14:46
# @Author  : harilou
# @Describe: 获取配置中心的参数模板
import os
import logging
from ops_sdk import ConfigCenterHandler, get_env_file_connext

log_format = '%(asctime)s|%(levelname)s|%(message)s'
logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)



if __name__ == '__main__':
    conf_tree = os.getenv("codo_config_path")       # 配置中心参数模板的路径             
    prompt = os.getenv("codo_prompt")                
    CODO_API_KEY = get_env_file_connext(env_path=os.getenv("CODO_CMDB_API_KEY")) # CMDB KEY

    assert conf_tree, f"错误参数 codoconfig_path:{conf_tree}"
    assert prompt, f"错误参数 prompt:{prompt}"
    assert CODO_API_KEY, f"错误参数CODO_API_KEY:{CODO_API_KEY}"
    project = conf_tree.split("/")[0]
    app = conf_tree.split("/")[1]

    config_path_list = [
        {
            "data": {
                "project_code": "AI_data_analysis",
                "env_name": "global",
                "service": "default",
                "filename": "config.yaml",
            },
            "filename": "config.yaml"
        },
        {
            "data": {
                "project_code": "AI_data_analysis",
                "env_name": project,
                "service": app,
                "filename": "config.yaml",
            },
            "filename": f"projects/{project}/{app}/config.yaml"
        }
    ]

    for item in config_path_list:
        conf_tree_data = item["data"]
        filename = item["filename"]

        conf_tree_data.update({"auth_key": CODO_API_KEY})

        conf = ConfigCenterHandler(**conf_tree_data)
        conf_tf_data = conf.get_publish_config()

        with open(filename, "w") as f:
            f.write(conf_tf_data)

    prompt_file = f"projects/{project}/{app}/prompt.yaml"
    prompt_tmp = """
template: |
  %s
  {{logs}}
""" % prompt
    with open(prompt_file, "w") as f:
        f.write(prompt_tmp)
