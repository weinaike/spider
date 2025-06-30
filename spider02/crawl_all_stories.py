#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故事365网站异步爬虫 - 高性能版本
专门爬取睡前故事和寓言故事
使用方法：python crawl_all_stories.py
"""

import asyncio
import sys
import os
import time
from main_spider import OptimizedGushi365Spider

async def main():
    print("故事365网站异步爬虫 - 高性能版本")
    print("=" * 60)
    
    # 爬虫配置 - 更保守的设置以避免被封
    spider_config = {
        'max_concurrent': 4,     # 降低并发数
        'request_delay': 1.2,    # 增加请求间隔
    }
    
    # 定义要爬取的分类
    categories = [
        ("童话故事", "https://www.gushi365.com/tonghuagushi/"),
        ("寓言故事", "https://www.gushi365.com/yuyangushi/")
    ]
    
    total_stories = 0
    total_start_time = time.time()
    
    async with OptimizedGushi365Spider(**spider_config) as spider:
        for category_name, category_url in categories:
            print(f"\n{'='*60}")
            print(f"开始爬取: {category_name}")
            print(f"URL: {category_url}")
            print(f"{'='*60}")
            
            try:
                # 创建分类专用目录
                stories_dir = f"stories_{category_name}"
                if not os.path.exists(stories_dir):
                    os.makedirs(stories_dir)
                
                # 记录开始时间
                start_time = time.time()
                
                # 爬取该分类（高性能并发爬取）
                count = await spider.crawl_category(
                    category_url, 
                    max_pages=50,      # 爬取50页
                    max_stories=1000,  # 每个分类最多1000个故事
                    stories_dir=stories_dir
                )
                
                # 记录耗时
                elapsed_time = time.time() - start_time
                total_stories += count
                
                print(f"\n{category_name} 爬取完成！")
                print(f"- 成功保存: {count} 个故事")
                print(f"- 耗时: {elapsed_time:.2f} 秒")
                if count > 0:
                    print(f"- 平均速度: {elapsed_time/count:.2f} 秒/故事")
                
            except KeyboardInterrupt:
                print("\n用户中断爬取")
                break
            except Exception as e:
                print(f"爬取 {category_name} 失败: {e}")
                continue
    
    # 总结
    total_elapsed_time = time.time() - total_start_time
    print(f"\n{'='*60}")
    print(f"爬取完成！")
    print(f"- 总共保存: {total_stories} 个故事")
    print(f"- 总耗时: {total_elapsed_time:.2f} 秒")
    if total_stories > 0:
        print(f"- 平均速度: {total_elapsed_time/total_stories:.2f} 秒/故事")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行失败: {e}")
        sys.exit(1)
