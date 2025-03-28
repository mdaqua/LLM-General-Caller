import logging
from .config import Config
from .cache import MessageCache
from .monitor import PerformanceMonitor
from .balancer import LoadBalancer
from .client import APIClient
from .requestor import RequestCoordinator

def main():
    # 初始化配置
    config = Config.get_instance()
    
    # 初始化组件
    cache = MessageCache(config.api_config['ttl'])
    monitor = PerformanceMonitor()
    balancer = LoadBalancer(config.api_config['providers'])
    client = APIClient(cache, monitor, balancer, config)
    requestor = RequestCoordinator(client, config.api_config['max_workers'])
    
    # 示例调用
    messages = [
        "Hello, how are you?",
        "What's the weather today?",
        "Explain quantum computing"
    ]
    
    results = requestor.batch_request(messages)
    print(f"Final results: {results}")
    print(f"Performance metrics: {monitor.get_metrics()}")

if __name__ == "__main__":
    main()