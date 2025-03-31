from .config import Config
from .cache import MessageCache
from .monitor import PerformanceMonitor
from .balancer import LoadBalancer
from .client import APIClient
from .requestor import RequestCoordinator
import json
import logging
import pandas as pd

def setup_logging():
    config = Config.get_instance()
    logging.config.dictConfig(config.logging_config)

def analyze_case_example():
    config = Config.get_instance()
    # 初始化组件
    cache = MessageCache(config.api_config['ttl'])
    monitor = PerformanceMonitor()
    balancer = LoadBalancer(config.api_config['providers'])
    client = APIClient(cache, monitor, balancer, config)
    requestor = RequestCoordinator(client, config.api_config['max_workers'])  

    case_descriptions = [
        ""
    ]
    
    results = requestor.batch_process_cases(case_descriptions)

    # 输出结果统计
    success = sum(1 for r in results if not r.get('error'))
    print(f"成功处理 {success}/{len(case_descriptions)} 个案件")
    print(f"性能指标: {monitor.get_metrics()}")

def construct_msg_description(file_path, start_row=2, end_row=None):
    """
    基于`Excel表格`构建`获取案件描述`的请求消息
    """
    try:
        # 读取整个表格
        df = pd.read_excel(file_path, header=0, engine='openpyxl')

        # 将空值替换为 None
        df = df.fillna(value="None")
        
        # 处理行号范围
        start_idx = max(start_row - 2, 0)  # 数据行索引从0开始
        end_idx = end_row - 2 if end_row else len(df)-1
        
        # 有效性检查
        if start_idx > end_idx or end_idx >= len(df):
            raise ValueError("无效的行号范围")
            
        # 切片获取数据
        selected = df.iloc[start_idx:end_idx+1]
        
        # 转换为消息格式
        messages = []
        for _, row in selected.iterrows():
            # 生成结构化内容
            content = "\n".join([f"{col}: {row[col]}" for col in df.columns])
            messages.append(content)
            
        return messages

    except Exception as e:
        print(f"读取失败: {str(e)}")
        return []

def construct_msg_case_info(results):
    """
    基于`案件描述`构建`获取案件基础信息`的请求消息
    """
    msg = []
    for res in results:
        msg.append(res["content"])
    return msg

def construct_msg_relationship(results):
    """
    基于`现有案件`和`新增案件描述`构建`获取案件关系`的请求消息
    """
    msg = []
    for res in results:
        # TODO: 引入图数据库
        msg.append(res["content"])
    return msg

def construct_msg_law(results):
    """
    基于`案件描述`构建`获取案件法律层要素`的请求消息
    """
    msg = []
    return msg

def main():
    # 初始化配置
    setup_logging()
    config = Config.get_instance()
    
    # 初始化组件
    cache = MessageCache(ttl=config.api_config['ttl'])
    monitor = PerformanceMonitor()
    balancer = LoadBalancer(config.api_config['providers'])
    client = APIClient(cache, monitor, balancer, config)
    requestor = RequestCoordinator(client, config.api_config['max_workers'])

    excel_path = "C:\\Users\\mdaqua\\Desktop\\Workbench\\Dazhou\\LLM-General-Caller\\test\\base.xlsx"
    start_row = 801  # 开始读取行号
    end_row = 801  # 结束读取行号，None表示读取到文件末尾

    messages_description = construct_msg_description(excel_path, start_row, end_row)
    results_description = requestor.batch_request(messages_description, provider="dify", key_index=0)
    
    print(f"\nResults: {len(results_description)} responses")
    print(f"Metrics: {monitor.get_metrics().__dict__}")
    print(f"======= ====== =======")
    print(f"{results_description}\n")

if __name__ == "__main__":
    main()