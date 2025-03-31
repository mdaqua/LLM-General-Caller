from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    total_requests: int = 0
    success_requests: int = 0
    error_requests: int = 0
    total_response_time: float = 0.0

class PerformanceMonitor:
    def __init__(self):
        self.metrics = PerformanceMetrics()
    
    def record_request(self, success, response_time):
        self.metrics.total_requests += 1
        if success:
            self.metrics.success_requests += 1
        else:
            self.metrics.error_requests += 1
        self.metrics.total_response_time += response_time
    
    def get_metrics(self):
        return self.metrics