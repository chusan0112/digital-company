"""
测试扩展模块 - 财务、市场、满意度
"""

import pytest
import json
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFinanceExtended:
    """测试扩展财务模块"""
    
    def test_create_budget(self):
        """测试创建预算"""
        from domains.finance_extended import get_finance_service
        finance = get_finance_service()
        
        budget = finance.create_budget(
            name="测试预算",
            department_id="dept_001",
            fiscal_year=2026,
            amount=50000,
            category="R&D"
        )
        
        assert budget is not None
        assert budget.name == "测试预算"
        assert budget.amount == 50000
        assert budget.status == "draft"
    
    def test_budget_workflow(self):
        """测试预算审批流程"""
        from domains.finance_extended import get_finance_service
        finance = get_finance_service()
        
        # 创建预算
        budget = finance.create_budget(
            name="测试预算2",
            department_id="dept_002",
            fiscal_year=2026,
            amount=30000
        )
        
        # 提交审批
        result = finance.submit_budget(budget.id)
        assert result is True
        
        # 获取预算
        b = finance.get_budget(budget.id)
        assert b.status == "pending"
        
        # 审批通过
        result = finance.approve_budget(budget.id, "admin")
        assert result is True
        
        b = finance.get_budget(budget.id)
        assert b.status == "approved"
        assert b.approved_by == "admin"
    
    def test_add_cost(self):
        """测试添加成本记录"""
        from domains.finance_extended import get_finance_service
        finance = get_finance_service()
        
        cost = finance.add_cost(
            date="2026-03-22",
            department_id="dept_001",
            category="personnel",
            amount=5000,
            description="测试成本"
        )
        
        assert cost is not None
        assert cost.amount == 5000
        assert cost.category == "personnel"
    
    def test_cost_summary(self):
        """测试成本汇总"""
        from domains.finance_extended import get_finance_service
        finance = get_finance_service()
        
        summary = finance.get_cost_summary()
        
        assert "total" in summary
        assert "by_category" in summary
    
    def test_income_statement(self):
        """测试利润表"""
        from domains.finance_extended import get_finance_service
        finance = get_finance_service()
        
        statement = finance.generate_income_statement(
            period="monthly",
            start_date="2026-03-01",
            end_date="2026-03-31",
            revenue=100000,
            cost_of_goods_sold=40000,
            operating_expenses=20000,
            other_income=1000,
            other_expenses=500
        )
        
        assert statement.revenue == 100000
        assert statement.gross_profit == 60000  # 100000 - 40000
        # net_income = operating_income + other_income - other_expenses
        # = (gross_profit - operating_expenses) + other_income - other_expenses
        # = (60000 - 20000) + 1000 - 500 = 40000 + 500 = 40500
        assert statement.net_income == 40500
    
    def test_balance_sheet(self):
        """测试资产负债表"""
        from domains.finance_extended import get_finance_service
        finance = get_finance_service()
        
        sheet = finance.generate_balance_sheet(
            period="monthly",
            end_date="2026-03-31",
            cash=50000,
            accounts_receivable=20000,
            inventory=10000,
            accounts_payable=15000,
            short_term_debt=10000,
            long_term_debt=20000,
            owner_equity=30000,
            retained_earnings=5000
        )
        
        assert sheet.total_assets == 80000  # 50000 + 20000 + 10000
        assert sheet.total_liabilities == 45000  # 15000 + 10000 + 20000
        assert sheet.total_equity == 35000  # 30000 + 5000


class TestMarketService:
    """测试市场竞争模块"""
    
    def test_collect_market_data(self):
        """测试采集市场数据"""
        from domains.market_service import get_market_service
        market = get_market_service()
        
        data = market.collect_market_data(
            market_name="测试市场",
            industry="tech",
            total_market_size=1000000
        )
        
        assert data is not None
        assert data.market_name == "测试市场"
        assert data.industry == "tech"
        assert data.total_market_size == 1000000
    
    def test_add_competitor(self):
        """测试添加竞争对手"""
        from domains.market_service import get_market_service
        market = get_market_service()
        
        competitor = market.add_competitor(
            name="测试竞争公司",
            industry="tech",
            market_share=15,
            revenue=500000,
            strength_score=70,
            threat_level="medium"
        )
        
        assert competitor is not None
        assert competitor.name == "测试竞争公司"
        assert competitor.threat_level == "medium"
    
    def test_update_market_share(self):
        """测试更新市场份额"""
        from domains.market_service import get_market_service
        market = get_market_service()
        
        share = market.update_market_share(
            market_name="测试市场",
            company_name="金库集团",
            period="2026-03",
            share=10.5,
            revenue=100000
        )
        
        assert share is not None
        assert share.share == 10.5
        assert share.trend in ["growing", "stable", "declining"]
    
    def test_simulate_market_share(self):
        """测试市场份额模拟"""
        from domains.market_service import get_market_service
        market = get_market_service()
        
        # 先创建初始市场份额
        market.update_market_share(
            market_name="模拟市场",
            company_name="金库集团",
            period="2026-02",
            share=10,
            revenue=100000
        )
        
        result = market.simulate_market_share_change(
            company_name="金库集团",
            market_name="模拟市场",
            marketing_budget=20000,
            product_quality=80
        )
        
        assert result is not None
        assert "predicted_share" in result
        assert "factors" in result
    
    def test_generate_report(self):
        """测试生成市场报告"""
        from domains.market_service import get_market_service
        market = get_market_service()
        
        report = market.generate_market_report(
            market_name="测试市场",
            period="2026-03"
        )
        
        assert report is not None
        assert report.market_name == "测试市场"
        assert len(report.opportunities) > 0


