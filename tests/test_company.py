"""测试公司核心模型"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from company import Company, Department, Employee, Project, Task, reset_company


class TestDepartment(unittest.TestCase):
    """部门测试用例"""

    def test_department_creation(self):
        """测试部门创建"""
        dept = Department(id="dept1", name="研发部", description="技术研发", parent_id="")
        
        self.assertEqual(dept.id, "dept1")
        self.assertEqual(dept.name, "研发部")
        self.assertEqual(dept.description, "技术研发")
        self.assertEqual(dept.parent_id, "")
        self.assertIsNotNone(dept.created_at)

    def test_department_to_dict(self):
        """测试部门转字典"""
        dept = Department(id="dept1", name="研发部", description="技术研发")
        d = dept.to_dict()
        
        self.assertIsInstance(d, dict)
        self.assertEqual(d["id"], "dept1")
        self.assertEqual(d["name"], "研发部")

    def test_department_from_dict(self):
        """测试从字典创建部门"""
        d = {"id": "dept1", "name": "研发部", "description": "技术研发", "parent_id": "", "created_at": "2024-01-01"}
        dept = Department.from_dict(d)
        
        self.assertEqual(dept.id, "dept1")
        self.assertEqual(dept.name, "研发部")


class TestEmployee(unittest.TestCase):
    """员工测试用例"""

    def test_employee_creation(self):
        """测试员工创建"""
        emp = Employee(id="emp1", name="张三", role="工程师", department_id="dept1")
        
        self.assertEqual(emp.id, "emp1")
        self.assertEqual(emp.name, "张三")
        self.assertEqual(emp.role, "工程师")
        self.assertEqual(emp.department_id, "dept1")
        self.assertEqual(emp.status, "idle")
        self.assertEqual(emp.skills, [])
        self.assertIsNotNone(emp.hire_date)

    def test_employee_with_skills(self):
        """测试带技能的员工创建"""
        emp = Employee(id="emp1", name="张三", role="工程师", department_id="dept1", 
                      skills=["Python", "Java"], salary=10000)
        
        self.assertEqual(emp.skills, ["Python", "Java"])
        self.assertEqual(emp.salary, 10000)

    def test_employee_to_dict(self):
        """测试员工转字典"""
        emp = Employee(id="emp1", name="张三", role="工程师", department_id="dept1")
        d = emp.to_dict()
        
        self.assertIsInstance(d, dict)
        self.assertEqual(d["id"], "emp1")
        self.assertEqual(d["name"], "张三")


class TestProject(unittest.TestCase):
    """项目测试用例"""

    def test_project_creation(self):
        """测试项目创建"""
        proj = Project(id="proj1", name="新项目", description="项目描述")
        
        self.assertEqual(proj.id, "proj1")
        self.assertEqual(proj.name, "新项目")
        self.assertEqual(proj.description, "项目描述")
        self.assertEqual(proj.status, "planning")
        self.assertEqual(proj.progress, 0)

    def test_project_with_budget(self):
        """测试带预算的项目"""
        proj = Project(id="proj1", name="新项目", description="项目描述", budget=50000)
        
        self.assertEqual(proj.budget, 50000)


class TestTask(unittest.TestCase):
    """任务测试用例"""

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(id="task1", name="新任务", description="任务描述")
        
        self.assertEqual(task.id, "task1")
        self.assertEqual(task.name, "新任务")
        self.assertEqual(task.status, "pending")
        self.assertEqual(task.priority, 1)

    def test_task_with_assignee(self):
        """测试带负责人的任务"""
        task = Task(id="task1", name="新任务", description="任务描述", 
                   assignee_id="emp1", priority=3)
        
        self.assertEqual(task.assignee_id, "emp1")
        self.assertEqual(task.priority, 3)


class TestCompany(unittest.TestCase):
    """公司测试用例"""

    def setUp(self):
        """每个测试前重置公司"""
        reset_company()

    def test_company_initialization(self):
        """测试公司初始化"""
        company = Company("测试公司")
        
        self.assertIsNotNone(company.id)
        self.assertEqual(company.name, "测试公司")
        self.assertEqual(company.budget, 1000)
        self.assertEqual(company.spent, 0)

    def test_add_department(self):
        """测试添加部门"""
        company = Company("测试公司")
        initial_count = len(company.departments)
        dept = company.add_department("测试部门", "描述")
        
        self.assertIsNotNone(dept.id)
        self.assertEqual(dept.name, "测试部门")
        self.assertEqual(len(company.departments), initial_count + 1)

    def test_get_department(self):
        """测试获取部门"""
        company = Company("测试公司")
        dept = company.add_department("测试部门", "描述")
        
        found = company.get_department(dept.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "测试部门")

    def test_get_department_not_found(self):
        """测试获取不存在的部门"""
        company = Company("测试公司")
        
        found = company.get_department("not_exists")
        self.assertIsNone(found)

    def test_list_departments(self):
        """测试列出部门"""
        company = Company("测试公司")
        company.add_department("部门1", "描述1")
        company.add_department("部门2", "描述2")
        
        depts = company.list_departments()
        self.assertGreaterEqual(len(depts), 2)

    def test_hire_employee(self):
        """测试雇佣员工"""
        company = Company("测试公司")
        dept = company.add_department("研发部", "技术研发")
        initial_count = len(company.employees)
        
        emp = company.hire_employee("张三", "工程师", dept.id, ["Python"], 5000)
        
        self.assertIsNotNone(emp.id)
        self.assertEqual(emp.name, "张三")
        self.assertEqual(len(company.employees), initial_count + 1)

    def test_fire_employee(self):
        """测试解雇员工"""
        company = Company("测试公司")
        dept = company.add_department("研发部", "技术研发")
        emp = company.hire_employee("张三", "工程师", dept.id)
        initial_count = len(company.employees)
        
        result = company.fire_employee(emp.id)
        
        self.assertTrue(result)
        self.assertEqual(len(company.employees), initial_count - 1)

    def test_get_employee(self):
        """测试获取员工"""
        company = Company("测试公司")
        dept = company.add_department("研发部", "技术研发")
        emp = company.hire_employee("张三", "工程师", dept.id)
        
        found = company.get_employee(emp.id)
        
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "张三")

    def test_update_employee_status(self):
        """测试更新员工状态"""
        company = Company("测试公司")
        dept = company.add_department("研发部", "技术研发")
        emp = company.hire_employee("张三", "工程师", dept.id)
        
        company.update_employee_status(emp.id, "working")
        
        updated = company.get_employee(emp.id)
        self.assertEqual(updated.status, "working")

    def test_list_employees_by_department(self):
        """测试按部门列出员工"""
        company = Company("测试公司")
        dept1 = company.add_department("研发部", "技术研发")
        dept2 = company.add_department("市场部", "市场营销")
        
        emp1 = company.hire_employee("张三", "工程师", dept1.id)
        emp2 = company.hire_employee("李四", "销售", dept2.id)
        
        dept1_emps = company.list_employees(department_id=dept1.id)
        
        self.assertEqual(len(dept1_emps), 1)
        self.assertEqual(dept1_emps[0].name, "张三")

    def test_create_project(self):
        """测试创建项目"""
        company = Company("测试公司")
        
        proj = company.create_project("新项目", "项目描述", budget=10000)
        
        self.assertIsNotNone(proj.id)
        self.assertEqual(proj.name, "新项目")
        self.assertEqual(proj.budget, 10000)

    def test_get_project(self):
        """测试获取项目"""
        company = Company("测试公司")
        proj = company.create_project("新项目", "项目描述")
        
        found = company.get_project(proj.id)
        
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "新项目")

    def test_list_projects(self):
        """测试列出项目"""
        company = Company("测试公司")
        company.create_project("项目1", "描述1")
        company.create_project("项目2", "描述2")
        
        projects = company.list_projects()
        
        self.assertGreaterEqual(len(projects), 2)

    def test_update_project_progress(self):
        """测试更新项目进度"""
        company = Company("测试公司")
        proj = company.create_project("新项目", "项目描述")
        
        company.update_project_progress(proj.id, 50)
        
        updated = company.get_project(proj.id)
        self.assertEqual(updated.progress, 50)
        # 注意：进度50%时status不会自动变为running，只有100%时才会变为completed

    def test_update_project_to_completed(self):
        """测试项目完成"""
        company = Company("测试公司")
        proj = company.create_project("新项目", "项目描述")
        
        company.update_project_progress(proj.id, 100)
        
        updated = company.get_project(proj.id)
        self.assertEqual(updated.progress, 100)
        self.assertEqual(updated.status, "completed")

    def test_create_task(self):
        """测试创建任务"""
        company = Company("测试公司")
        
        task = company.create_task("新任务", "任务描述", priority=2)
        
        self.assertIsNotNone(task.id)
        self.assertEqual(task.name, "新任务")
        self.assertEqual(task.priority, 2)

    def test_assign_task(self):
        """测试分配任务"""
        company = Company("测试公司")
        dept = company.add_department("研发部", "技术研发")
        emp = company.hire_employee("张三", "工程师", dept.id)
        task = company.create_task("新任务", "任务描述")
        
        result = company.assign_task(task.id, emp.id)
        
        self.assertTrue(result)
        updated_task = company.get_task(task.id)
        self.assertEqual(updated_task.assignee_id, emp.id)
        self.assertEqual(updated_task.status, "in_progress")

    def test_complete_task(self):
        """测试完成任务"""
        company = Company("测试公司")
        task = company.create_task("新任务", "任务描述")
        
        result = company.complete_task(task.id)
        
        self.assertTrue(result)
        completed = company.get_task(task.id)
        self.assertEqual(completed.status, "completed")

    def test_spend(self):
        """测试支出"""
        company = Company("测试公司")
        company.budget = 1000
        
        result = company.spend(500, "测试支出")
        
        self.assertTrue(result)
        self.assertEqual(company.spent, 500)
        self.assertEqual(company.get_balance(), 500)

    def test_spend_exceed_budget(self):
        """测试超出预算的支出"""
        company = Company("测试公司")
        company.budget = 1000
        
        result = company.spend(1500, "超额支出")
        
        self.assertFalse(result)
        self.assertEqual(company.spent, 0)

    def test_get_balance(self):
        """测试获取余额"""
        company = Company("测试公司")
        company.budget = 1000
        company.spent = 300
        
        balance = company.get_balance()
        
        self.assertEqual(balance, 700)

    def test_get_dashboard(self):
        """测试仪表板"""
        company = Company("测试公司")
        
        dashboard = company.get_dashboard()
        
        self.assertIn("company_name", dashboard)
        self.assertIn("departments", dashboard)
        self.assertIn("employees", dashboard)
        self.assertIn("projects", dashboard)
        self.assertIn("tasks", dashboard)
        self.assertIn("financial", dashboard)


if __name__ == "__main__":
    unittest.main()
