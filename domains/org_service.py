"""Organization domain service."""

from company import get_company


def create_business_unit(name: str, description: str = "新业务事业部") -> dict:
    company = get_company()
    dept = company.add_department(name=name, description=description)
    return dept.to_dict()
