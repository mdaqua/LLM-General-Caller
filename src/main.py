import json
import logging
import pandas as pd
from .config import Config
from .cache import MessageCache, NullCache
from .monitor import PerformanceMonitor
from .balancer import LoadBalancer
from .client import APIClient
from .requestor import RequestCoordinator

def setup_logging():
    config = Config.get_instance()
    logging.config.dictConfig(config.logging_config)

def multiple_json_parse(s):
    decoder = json.JSONDecoder()
    offset = 0
    while offset < len(s):
        while offset < len(s) and s[offset].isspace():
            offset += 1
        if offset >= len(s):
            break
        data, offset = decoder.raw_decode(s, idx=offset)
        result = {
            "case": {
                "id": data["case"]["id"],
                "subject": data["case"]["behavior"]["subject"],
                "location": data["case"]["space_time"]["location"],
                "actions": data["case"]["behavior"]["actions"],
                "occurrence_time": data["case"]["space_time"]["occurrence_time"]
            }
        }
        yield result

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

def construct_msg_law(results):
    """
    基于`案件描述`构建`获取案件法律层要素`的请求消息
    """
    msg = []
    for res in results:
        msg.append(res["content"])
    return msg

def construct_msg_relationship(results, file_path):
    """
    基于`现有案件`和`新增案件描述`构建`获取案件关系`的请求消息
    """
    # 读取现有案件数据
    with open(file_path, 'r', encoding='utf-8') as file:
        data = file.read()
    cases = []
    for obj in multiple_json_parse(data.strip()):
        cases.append(obj["case"])

    # 构建请求消息
    msg = []
    for res in results:
        # TODO: 引入图数据库
        temp = {
            "base": [{f"case_{i+1}": case} for i, case in enumerate(cases)],
            "target": res["content"]
        }
        msg.append(str(temp))
    return msg

def result_handler(case_infos, law_infos, relationship_infos):
    """
    处理请求结果
    """
    # 解析案件基础信息
    cases = []
    for case in case_infos:
        cases.append(json.loads(case["content"].replace("```json\n", "").replace("\n```", "")))
    # 解析案件法律层要素
    for law_info in law_infos:
        law_info = json.loads(law_info["content"].replace("```json\n", "").replace("\n```", ""))
        for case in cases:
            if case["case"]["id"] == law_info["case"]["id"]:
                case["case"]["law"] = law_info["case"]["law"]
    # 解析案件关系
    for relationship_info in relationship_infos:
        relationship_info = json.loads(relationship_info["content"].replace("```json\n", "").replace("\n```", ""))
        for case in cases:
            if case["case"]["id"] == relationship_info["case"]["id"]:
                case["case"]["relationships"] = relationship_info["case"]["relationships"]

    return cases

def main():
    # 初始化配置
    setup_logging()
    config = Config.get_instance()
    config.validate()
    
    # 初始化组件
    if config.api_config["enable_cache"]:
        cache = MessageCache(ttl=config.api_config['ttl'])
    else:
        cache = NullCache()
    monitor = PerformanceMonitor()
    balancer = LoadBalancer(config.api_config['providers'])
    client = APIClient(cache, monitor, balancer, config)
    requestor = RequestCoordinator(client, config.api_config['max_workers'])

    excel_path = "C:\\Users\\mdaqua\\Desktop\\Workbench\\Dazhou\\LLM-General-Caller\\test\\base.xlsx"
    start_row = 801  # 开始读取行号
    end_row = 801  # 结束读取行号，None表示读取到文件末尾

    # 读取Excel表格，构建案件描述信息
    messages_description = construct_msg_description(excel_path, start_row, end_row)
    results_description = requestor.batch_request(messages_description, provider="difya")
    # 获取案件结构化信息
    messages_case_info = construct_msg_case_info(results_description)
    results_case_info = requestor.batch_request(messages_case_info, provider="difyb")
    # 获取案件法律层信息
    messages_law = construct_msg_law(results_description)
    results_law = requestor.batch_request(messages_law, provider="difyc")
    # 获取案件关系信息
    base_file_path = "C:\\Users\\mdaqua\\Desktop\\Workbench\\Dazhou\\LLM-General-Caller\\test\\fake_database.txt"
    messages_relationship = construct_msg_relationship(results_description, base_file_path)
    results_relationship = requestor.batch_request(messages_relationship, provider="difyd")
    
    # 输出结果
    # print(f"\nResults: {len(results_description)} responses")
    # print(f"Metrics: {monitor.get_metrics().__dict__}")
    cases = result_handler(
        case_infos=results_case_info,
        law_infos=results_law,
        relationship_infos=results_relationship
    )
    for case in cases:
        print(json.dumps(case, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    main()