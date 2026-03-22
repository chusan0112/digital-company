"""测试API接口"""

import unittest
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import handle_request
from company import reset_company


class TestAPI(unittest.TestCase):
    """API接口测试用例"""

    def setUp(self):
        """每个测试前重置公司"""
        reset_company()

    def test_health_check(self):
        """测试健康检查"""
        result = handle_request("/api/health")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["service"], "digital-company")
        self.assertEqual(result["status"], "ok")

    def test_dashboard(self):
        """测试仪表板接口"""
        result = handle_request("/api/dashboard")
        
        self.assertIn("company_name", result)
        self.assertIn("departments", result)
        self.assertIn("employees", result)

    def test_list_employees(self):
        """测试列出员工"""
        result = handle_request("/api/employees")
        
        self.assertIsInstance(result, list)

    def test_list_departments(self):
        """测试列出部门"""
        result = handle_request("/api/departments")
        
        self.assertIsInstance(result, list)

    def test_list_projects(self):
        """测试列出项目"""
        result = handle_request("/api/projects")
        
        self.assertIsInstance(result, list)

    def test_list_tasks(self):
        """测试列出任务"""
        result = handle_request("/api/tasks")
        
        self.assertIsInstance(result, list)

    def test_create_department(self):
        """测试创建部门"""
        body = json.dumps({
            "name": "测试部门",
            "description": "测试描述"
        })
        
        result = handle_request("/api/department", method="POST", body=body)
        
        self.assertTrue(result["success"])
        self.assertIn("id", result)

    def test_create_employee(self):
        """测试雇佣员工"""
        # 先创建一个部门
        dept_result = handle_request("/api/department", method="POST", 
                                     body=json.dumps({"name": "研发部", "description": "技术研发"}))
        dept_id = dept_result["id"]
        
        # 雇佣员工
        body = json.dumps({
            "name": "张三",
            "role": "工程师",
            "department_id": dept_id,
            "skills": ["Python"],
            "salary": 5000
        })
        
        result = handle_request("/api/employee", method="POST", body=body)
        
        self.assertTrue(result["success"])
        self.assertIn("id", result)

    def test_fire_employee(self):
        """测试解雇员工"""
        # 先创建部门并雇佣员工
        dept_result = handle_request("/api/department", method="POST",
                                     body=json.dumps({"name": "研发部", "description": "技术研发"}))
        dept_id = dept_result["id"]
        
        emp_result = handle_request("/api/employee", method="POST",
                                    body=json.dumps({
                                        "name": "张三",
                                        "role": "工程师",
                                        "department_id": dept_id
                                    }))
        emp_id = emp_result["id"]
        
        # 解雇员工
        body = json.dumps({"id": emp_id})
        result = handle_request("/api/employee", method="DELETE", body=body)
        
        self.assertTrue(result["success"])

    def test_update_employee_status(self):
        """测试更新员工状态"""
        # 先创建部门并雇佣员工
        dept_result = handle_request("/api/department", method="POST",
                                     body=json.dumps({"name": "研发部", "description": "技术研发"}))
        dept_id = dept_result["id"]
        
        emp_result = handle_request("/api/employee", method="POST",
                                    body=json.dumps({
                                        "name": "张三",
                                        "role": "工程师",
                                        "department_id": dept_id
                                    }))
        emp_id = emp_result["id"]
        
        # 更新状态
        body = json.dumps({"id": emp_id, "status": "working"})
        result = handle_request("/api/employee/status", method="POST", body=body)
        
        self.assertTrue(result["success"])

    def test_create_project(self):
        """测试创建项目"""
        body = json.dumps({
            "name": "新项目",
            "description": "项目描述",
            "budget": 10000
        })
        
        result = handle_request("/api/project", method="POST", body=body)
        
        self.assertTrue(result["success"])
        self.assertIn("id", result)

    def test_create_task(self):
        """测试创建任务"""
        body = json.dumps({
            "name": "新任务",
            "description": "任务描述",
            "priority": 2
        })
        
        result = handle_request("/api/task", method="POST", body=body)
        
        self.assertTrue(result["success"])
        self.assertIn("id", result)

    def test_assign_task(self):
        """测试分配任务"""
        # 先创建部门、员工和任务
        dept_result = handle_request("/api/department", method="POST",
                                     body=json.dumps({"name": "研发部", "description": "技术研发"}))
        dept_id = dept_result["id"]
        
        emp_result = handle_request("/api/employee", method="POST",
                                    body=json.dumps({
                                        "name": "张三",
                                        "role": "工程师",
                                        "department_id": dept_id
                                    }))
        emp_id = emp_result["id"]
        
        task_result = handle_request("/api/task", method="POST",
                                     body=json.dumps({
                                         "name": "新任务",
                                         "description": "任务描述"
                                     }))
        task_id = task_result["id"]
        
        # 分配任务
        body = json.dumps({"task_id": task_id, "employee_id": emp_id})
        result = handle_request("/api/task/assign", method="POST", body=body)
        
        self.assertTrue(result["success"])

    def test_complete_task(self):
        """测试完成任务"""
        # 先创建任务
        task_result = handle_request("/api/task", method="POST",
                                     body=json.dumps({
                                         "name": "新任务",
                                         "description": "任务描述"
                                     }))
        task_id = task_result["id"]
        
        # 完成任务
        body = json.dumps({"task_id": task_id})
        result = handle_request("/api/task/complete", method="POST", body=body)
        
        self.assertTrue(result["success"])

    def test_spend(self):
        """测试支出"""
        body = json.dumps({
            "amount": 100,
            "description": "测试支出"
        })
        
        result = handle_request("/api/spend", method="POST", body=body)
        
        self.assertTrue(result["success"])

    def test_spend_insufficient_budget(self):
        """测试预算不足的支出"""
        body = json.dumps({
            "amount": 999999,
            "description": "超额支出"
        })
        
        result = handle_request("/api/spend", method="POST", body=body)
        
        self.assertFalse(result["success"])

    def test_not_found(self):
        """测试不存在的接口"""
        result = handle_request("/api/not/exist")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Not found")

    def test_command_without_command_field(self):
        """测试董事长指令-缺少command字段"""
        body = json.dumps({})
        
        result = handle_request("/api/chairman/command", method="POST", body=body)
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "command_required")

    def test_preview_without_command_field(self):
        """测试预览指令-缺少command字段"""
        body = json.dumps({})
        
        result = handle_request("/api/chairman/command/preview", method="POST", body=body)
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "command_required")


if __name__ == "__main__":
    unittest.main()
