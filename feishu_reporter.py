"""
数字公司插件 - 飞书集成
实时汇报到飞书
"""

import requests
import json
from company import get_company


class FeishuReporter:
    """飞书汇报器"""
    
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
    
    def send_dashboard(self):
        """发送驾驶舱数据到飞书"""
        if not self.enabled:
            return False
        
        company = get_company()
        data = company.get_dashboard()
        
        # 格式化消息
        message = self._format_dashboard(data)
        
        return self._send_message(message)
    
    def _format_dashboard(self, data):
        """格式化驾驶舱消息"""
        # 简化版消息卡片
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🏢 {data['company_name']} - 董事长驾驶舱"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**👥 员工**: {data['employees']}人 | **工作中**: {data['employees_by_status']['working']}人\n"
                        }
                    },
                    {
                        "tag": "div", 
                        "text": {
                            "tag": "lark_md",
                            "content": f"**📊 项目**: {data['projects']['total']}个 | **进行中**: {data['projects']['running']}个\n"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md", 
                            "content": f"**✅ 任务**: {data['tasks']['total']}个 | **待处理**: {data['tasks']['pending']}个\n"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**💰 资金**: ¥{data['financial']['budget']} | **剩余**: ¥{data['financial']['balance']}"
                        }
                    }
                ]
            }
        }
    
    def send_message(self, text):
        """发送文本消息"""
        if not self.enabled:
            return False
        
        return self._send_message({
            "msg_type": "text",
            "content": {"text": text}
        })
    
    def _send_message(self, payload):
        """发送消息"""
        try:
            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"飞书发送失败: {e}")
            return False


# 全局实例
_feishu_reporter = None


def get_feishu_reporter(webhook_url=None) -> FeishuReporter:
    global _feishu_reporter
    if _feishu_reporter is None:
        _feishu_reporter = FeishuReporter(webhook_url)
    return _feishu_reporter


def set_webhook(url: str):
    """设置飞书Webhook"""
    global _feishu_reporter
    _feishu_reporter = FeishuReporter(url)


def report_to_feishu():
    """汇报到飞书（定时任务用）"""
    reporter = get_feishu_reporter()
    return reporter.send_dashboard()


# 便捷函数
def send_daily_report():
    """发送每日汇报"""
    reporter = get_feishu_reporter()
    
    company = get_company()
    data = company.get_dashboard()
    
    text = f"""📊 金库集团日报

👥 员工: {data['employees']}人 (工作中 {data['employees_by_status']['working']})
📊 项目: {data['projects']['total']}个 (进行中 {data['projects']['running']})
✅ 任务: {data['tasks']['total']}个 (待处理 {data['tasks']['pending']})
💰 资金: ¥{data['financial']['balance']} / ¥{data['financial']['budget']}

— 金多多自动汇报"""
    
    return reporter.send_message(text)
