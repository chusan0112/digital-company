"""测试审计日志模块"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import audit_log


class TestAuditLog(unittest.TestCase):
    """审计日志测试用例"""

    def setUp(self):
        """每个测试前清空审计事件"""
        audit_log.clear_events()

    def test_log_event_basic(self):
        """测试基本的事件记录"""
        audit_log.log_event("test_action", "test_actor", {"key": "value"})
        events = audit_log.list_events(limit=10)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["action"], "test_action")
        self.assertEqual(events[0]["actor"], "test_actor")
        self.assertEqual(events[0]["payload"], {"key": "value"})
        self.assertIn("timestamp", events[0])

    def test_log_event_without_payload(self):
        """测试无payload的事件记录"""
        audit_log.log_event("login", "admin")
        events = audit_log.list_events()
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["payload"], {})

    def test_list_events_limit(self):
        """测试事件列表限制"""
        # 记录3条事件
        for i in range(3):
            audit_log.log_event(f"action_{i}", f"actor_{i}")
        
        events = audit_log.list_events(limit=2)
        self.assertEqual(len(events), 2)
        # 应该返回最新的2条
        self.assertEqual(events[0]["action"], "action_1")
        self.assertEqual(events[1]["action"], "action_2")

    def test_list_events_zero_limit(self):
        """测试limit为0的情况"""
        audit_log.log_event("action", "actor")
        events = audit_log.list_events(limit=0)
        
        self.assertEqual(len(events), 0)

    def test_list_events_negative_limit(self):
        """测试负数limit"""
        audit_log.log_event("action", "actor")
        events = audit_log.list_events(limit=-1)
        
        self.assertEqual(len(events), 0)

    def test_get_total_count(self):
        """测试获取事件总数"""
        audit_log.clear_events()
        self.assertEqual(audit_log.get_total_count(), 0)
        
        audit_log.log_event("action1", "actor1")
        self.assertEqual(audit_log.get_total_count(), 1)
        
        audit_log.log_event("action2", "actor2")
        self.assertEqual(audit_log.get_total_count(), 2)

    def test_clear_events(self):
        """测试清空事件"""
        audit_log.log_event("action", "actor")
        self.assertEqual(audit_log.get_total_count(), 1)
        
        audit_log.clear_events()
        self.assertEqual(audit_log.get_total_count(), 0)

    def test_auto_cleanup(self):
        """测试自动清理超过最大容量的事件"""
        # audit_log.MAX_AUDIT_EVENTS = 1000
        original_max = audit_log.MAX_AUDIT_EVENTS
        audit_log.MAX_AUDIT_EVENTS = 5
        
        # 记录超过最大容量的事件
        for i in range(7):
            audit_log.log_event(f"action_{i}", f"actor_{i}")
        
        # 应该只保留最近的5条
        self.assertEqual(audit_log.get_total_count(), 5)
        
        # 验证最早的事件被清理
        events = audit_log.list_events(limit=10)
        self.assertEqual(events[0]["action"], "action_2")
        
        # 恢复原始值
        audit_log.MAX_AUDIT_EVENTS = original_max


if __name__ == "__main__":
    unittest.main()
