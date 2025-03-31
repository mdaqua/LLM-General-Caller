from dataclasses import dataclass
from collections import defaultdict

@dataclass
class PerformanceMetrics:
    total_requests: int = 0
    success_requests: int = 0
    error_requests: int = 0
    total_response_time: float = 0.0

    @property
    def avg_response_time(self):
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests

class PerformanceMonitor:
    def __init__(self):
        self.global_metrics = PerformanceMetrics()
        self.provider_metrics = defaultdict(PerformanceMetrics)
    
    def record_request(self, provider, success, response_time):
        self.global_metrics.total_requests += 1
        if success:
            self.global_metrics.success_requests += 1
        else:
            self.global_metrics.error_requests += 1
        self.global_metrics.total_response_time += response_time

        provider_metrics = self.provider_metrics[provider]
        provider_metrics.total_requests += 1
        if success:
            provider_metrics.success_requests += 1
        else:
            provider_metrics.error_requests += 1
        provider_metrics.total_response_time += response_time
    
    def get_metrics(self, provider=None):
        if provider:
            return self.provider_metrics.get(provider, PerformanceMetrics())
        return self.global_metrics