#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加GitHub地址到awesome_cpp_dataset.csv文件的脚本
从awesome-cpp README文件中解析项目的GitHub地址
"""

import re
import csv
import requests
from urllib.parse import urlparse
import sys
import time

def fetch_readme_content():
    """获取awesome-cpp的README内容"""
    url = "https://raw.githubusercontent.com/fffaraz/awesome-cpp/master/README.md"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"获取README失败: {e}")
        return None

def parse_github_urls(readme_content):
    """从README内容中解析项目名称和GitHub URL的映射"""
    # 匹配markdown链接格式: [project-name](https://github.com/...)
    # 也匹配其他格式如: * project-name - description [license]
    
    project_urls = {}
    
    # 主要的正则表达式模式
    patterns = [
        # 匹配 [name](https://github.com/...) 格式
        r'\*\s+\[([^\]]+)\]\((https://github\.com/[^)]+)\)',
        # 匹配 name - description [license] [website](https://github.com/...)
        r'\*\s+([^-\[]*).*?\[website\]\((https://github\.com/[^)]+)\)',
        # 匹配其他GitHub链接格式
        r'\*\s+([^-\[]*).*?(https://github\.com/[^)\s]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, readme_content, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                name, url = match
                name = name.strip()
                url = url.strip()
                
                # 清理项目名称
                name = re.sub(r'[^\w\-+.]', '', name)
                
                # 确保是GitHub URL
                if 'github.com' in url:
                    # 标准化URL格式
                    url = url.rstrip('/')
                    
                    # 存储多种可能的名称变体
                    project_urls[name.lower()] = url
                    
                    # 从URL中提取repo名称
                    url_parts = url.split('/')
                    if len(url_parts) >= 2:
                        repo_name = url_parts[-1]
                        project_urls[repo_name.lower()] = url
                        
                        # 移除常见后缀
                        repo_clean = repo_name.replace('-cpp', '').replace('cpp', '').replace('.js', '').replace('.h', '')
                        if repo_clean:
                            project_urls[repo_clean.lower()] = url
    
    return project_urls

def find_project_url(project_name, project_urls):
    """为给定的项目名称查找GitHub URL"""
    # 清理项目名称
    clean_name = project_name.lower().strip()
    
    # 直接匹配
    if clean_name in project_urls:
        return project_urls[clean_name]
    
    # 尝试不同的匹配策略
    variations = [
        clean_name.replace('-', ''),
        clean_name.replace('_', ''),
        clean_name.replace('.', ''),
        clean_name.replace('++', 'plusplus'),
        clean_name.replace('cpp', ''),
        clean_name.replace('c++', ''),
    ]
    
    for variation in variations:
        if variation in project_urls:
            return project_urls[variation]
    
    # 模糊匹配
    for stored_name, url in project_urls.items():
        if clean_name in stored_name or stored_name in clean_name:
            return url
    
    return None

def update_csv_with_github_urls(csv_file_path, project_urls):
    """更新CSV文件，添加GitHub URL列"""
    
    # 读取原始CSV文件
    rows = []
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"CSV文件不存在: {csv_file_path}")
        return False
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return False
    
    if not rows:
        print("CSV文件为空")
        return False
    
    # 检查并添加header
    header = rows[0]
    if len(header) < 3:  # 如果没有第三列，添加GitHub URL列
        header.append('github_url')
    elif header[2] != 'github_url':
        header[2] = 'github_url'
    
    # 处理数据行
    updated_count = 0
    for i, row in enumerate(rows[1:], 1):
        # 确保行有足够的列
        while len(row) < 3:
            row.append('')
        
        project_name = row[1] if len(row) > 1 else ''
        
        if project_name and not row[2]:  # 如果项目名存在且GitHub URL为空
            github_url = find_project_url(project_name, project_urls)
            if github_url:
                row[2] = github_url
                updated_count += 1
                print(f"找到 {project_name}: {github_url}")
            else:
                print(f"未找到 {project_name} 的GitHub地址")
    
    # 写回文件
    try:
        with open(csv_file_path, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        
        print(f"\n成功更新CSV文件!")
        print(f"总共更新了 {updated_count} 个项目的GitHub地址")
        return True
        
    except Exception as e:
        print(f"写入CSV文件失败: {e}")
        return False

def main():
    """主函数"""
    csv_file_path = "/Users/nike/code/spider/spider03/awesome_cpp_dataset.csv"
    
    print("开始获取awesome-cpp README内容...")
    readme_content = fetch_readme_content()
    
    if not readme_content:
        print("无法获取README内容，退出程序")
        return
    
    print("解析GitHub URL...")
    project_urls = parse_github_urls(readme_content)
    print(f"解析到 {len(project_urls)} 个项目URL映射")
    
    print(f"更新CSV文件: {csv_file_path}")
    success = update_csv_with_github_urls(csv_file_path, project_urls)
    
    if success:
        print("脚本执行完成!")
    else:
        print("脚本执行失败!")

if __name__ == "__main__":
    main()
