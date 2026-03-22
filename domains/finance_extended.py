"""
扩展财务模块 - 预算编制、成本核算、利润表、资产负债表
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict
import uuid
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "storage")


# ============== 预算管理 ==============

@dataclass
class Budget:
    """预算"""
    id: str
    name: str
    department_id: str
    fiscal_year: int
    amount: float
    spent: float = 0
    status: str = "draft"  # draft, pending, approved, rejected
    created_at: str = ""
    approved_at: str = ""
    approved_by: str = ""
    category: str = "general"  # general, marketing, R&D, operations
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return Budget(**d)


@dataclass
class BudgetItem:
    """预算项目明细"""
    id: str
    budget_id: str
    name: str
    planned_amount: float
    actual_amount: float = 0
    category: str = "general"
    description: str = ""
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return BudgetItem(**d)


# ============== 成本核算 ==============

@dataclass
class CostRecord:
    """成本记录"""
    id: str
    date: str
    department_id: str
    category: str  # personnel, materials, equipment, marketing, other
    amount: float
    project_id: str = ""
    description: str = ""
    vendor: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return CostRecord(**d)


# ============== 财务报表 ==============

@dataclass
class IncomeStatement:
    """利润表"""
    id: str
    period: str  # monthly, quarterly, yearly
    start_date: str
    end_date: str
    revenue: float = 0
    cost_of_goods_sold: float = 0
    gross_profit: float = 0
    operating_expenses: float = 0
    operating_income: float = 0
    other_income: float = 0
    other_expenses: float = 0
    net_income: float = 0
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        # 计算毛利和净收入
        self.gross_profit = self.revenue - self.cost_of_goods_sold
        self.operating_income = self.gross_profit - self.operating_expenses
        self.net_income = self.operating_income + self.other_income - self.other_expenses
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return IncomeStatement(**d)


@dataclass
class BalanceSheet:
    """资产负债表"""
    id: str
    period: str
    end_date: str
    
    # 资产
    cash: float = 0
    accounts_receivable: float = 0
    inventory: float = 0
    total_assets: float = 0
    
    # 负债
    accounts_payable: float = 0
    short_term_debt: float = 0
    long_term_debt: float = 0
    total_liabilities: float = 0
    
    # 所有者权益
    owner_equity: float = 0
    retained_earnings: float = 0
    total_equity: float = 0
    
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.total_assets = self.cash + self.accounts_receivable + self.inventory
        self.total_liabilities = self.accounts_payable + self.short_term_debt + self.long_term_debt
        self.total_equity = self.owner_equity + self.retained_earnings
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(d):
        return BalanceSheet(**d)


# ============== 财务服务类 ==============

class FinanceExtendedService:
    """扩展财务服务"""
    
    def __init__(self):
        self.budgets: List[Budget] = []
        self.budget_items: List[BudgetItem] = []
        self.cost_records: List[CostRecord] = []
        self.income_statements: List[IncomeStatement] = []
        self.balance_sheets: List[BalanceSheet] = []
        self.load()
    
    def _get_data_file(self, name: str) -> str:
        os.makedirs(DATA_DIR, exist_ok=True)
        return os.path.join(DATA_DIR, f"finance_{name}.json")
    
    def save(self):
        """保存所有数据"""
        with open(self._get_data_file("budgets"), "w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in self.budgets], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("budget_items"), "w", encoding="utf-8") as f:
            json.dump([i.to_dict() for i in self.budget_items], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("costs"), "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self.cost_records], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("income_statements"), "w", encoding="utf-8") as f:
            json.dump([i.to_dict() for i in self.income_statements], f, ensure_ascii=False, indent=2)
        with open(self._get_data_file("balance_sheets"), "w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in self.balance_sheets], f, ensure_ascii=False, indent=2)
    
    def load(self):
        """加载数据"""
        # 预算
        if os.path.exists(self._get_data_file("budgets")):
            with open(self._get_data_file("budgets"), "r", encoding="utf-8") as f:
                self.budgets = [Budget.from_dict(b) for b in json.load(f)]
        # 预算项目
        if os.path.exists(self._get_data_file("budget_items")):
            with open(self._get_data_file("budget_items"), "r", encoding="utf-8") as f:
                self.budget_items = [BudgetItem.from_dict(i) for i in json.load(f)]
        # 成本记录
        if os.path.exists(self._get_data_file("costs")):
            with open(self._get_data_file("costs"), "r", encoding="utf-8") as f:
                self.cost_records = [CostRecord.from_dict(c) for c in json.load(f)]
        # 利润表
        if os.path.exists(self._get_data_file("income_statements")):
            with open(self._get_data_file("income_statements"), "r", encoding="utf-8") as f:
                self.income_statements = [IncomeStatement.from_dict(i) for i in json.load(f)]
        # 资产负债表
        if os.path.exists(self._get_data_file("balance_sheets")):
            with open(self._get_data_file("balance_sheets"), "r", encoding="utf-8") as f:
                self.balance_sheets = [BalanceSheet.from_dict(b) for b in json.load(f)]
    
    # ---------- 预算管理 ----------
    
    def create_budget(self, name: str, department_id: str, fiscal_year: int, 
                     amount: float, category: str = "general") -> Budget:
        """创建预算"""
        budget = Budget(
            id=str(uuid.uuid4())[:8],
            name=name,
            department_id=department_id,
            fiscal_year=fiscal_year,
            amount=amount,
            category=category,
            status="draft"
        )
        self.budgets.append(budget)
        self.save()
        return budget
    
    def submit_budget(self, budget_id: str) -> bool:
        """提交预算审批"""
        for b in self.budgets:
            if b.id == budget_id:
                b.status = "pending"
                self.save()
                return True
        return False
    
    def approve_budget(self, budget_id: str, approved_by: str) -> bool:
        """审批预算"""
        for b in self.budgets:
            if b.id == budget_id:
                b.status = "approved"
                b.approved_at = datetime.now().isoformat()
                b.approved_by = approved_by
                self.save()
                return True
        return False
    
    def reject_budget(self, budget_id: str) -> bool:
        """拒绝预算"""
        for b in self.budgets:
            if b.id == budget_id:
                b.status = "rejected"
                self.save()
                return True
        return False
    
    def get_budget(self, budget_id: str) -> Optional[Budget]:
        for b in self.budgets:
            if b.id == budget_id:
                return b
        return None
    
    def list_budgets(self, department_id: str = None, status: str = None, 
                    fiscal_year: int = None) -> List[Budget]:
        result = self.budgets
        if department_id:
            result = [b for b in result if b.department_id == department_id]
        if status:
            result = [b for b in result if b.status == status]
        if fiscal_year:
            result = [b for b in result if b.fiscal_year == fiscal_year]
        return result
    
    def add_budget_item(self, budget_id: str, name: str, planned_amount: float,
                       category: str = "general", description: str = "") -> Optional[BudgetItem]:
        """添加预算项目明细"""
        if not self.get_budget(budget_id):
            return None
        item = BudgetItem(
            id=str(uuid.uuid4())[:8],
            budget_id=budget_id,
            name=name,
            planned_amount=planned_amount,
            category=category,
            description=description
        )
        self.budget_items.append(item)
        self.save()
        return item
    
    def get_budget_items(self, budget_id: str) -> List[BudgetItem]:
        return [i for i in self.budget_items if i.budget_id == budget_id]
    
    def update_budget_spent(self, budget_id: str, amount: float):
        """更新预算支出"""
        for b in self.budgets:
            if b.id == budget_id:
                b.spent += amount
                self.save()
                return True
        return False
    
    def get_budget_utilization(self, budget_id: str) -> dict:
        """获取预算使用率"""
        budget = self.get_budget(budget_id)
        if not budget:
            return {}
        utilization = (budget.spent / budget.amount * 100) if budget.amount > 0 else 0
        return {
            "budget_id": budget_id,
            "budget_name": budget.name,
            "total": budget.amount,
            "spent": budget.spent,
            "remaining": budget.amount - budget.spent,
            "utilization": round(utilization, 2)
        }
    
    # ---------- 成本核算 ----------
    
    def add_cost(self, date: str, department_id: str, category: str,
                amount: float, description: str = "", 
                project_id: str = "", vendor: str = "") -> CostRecord:
        """添加成本记录"""
        cost = CostRecord(
            id=str(uuid.uuid4())[:8],
            date=date,
            department_id=department_id,
            project_id=project_id,
            category=category,
            amount=amount,
            description=description,
            vendor=vendor
        )
        self.cost_records.append(cost)
        # 更新对应预算的支出
        budgets = self.list_budgets(department_id=department_id, status="approved")
        if budgets:
            self.update_budget_spent(budgets[0].id, amount)
        self.save()
        return cost
    
    def get_costs(self, department_id: str = None, project_id: str = None,
                 category: str = None, start_date: str = None,
                 end_date: str = None) -> List[CostRecord]:
        """查询成本记录"""
        result = self.cost_records
        if department_id:
            result = [c for c in result if c.department_id == department_id]
        if project_id:
            result = [c for c in result if c.project_id == project_id]
        if category:
            result = [c for c in result if c.category == category]
        if start_date:
            result = [c for c in result if c.date >= start_date]
        if end_date:
            result = [c for c in result if c.date <= end_date]
        return result
    
    def get_cost_summary(self, department_id: str = None, 
                       start_date: str = None, end_date: str = None) -> dict:
        """获取成本汇总"""
        costs = self.get_costs(department_id, start_date=start_date, end_date=end_date)
        
        # 按类别汇总
        by_category = {}
        for c in costs:
            if c.category not in by_category:
                by_category[c.category] = 0
            by_category[c.category] += c.amount
        
        total = sum(c.amount for c in costs)
        
        return {
            "total": total,
            "by_category": by_category,
            "count": len(costs),
            "department_id": department_id,
            "start_date": start_date,
            "end_date": end_date
        }
    
    # ---------- 利润表 ----------
    
    def generate_income_statement(self, period: str, start_date: str, end_date: str,
                                 revenue: float, cost_of_goods_sold: float,
                                 operating_expenses: float, other_income: float = 0,
                                 other_expenses: float = 0) -> IncomeStatement:
        """生成利润表"""
        statement = IncomeStatement(
            id=str(uuid.uuid4())[:8],
            period=period,
            start_date=start_date,
            end_date=end_date,
            revenue=revenue,
            cost_of_goods_sold=cost_of_goods_sold,
            operating_expenses=operating_expenses,
            other_income=other_income,
            other_expenses=other_expenses
        )
        self.income_statements.append(statement)
        self.save()
        return statement
    
    def get_income_statements(self, period: str = None) -> List[IncomeStatement]:
        if period:
            return [s for s in self.income_statements if s.period == period]
        return self.income_statements
    
    # ---------- 资产负债表 ----------
    
    def generate_balance_sheet(self, period: str, end_date: str,
                              cash: float, accounts_receivable: float = 0,
                              inventory: float = 0, accounts_payable: float = 0,
                              short_term_debt: float = 0, long_term_debt: float = 0,
                              owner_equity: float = 0, retained_earnings: float = 0) -> BalanceSheet:
        """生成资产负债表"""
        sheet = BalanceSheet(
            id=str(uuid.uuid4())[:8],
            period=period,
            end_date=end_date,
            cash=cash,
            accounts_receivable=accounts_receivable,
            inventory=inventory,
            accounts_payable=accounts_payable,
            short_term_debt=short_term_debt,
            long_term_debt=long_term_debt,
            owner_equity=owner_equity,
            retained_earnings=retained_earnings
        )
        self.balance_sheets.append(sheet)
        self.save()
        return sheet
    
    def get_balance_sheets(self, period: str = None) -> List[BalanceSheet]:
        if period:
            return [s for s in self.balance_sheets if s.period == period]
        return self.balance_sheets
    
    # ---------- 财务报表汇总 ----------
    
    def get_financial_summary(self) -> dict:
        """获取财务汇总"""
        # 预算汇总
        total_budget = sum(b.amount for b in self.budgets)
        approved_budget = sum(b.amount for b in self.budgets if b.status == "approved")
        total_spent = sum(b.spent for b in self.budgets)
        
        # 成本汇总
        total_costs = sum(c.amount for c in self.cost_records)
        
        # 成本按类别
        cost_by_category = {}
        for c in self.cost_records:
            if c.category not in cost_by_category:
                cost_by_category[c.category] = 0
            cost_by_category[c.category] += c.amount
        
        # 最新利润表
        latest_income = self.income_statements[-1] if self.income_statements else None
        
        # 最新资产负债表
        latest_balance = self.balance_sheets[-1] if self.balance_sheets else None
        
        return {
            "budget": {
                "total": total_budget,
                "approved": approved_budget,
                "spent": total_spent,
                "utilization": round(total_spent / total_budget * 100, 2) if total_budget > 0 else 0
            },
            "costs": {
                "total": total_costs,
                "by_category": cost_by_category
            },
            "income_statement": latest_income.to_dict() if latest_income else None,
            "balance_sheet": latest_balance.to_dict() if latest_balance else None
        }


# 全局实例
_finance_service: Optional[FinanceExtendedService] = None


def get_finance_service() -> FinanceExtendedService:
    global _finance_service
    if _finance_service is None:
        _finance_service = FinanceExtendedService()
    return _finance_service
