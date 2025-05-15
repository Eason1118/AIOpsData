import requests
from email.mime.text import MIMEText
import yaml
import json
from datetime import datetime
import logging
import argparse
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from feishu_api import FSMsgHandler
import os

# 配置日志
def setup_logging(config: Dict[str, Any]) -> None:
    logging.basicConfig(
        level=config['logging']['level'],
        format=config['logging']['format']
    )
    return logging.getLogger(__name__)

# 解析命令行参数
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='安全告警分析系统')
    parser.add_argument('--config', type=str, default='config.yaml',
                      help='配置文件路径 (默认: config.yaml)')
    parser.add_argument('--prompt', type=str,
                      help='Prompt模板文件路径 (可选，默认使用配置文件中的路径)')
    parser.add_argument('--log', type=str,
                      help='日志文件路径 (可选，默认使用配置文件中的路径)')
    parser.add_argument('--output', type=str,
                      help='输出文件路径 (可选，默认使用配置文件中的路径)')
    return parser.parse_args()

# 加载配置
def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    try:
        with open(config_path, "r", encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 确保必要的配置项存在
        required_keys = ['files', 'api', 'logging', 'notification']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置文件缺少必要的配置项: {key}")
        
        return config
    except Exception as e:
        raise Exception(f"加载配置文件失败: {str(e)}")

# 1. 读取日志
def load_logs(log_path: str) -> List[str]:
    try:
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"日志文件不存在: {log_path}")
            
        with open(log_path, "r", encoding="utf-8") as f:
            logs = f.readlines()
        return logs
    except Exception as e:
        raise Exception(f"读取日志文件失败: {str(e)}")

# 2. 预处理日志
def preprocess_logs(logs: List[str]) -> List[str]:
    try:
        # 统计每条日志出现的次数
        # log_count = {}
        # for line in logs:
        #     line = line.strip()
        #     if line:
        #         log_count[line] = log_count.get(line, 0) + 1
        
        # # 生成带计数的日志列表
        # cleaned = [f"{count} {log}" for log, count in log_count.items()]
        return logs
    except Exception as e:
        raise Exception(f"预处理日志失败: {str(e)}")

# 3. 读取prompt模板
def load_prompt_template(prompt_path: str) -> str:
    try:
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt模板文件不存在: {prompt_path}")
            
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_config = yaml.safe_load(f)
            
        if 'template' not in prompt_config:
            raise ValueError("Prompt模板文件缺少template字段")
            
        return prompt_config["template"]
    except Exception as e:
        raise Exception(f"读取prompt模板失败: {str(e)}")

# 4. 构建prompt
def build_prompt(template: str, logs: List[str]) -> str:
    try:
        logs_text = "\n".join(logs[:100])  # 限制日志数量，避免超出token限制
        prompt = template.replace("{{logs}}", logs_text)
        return prompt
    except Exception as e:
        raise Exception(f"构建prompt失败: {str(e)}")

def save_to_file(file, text: str, is_question: bool = False) -> None:
    try:
        prefix = "\n【问题】\n" if is_question else "\n【回答】\n"
        file.write(prefix + text + "\n")
    except Exception as e:
        raise Exception(f"保存到文件失败: {str(e)}")

# 5. 调用AI模型
def call_deepseekai_api(prompt: str, config: Dict[str, Any], logger: logging.Logger) -> str:
    url = config['api']['deepseek']['url']
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api']['deepseek']['api_key']}"
    }

    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(config['files']['conversation'])
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(config['files']['conversation'], "a", encoding="utf-8") as file:
            save_to_file(file, prompt, is_question=True)

            data = {
                "model": config['api']['deepseek']['model'],
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "max_tokens": config['api']['deepseek']['max_tokens'],
                "temperature": config['api']['deepseek']['temperature'],
                "top_p": config['api']['deepseek']['top_p'],
                "top_k": config['api']['deepseek']['top_k'],
                "frequency_penalty": config['api']['deepseek']['frequency_penalty'],
                "n": 1,
                "response_format": {"type": "text"}
            }
            logger.info(f"data: {json.dumps(data)}")
            response = requests.post(url, json=data, headers=headers, stream=True)
            logger.info(response.text)
            response.raise_for_status()

            logger.info("开始接收AI响应")
            print("\n【回答】\n")
            file.write("\n【回答】\n")

            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: ') and line != 'data: [DONE]':
                        try:
                            content = json.loads(line[6:])
                            if content['choices'][0]['delta'].get('content'):
                                chunk = content['choices'][0]['delta']['content']
                                print(chunk, end='', flush=True)
                                file.write(chunk)
                                full_response += chunk
                        except json.JSONDecodeError:
                            continue

            print("\n\n------ 结束 ------")
            file.write("\n\n------ 结束 ------\n")
            return full_response

    except requests.RequestException as e:
        error_msg = f"请求错误: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

# 6. 生成报告
def generate_report(model_result: str) -> str:
    try:
        report = f"# 安全告警自动分析报告\n\n生成时间: {datetime.now()}\n\n## 分析结果:\n{model_result}"
        return report
    except Exception as e:
        raise Exception(f"生成报告失败: {str(e)}")

# 7. 发送通知
def send_fs_notice(context: str, config: Dict[str, Any], logger: logging.Logger) -> None:
    try:
        from feishu_api import FSMsgHandler
        
        # 初始化飞书消息处理器
        fs_handler = FSMsgHandler(
            app_id=config['notification']['feishu']['app_id'],
            app_secret=config['notification']['feishu']['app_secret'],
            default_chat_id=config['notification']['feishu']['chat_id'],
            user_emails_map=config['notification']['feishu'].get('user_emails_map', {})
        )
        
        # 发送告警消息
        msg_id = fs_handler.alert(
            msg=context,
            chat_id=config['notification']['feishu']['chat_id']
        )
        
        logger.info(f"飞书通知发送成功，消息ID: {msg_id}")
        
    except Exception as e:
        logger.error(f"发送通知失败: {str(e)}")
        raise

# 主流程
def main():
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 加载配置
        config = load_config(args.config)
        logger = setup_logging(config)
        
        # 更新文件路径（如果通过命令行参数指定）
        if args.prompt:
            config['files']['prompt_template'] = args.prompt
        if args.log:
            config['files']['log_path'] = args.log
        if args.output:
            config['files']['conversation'] = args.output
        
        logger.info("开始处理数据")
        
        # 读取和预处理日志
        logs = load_logs(config['files']['log_path'])
        cleaned_logs = preprocess_logs(logs)
        
        # 构建prompt
        prompt_template = load_prompt_template(config['files']['prompt_template'])
        prompt = build_prompt(prompt_template, cleaned_logs)
        
        # 调用AI模型
        model_result = call_deepseekai_api(prompt, config, logger)
        
        # 生成报告
        report = generate_report(model_result)
        
        # 发送通知
        send_fs_notice(report, config, logger)
        
        logger.info("安全告警分析完成")
        
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()
