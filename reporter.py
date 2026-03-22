"""
数字公司插件 - 定时汇报
"""

import time
import threading
from company import get_company
from feishu_reporter import send_daily_report, get_feishu_reporter


class PeriodicReporter:
    """定时汇报器"""
    
    def __init__(self, interval_seconds=300):  # 默认5分钟
        self.interval = interval_seconds
        self.running = False
        self.thread = None
    
    def start(self):
        """启动定时汇报"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"定时汇报已启动，每{self.interval}秒汇报一次")
    
    def stop(self):
        """停止定时汇报"""
        self.running = False
        if self.thread:
            print("定时汇报已停止")
    
    def _run(self):
        """运行循环"""
        while self.running:
            try:
                self.report()
            except Exception as e:
                print(f"汇报失败: {e}")
            time.sleep(self.interval)
    
    def report(self):
        """执行汇报"""
        company = get_company()
        data = company.get_dashboard()
        
        # 格式化消息
        text = f"""📊 金库集团实时状态

💰 资金: ¥{data['financial']['balance']} / ¥{data['financial']['budget']}
👥 员工: {data['employees']}人 (工作中 {data['employees_by_status']['working']})
📊 项目: {data['projects']['total']}个 (进行中 {data['projects']['running']})
✅ 任务: {data['tasks']['total']}个 (待处理 {data['tasks']['pending']} / 进行中 {data['tasks']['in_progress']})

— 金多多自动汇报"""
        
        reporter = get_feishu_reporter()
        if reporter.enabled:
            reporter.send_message(text)
            print("已发送飞书汇报")
        else:
            print(f"飞书未配置，仅打印: {text}")
        
        return text


# 全局实例
_reporter = None


def get_reporter(interval=300) -> PeriodicReporter:
    global _reporter
    if _reporter is None:
        _reporter = PeriodicReporter(interval)
    return _reporter


def start_reporting(interval=300):
    """启动定时汇报"""
    get_reporter(interval).start()


def stop_reporting():
    """停止定时汇报"""
    get_reporter().stop()


def send_once():
    """立即汇报一次"""
    return get_reporter().report()
