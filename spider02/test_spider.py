#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试异步爬虫功能 - 只爬取少量故事进行测试
"""

import asyncio
import time
from main_spider import OptimizedGushi365Spider

async def test_spider():
    print("开始测试故事365异步爬虫...")
    
    spider_config = {
        'max_concurrent': 5,     # 测试时使用较小并发数
        'request_delay': 0.5,    # 测试时使用较长间隔
    }
    
    total_count = 0
    start_time = time.time()
    
    async with OptimizedGushi365Spider(**spider_config) as spider:
        
        # 测试睡前故事（只爬取1页，最多3个故事）
        print("\n测试睡前故事...")
        try:
            count1 = await spider.crawl_category(
                "https://www.gushi365.com/shuiqiangushi/", 
                max_pages=1, 
                max_stories=3,
                stories_dir="test_stories_睡前故事"
            )
            print(f"睡前故事测试完成，保存了 {count1} 个故事")
            total_count += count1
        except Exception as e:
            print(f"睡前故事测试失败: {e}")
            count1 = 0
        
        # 测试寓言故事（只爬取1页，最多3个故事）
        print("\n测试寓言故事...")
        try:
            count2 = await spider.crawl_category(
                "https://www.gushi365.com/yuyangushi/", 
                max_pages=1, 
                max_stories=3,
                stories_dir="test_stories_寓言故事"
            )
            print(f"寓言故事测试完成，保存了 {count2} 个故事")
            total_count += count2
        except Exception as e:
            print(f"寓言故事测试失败: {e}")
            count2 = 0
    
    # 测试总结
    elapsed_time = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"测试完成！")
    print(f"- 总共保存: {total_count} 个故事")
    print(f"- 总耗时: {elapsed_time:.2f} 秒")
    if total_count > 0:
        print(f"- 平均速度: {elapsed_time/total_count:.2f} 秒/故事")
    print(f"{'='*50}")
    
    # 检查生成的文件
    import os
    for dirname in ["test_stories_睡前故事", "test_stories_寓言故事"]:
        if os.path.exists(dirname):
            files = os.listdir(dirname)
            print(f"\n{dirname} 目录包含 {len(files)} 个文件:")
            for file in files[:3]:  # 只显示前3个文件
                print(f"  - {file}")
            if len(files) > 3:
                print(f"  - ... 还有 {len(files)-3} 个文件")

if __name__ == "__main__":
    try:
        asyncio.run(test_spider())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试失败: {e}")
