"""
OpenClaw集成测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from company import get_company


def test_openclaw_integration():
    """测试OpenClaw集成"""
    print("=" * 50)
    print("OpenClaw集成测试")
    print("=" * 50)
    
    company = get_company()
    
    # 1. 列出当前员工
    print("\n[1] 当前员工列表:")
    employees = company.list_employees()
    for emp in employees:
        agent_id = emp.openclaw_agent_id if hasattr(emp, 'openclaw_agent_id') else ""
        print(f"  - {emp.name} ({emp.role})")
        print(f"    ID: {emp.id}")
        print(f"    OpenClaw Agent: {agent_id if agent_id else '无'}")
        print(f"    Status: {emp.status}")
    
    # 2. 招聘新员工（创建OpenClaw Agent）
    print("\n[2] 招聘新员工:")
    dept_id = company.departments[1].id if len(company.departments) > 1 else ""
    new_emp = company.hire_employee(
        name="AI工程师",
        role="高级工程师",
        department_id=dept_id,
        skills=["Python", "AI", "机器学习"],
        create_openclaw_agent=True
    )
    print(f"  新员工: {new_emp.name}")
    print(f"  OpenClaw Agent ID: {new_emp.openclaw_agent_id}")
    
    # 3. 测试获取员工Agent信息
    print("\n[3] 获取员工Agent信息:")
    if new_emp.openclaw_agent_id:
        agent_info = company.get_employee_agent(new_emp.id)
        if agent_info:
            print(f"  Agent名称: {agent_info.name}")
            print(f"  Agent状态: {agent_info.status}")
            print(f"  工作区: {agent_info.workspace}")
    
    # 4. 测试状态同步
    print("\n[4] 测试状态同步:")
    company.sync_agent_status(emp_id=new_emp.id)
    emp = company.get_employee(new_emp.id)
    print(f"  同步后员工状态: {emp.status}")
    
    # 5. 列出所有OpenClaw Agents
    print("\n[5] OpenClaw Agents列表:")
    try:
        from integrations.openclaw_client import get_openclaw_client
        client = get_openclaw_client()
        agents = client.list_agents()
        print(f"  共 {len(agents)} 个Agent")
        for agent in agents:
            print(f"  - {agent.name}: {agent.status}")
    except Exception as e:
        print(f"  列出Agent失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    test_openclaw_integration()
