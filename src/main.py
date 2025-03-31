from .config import Config
from .cache import MessageCache
from .monitor import PerformanceMonitor
from .balancer import LoadBalancer
from .client import APIClient
from .requestor import RequestCoordinator

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
        "编号：5732828124939155883  四川省成都市青羊府南街道  成都市青羊区政府府南街道办事处人民调解委员会  戴娅  2021/8/4  2 小 人身损害  本级摸排  双方因梁语涵进出小区门口引发纠纷，胡同根推搡致梁语涵摔倒全身多处软组织挫伤，经调解双方同意胡同根一次性赔偿梁语涵1600元，双方后期和谐共处    2021/8/4 0:00 成都市青羊区政府府南街道办事处人民调解委员会  戴娅      2021/8/4 0:00 2021/8/4 0:00 成功  梁语涵 胡同根   "
    ]
    
    results = requestor.batch_request(messages)
    print(f"Final results: {results}")
    print(f"Performance metrics: {monitor.get_metrics()}")

if __name__ == "__main__":
    main()