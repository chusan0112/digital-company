#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for intent parser and smart recruitment
Run: python core/test_recruitment.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent_parser import AIExpertRegistry, parse_chairman_command, SmartRecruiter


def main():
    print("=" * 70)
    print("Intent Parser + Smart Recruitment Demo")
    print("=" * 70)
    
    test_cases = [
        # Original requirements
        ("I want to make money", "我想赚钱"),
        ("Start a Xiaohongshu business", "做小红书创业"),
        ("Write code", "写代码"),
        ("Analyze stocks", "分析股票"),
        ("Create short videos", "做短视频"),
        # Additional cases
        ("Build an e-commerce website", "做电商网站"),
        ("Need a financial advisor", "需要财务顾问"),
        ("Analyze market", "分析市场"),
        ("Douyin operations", "抖音运营"),
    ]
    
    registry = AIExpertRegistry()
    
    print("\n=== AI Expert Templates Available ===")
    print(f"Total experts: {len(registry.EXPERTS)}")
    for name, config in registry.EXPERTS.items():
        print(f"  - {name}: {config['skills']}")
    
    print("\n" + "=" * 70)
    print("Testing Intent Parsing")
    print("=" * 70)
    
    for en_text, cn_text in test_cases:
        print(f"\n>>> Input: {cn_text} ({en_text})")
        print("-" * 50)
        
        # Parse intent
        result = parse_chairman_command(cn_text)
        print(f"  Intent: {result['intent']}")
        print(f"  Business: {result['business_name']}")
        print(f"  Budget: {result['budget_cap']}")
        print(f"  Deadline: {result['deadline']}")
        
        # Recommend experts
        experts = result.get('recommended_experts', [])
        print(f"  Recommended Experts ({len(experts)}):")
        for exp in experts:
            print(f"    * {exp['name']}")
            print(f"      Skills: {', '.join(exp['skills'])}")
            print(f"      Confidence: {exp['confidence']*100:.1f}%")
            if exp.get('matched_keywords'):
                print(f"      Matched: {exp['matched_keywords']}")
    
    print("\n" + "=" * 70)
    print("Smart Recruitment Simulation")
    print("=" * 70)
    
    recruiter = SmartRecruiter()
    
    recruit_tests = [
        "我想做小红书创业",
        "需要写代码开发网站",
        "想分析股票赚钱",
        "帮我做个电商平台"
    ]
    
    for req in recruit_tests:
        print(f"\n>>> Request: {req}")
        
        result = recruiter.parse_and_recruit(req)
        print(f"  Action: {result['action_summary']}")
        
        for exp in result['recommended_experts']:
            print(f"    -> Would recruit: {exp['name']} ({', '.join(exp['skills'])})")
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
