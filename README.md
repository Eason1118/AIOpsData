# AI分析系统

## 项目简介
本项目是一个基于 AI 的告警分析系统，用于自动化分析和处理数据流日志或者告警。系统通过调用 AI 模型对告警日志进行智能分析，生成分析报告，并通过飞书进行通知。

## 功能特点
- 支持多种日志格式的读取和处理
- 灵活的配置文件管理
- 智能的日志分析和处理
- AI 驱动的告警分析
- 自动化的报告生成
- 飞书通知集成
- 详细的日志记录

## 系统架构
```
.
├── config.yaml              # 主配置文件
├── main.py                 # 主程序入口
├── feishu_api.py           # 飞书 API 集成
├── templates/              # 模板目录
│   └── prompt_template.yaml # AI 提示模板
├── logs/                   # 日志目录
└── results/               # 结果输出目录
```

## 快速开始

### 1. 环境要求
- Python 3.8+
- 依赖包：
  - requests
  - pyyaml
  - logging

### 2. 安装
```bash
# 克隆项目
git clone [项目地址]

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置
1. 复制配置文件模板：
```bash
cp config.yaml.example config.yaml
```

2. 修改配置文件 `config.yaml`：
```yaml
# 文件配置
files:
  log_path: "logs/alerts.log"
  prompt_template: "templates/prompt_template.yaml"
  conversation: "results/conversation.txt"

# API 配置
api:
  deepseek:
    url: "https://api.deepseek.com/v1/chat/completions"
    api_key: "your-api-key"
    model: "deepseek-chat"
    max_tokens: 2000
    temperature: 0.7
    top_p: 0.9
    top_k: 40
    frequency_penalty: 0.0

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 通知配置
notification:
  feishu:
    app_id: "your-app-id"
    app_secret: "your-app-secret"
    chat_id: "your-chat-id"
    user_emails_map: {}
```

### 4. 运行
```bash
# 使用默认配置运行
python main.py

# 指定配置文件
python main.py --config custom_config.yaml

# 指定 prompt 模板
python main.py --prompt templates/custom_prompt.yaml

# 指定日志文件
python main.py --log logs/custom.log

# 指定输出文件
python main.py --output results/custom_output.txt
```

## 使用说明

### 1. 日志格式
系统支持多种日志格式，包括但不限于：
- 标准日志格式
- JSON 格式
- 自定义格式

### 2. Prompt 模板
在 `templates/prompt_template.yaml` 中定义 AI 提示模板：
```yaml
template: |
  请分析以下安全告警日志：
  {{logs}}
  
  请提供：
  1. 告警类型分析
  2. 风险等级评估
  3. 处理建议
```

### 3. 输出结果
系统会生成以下输出：
- 分析报告
- 对话记录
- 处理日志

## 开发指南

### 1. 添加新的日志格式支持
1. 在 `main.py` 中修改 `load_logs` 函数
2. 添加相应的日志解析逻辑

### 2. 自定义 AI 分析
1. 修改 `templates/prompt_template.yaml`
2. 调整 AI 参数配置

### 3. 扩展通知方式
1. 在 `feishu_api.py` 中添加新的通知方法
2. 更新配置文件

## 常见问题

### 1. 配置文件错误
- 检查配置文件格式是否正确
- 确保所有必要的配置项都已填写

### 2. API 调用失败
- 验证 API 密钥是否正确
- 检查网络连接
- 查看 API 调用限制

### 3. 日志处理问题
- 确认日志文件路径正确
- 检查日志格式是否符合要求

## 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证
[许可证类型]

## 联系方式
[联系方式]