class TestSatisfactionService:
    """测试员工满意度模块"""
    
    def test_create_survey(self):
        """测试创建满意度调查"""
        from domains.satisfaction_service import get_satisfaction_service
        satisfaction = get_satisfaction_service()
        
        survey = satisfaction.create_survey(
            title="Q1满意度调查",
            department_id="dept_001"
        )
        
        assert survey is not None
        assert survey.title == "Q1满意度调查"
        assert survey.status == "draft"
        assert len(survey.questions) > 0
    
    def test_survey_workflow(self):
        """测试问卷流程"""
        from domains.satisfaction_service import get_satisfaction_service
        satisfaction = get_satisfaction_service()
        
        # 创建问卷
        survey = satisfaction.create_survey(
            title="测试问卷",
            department_id="dept_test"
        )
        
        # 激活问卷
        result = satisfaction.activate_survey(survey.id)
        assert result is True
        
        s = satisfaction.get_survey(survey.id)
        assert s.status == "active"
        
        # 提交响应
        response = satisfaction.submit_response(
            survey_id=survey.id,
            employee_id="emp_001",
            responses={"q1": 80, "q2": 85, "q3": 90}
        )
        
        assert response is not None
        assert response.overall_score > 0
    
    def test_simulate_satisfaction(self):
        """测试模拟满意度数据"""
        from domains.satisfaction_service import get_satisfaction_service
        satisfaction = get_satisfaction_service()
        
        result = satisfaction.simulate_satisfaction_data(
            department_id="dept_sim",
            employee_count=5
        )
        
        assert result is not None
        assert result["response_count"] == 5
        assert "metrics" in result
        assert "insight" in result
    
    def test_calculate_metrics(self):
        """测试计算满意度指标"""
        from domains.satisfaction_service import get_satisfaction_service
        satisfaction = get_satisfaction_service()
        
        # 获取最近创建的问卷
        surveys = satisfaction.list_surveys(status="active")
        if surveys:
            survey = surveys[-1]
            metrics = satisfaction.calculate_metrics(
                survey_id=survey.id,
                department_id="dept_test"
            )
            
            assert metrics is not None
            assert metrics.overall_score > 0
    
    def test_generate_insights(self):
        """测试生成满意度洞察"""
        from domains.satisfaction_service import get_satisfaction_service
        satisfaction = get_satisfaction_service()
        
        insight = satisfaction.generate_insights("dept_sim")
        
        assert insight is not None
        assert insight.trend in ["improving", "stable", "declining"]
        assert insight.department_id == "dept_sim"


class TestAPIs:
    """测试API端点"""
    
    def test_finance_api_create_budget(self):
        """测试创建预算API"""
        from api import handle_request
        import json
        
        body = json.dumps({
            "name": "API测试预算",
            "department_id": "dept_api",
            "fiscal_year": 2026,
            "amount": 20000,
            "category": "operations"
        })
        
        result = handle_request("/api/finance/budget", "POST", body)
        assert result.get("success") is True
    
    def test_market_api_add_competitor(self):
        """测试添加竞争对手API"""
        from api import handle_request
        import json
        
        body = json.dumps({
            "name": "API竞争公司",
            "industry": "tech",
            "market_share": 20,
            "revenue": 800000,
            "strength_score": 75,
            "threat_level": "high"
        })
        
        result = handle_request("/api/market/competitor", "POST", body)
        assert result.get("success") is True
    
    def test_satisfaction_api_create_survey(self):
        """测试创建满意度调查API"""
        from api import handle_request
        import json
        
        body = json.dumps({
            "title": "API测试问卷",
            "department_id": "dept_api"
        })
        
        result = handle_request("/api/satisfaction/survey", "POST", body)
        assert result.get("success") is True
    
    def test_satisfaction_api_simulate(self):
        """测试模拟满意度API"""
        from api import handle_request
        import json
        
        body = json.dumps({
            "department_id": "dept_api_test",
            "employee_count": 3
        })
        
        result = handle_request("/api/satisfaction/simulate", "POST", body)
        assert result.get("success") is True
    
    def test_finance_summary_api(self):
        """测试财务汇总API"""
        from api import handle_request
        
        result = handle_request("/api/finance/summary", "GET")
        assert result.get("success") is True
        assert "summary" in result
    
    def test_market_overview_api(self):
        """测试市场概览API"""
        from api import handle_request
        import json
        
        # 先添加市场数据
        body = json.dumps({
            "market_name": "API测试市场",
            "industry": "tech",
            "total_market_size": 2000000
        })
        handle_request("/api/market/data", "POST", body)
        
        # GET请求不需要body参数
        result = handle_request("/api/market/overview", "GET")
        assert result.get("success") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
