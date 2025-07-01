#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版的GitHub地址添加脚本，包含详细统计和验证功能
"""

import re
import csv
import requests
from urllib.parse import urlparse
import sys
import time

def main():
    """主函数 - 生成统计报告"""
    csv_file_path = "/Users/nike/code/spider/spider03/awesome_cpp_dataset.csv"
    
    print("=== awesome-cpp GitHub地址统计报告 ===\n")
    
    # 读取CSV文件
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return

    if len(rows) < 2:
        print("CSV文件内容不足")
        return

    header = rows[0]
    data_rows = rows[1:]
    
    total_projects = len(data_rows)
    projects_with_github = 0
    projects_without_github = 0
    
    github_domains = {}
    project_categories = {}
    
    print(f"总项目数: {total_projects}")
    print(f"CSV文件结构: {', '.join(header)}")
    print()
    
    # 分析数据
    for row in data_rows:
        if len(row) >= 3:
            path = row[0]
            project_name = row[1]
            github_url = row[2] if len(row) > 2 else ""
            
            if github_url:
                projects_with_github += 1
                
                # 提取域名和用户名
                try:
                    parsed = urlparse(github_url)
                    domain = parsed.netloc
                    path_parts = parsed.path.strip('/').split('/')
                    if len(path_parts) >= 2:
                        username = path_parts[0]
                        repo_name = path_parts[1]
                        
                        if domain not in github_domains:
                            github_domains[domain] = 0
                        github_domains[domain] += 1
                        
                except Exception:
                    pass
            else:
                projects_without_github += 1
    
    print(f"有GitHub地址的项目: {projects_with_github} ({projects_with_github/total_projects*100:.1f}%)")
    print(f"没有GitHub地址的项目: {projects_without_github} ({projects_without_github/total_projects*100:.1f}%)")
    print()
    
    # 域名统计
    print("GitHub域名分布:")
    for domain, count in sorted(github_domains.items(), key=lambda x: x[1], reverse=True):
        print(f"  {domain}: {count} 个项目")
    print()
    
    # 显示前20个项目作为示例
    print("前20个项目示例:")
    print("-" * 80)
    for i, row in enumerate(data_rows[:20]):
        if len(row) >= 3:
            project_name = row[1]
            github_url = row[2] if len(row) > 2 else "无"
            print(f"{i+1:2d}. {project_name:<25} {github_url}")
    print()
    
    # 保存简化的统计文件
    stats_file = "/Users/nike/code/spider/spider03/github_stats.txt"
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("awesome-cpp项目GitHub地址统计报告\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"统计时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总项目数: {total_projects}\n")
            f.write(f"有GitHub地址: {projects_with_github} ({projects_with_github/total_projects*100:.1f}%)\n")
            f.write(f"没有GitHub地址: {projects_without_github} ({projects_without_github/total_projects*100:.1f}%)\n\n")
            
            f.write("域名分布:\n")
            for domain, count in sorted(github_domains.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {domain}: {count}\n")
        
        print(f"统计报告已保存到: {stats_file}")
        
    except Exception as e:
        print(f"保存统计文件失败: {e}")

if __name__ == "__main__":
    main()
