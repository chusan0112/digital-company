#!/usr/bin/env python
"""
数字公司插件 - 启动入口
"""

import sys
import os


def _setup_utf8_console():
    """尽量将控制台输出切换为UTF-8，避免Windows编码异常。"""
    try:
        os.environ["PYTHONUTF8"] = "1"
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        # 不阻断主流程
        pass


# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from company import get_company
from web.server import start_server
from reporter import start_reporting
import threading


def main():
    """主函数"""
    _setup_utf8_console()

    print("=" * 50)
    print("  数字公司插件启动中...")
    print("=" * 50)
    
    # 初始化公司数据
    company = get_company()
    data = company.get_dashboard()
    
    print(f"  公司: {data['company_name']}")
    print(f"  员工: {data['employees']}人")
    print(f"  部门: {data['departments']}个")
    print(f"  资金: ¥{data['financial']['balance']}")
    print()
    
    # 启动Web服务器
    print("  驾驶舱地址: http://localhost:8080")
    print()
    
    # 启动定时汇报 (可选)
    # start_reporting(60)  # 注释掉，需要配置飞书Webhook
    
    # 启动Web服务
    start_server(8080)


if __name__ == "__main__":
    main()
