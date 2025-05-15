import logging
import yaml
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re
import json
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class DomainProcessor:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.api_config = self.config.get('api', {})
        self.processed_data = set()  # 用于去重

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            raise

    def fetch_data(self) -> List[Dict]:
        """从API获取数据"""
        try:
            headers = {
                'Cookie': self.api_config.get('cookie', ''),
                'Content-Type': self.api_config.get('headers', {}).get('Content-Type', 'application/json')
            }
            
            payload = self.get_payload()
            
            response = requests.post(
                self.api_config.get('url', ''),
                headers=headers,
                data=json.dumps(payload)
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') != 0:
                raise ValueError(f"API返回错误: {data}")
            return data.get('data', {}).get('data', [])
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
            raise

    def clean_data(self, data: List[Dict]) -> List[Dict]:
        """清洗数据"""
        cleaned_data = []
        # 获取需要排除的字段配置
        exclude_fields = self.config.get('processor', {}).get('exclude_fields', [])
        logger.info(f"配置的排除字段: {exclude_fields}")

        for item in data:
            # 1. 排除指定字段
            cleaned_item = {k: v for k, v in item.items() if k not in exclude_fields}
            cleaned_data.append(cleaned_item)

        logger.info(f"数据清洗完成，原始数据量: {len(data)}, 清洗后数据量: {len(cleaned_data)}")
        return cleaned_data

    def compress_logs(self, logs):

        task_counter = Counter()
        from_task_counter = defaultdict(lambda: Counter())
        ip_prefix_counter = Counter()
        user_counter = Counter()

        for log in logs:
            task = log['task']
            source = log['from']
            user = log['username']
            ip = log['ip_address']

            # 计数
            task_counter[task] += 1
            from_task_counter[source][task] += 1

            # 用户分类
            user_counter[user] += 1

            # IP 聚合
            if ip:
                ip_prefix_counter[ip] += 1

        return {
            "search": self.api_config.get('payload', {}).get("search"),
            "total_events": len(logs),
            "task_counts": task_counter,
            "by_from": from_task_counter,
            "user_counts": user_counter.most_common(10),
            "ip_prefixes": ip_prefix_counter.most_common(10)
        }
    def deduplicate_data(self, data: List[Dict]) -> List[Dict]:
        """去重数据
        根据配置的字段进行去重处理
        """
        
        try:
            deduplicated_data = []
            dedup_config = self.config.get('processor', {})
            key_fields = dedup_config.get('duplicate_fields', [])
            
            # 获取需要排除的字段
            exclude_fields = self.config.get('processor', {}).get('exclude_fields', [])
            
            # 确保key_fields不包含被排除的字段
            key_fields = [field for field in key_fields if field not in exclude_fields]
            
            if not key_fields:
                logger.warning("没有有效的去重字段，将使用所有非排除字段进行去重")
                key_fields = [field for field in data[0].keys() if field not in exclude_fields] if data else []
            
            logger.info(f"使用以下字段进行去重: {key_fields}")
            
            # 用于存储已处理的键
            processed_keys = set()
            
            for item in data:
                try:
                    # 构建去重键
                    dedup_key_parts = []
                    for field in key_fields:
                        value = item.get(field, '')
                        dedup_key_parts.append(str(value))
                    
                    dedup_key = tuple(dedup_key_parts)
                    
                    # 检查是否已存在
                    if dedup_key not in processed_keys:
                        processed_keys.add(dedup_key)
                        deduplicated_data.append(item)
                        logger.debug(f"添加新记录: {dedup_key}")
                
                except Exception as e:
                    logger.error(f"处理记录时发生错误: {str(e)}, 记录: {item}")
                    continue
            
            logger.info(f"去重完成，原始数据量: {len(data)}, 去重后数据量: {len(deduplicated_data)}")
            return deduplicated_data
            
        except Exception as e:
            logger.error(f"去重处理失败: {str(e)}")
            raise

    def save(self, data: Dict) -> None:
        """保存处理后的结果"""
        try:
            result_text = f"""
源数据:
- 查询条件: {self.api_config.get('payload', {}).get('search')}
- 总事件数: {data['total_events']}
- 任务分布: {dict(data['task_counts'])}
- 用户统计: {data['user_counts']}
- 前10个IP前缀: {data['ip_prefixes']}"""
            output_path = self.config['processor']['output_file']
            if not output_path:
                logger.warning("输出功能未启用")
                return

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(result_text))
            logger.info(f"数据已保存至: {output_path}")

        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
            raise
        return result_text

    def process(self) -> Dict:
        """处理数据的主函数"""
        try:
            # 1. 获取数据
            raw_data = self.fetch_data()
            logger.info(f"获取到 {len(raw_data)} 条原始数据")
            
            # 2. 清洗数据
            cleaned_data = self.clean_data(raw_data)
            
            # 3. 压缩和统计
            compressed_data = self.compress_logs(cleaned_data)
            
            # 4. 保存结果            
            return self.save(compressed_data)
        except Exception as e:
            logger.error(f"数据处理失败: {str(e)}")
            raise

    def get_payload(self) -> Dict:
        # 获取当前时间
        current_time = datetime.now()

        # 获取24小时前的时间
        start_time = current_time - timedelta(hours=24)
        
        # 格式化时间字符串
        search = {
                "event_time_start": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event_time_end": current_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        payload_config = self.api_config.get('payload', {})
        payload_config["search"].update(search)
        return payload_config


def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 初始化处理器
        processor = DomainProcessor('projects/soc/domain/config.yaml')
        
        # 处理数据
        results = processor.process()
        
        return results
            
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        raise

if __name__ == '__main__':

    main()

