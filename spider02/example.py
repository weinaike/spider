#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步爬虫使用示例
演示如何使用OptimizedGushi365Spider
"""

import asyncio
from main_spider import OptimizedGushi365Spider

async def example_single_category():
    """示例：爬取单个分类"""
    print("示例：爬取单个分类")
    print("-" * 40)
    
    # 配置爬虫参数
    spider_config = {
        'max_concurrent': 10,    # 并发数
        'request_delay': 0.3,    # 请求间隔
    }
    
    # 使用异步上下文管理器
    async with OptimizedGushi365Spider(**spider_config) as spider:
        success_count = await spider.crawl_category(
            category_url="https://www.gushi365.com/shuiqiangushi/",
            max_pages=2,         # 爬取2页
            max_stories=20,      # 最多20个故事
            stories_dir="example_stories"
        )
        
        print(f"成功爬取 {success_count} 个故事")

async def example_multiple_categories():
    """示例：爬取多个分类"""
    print("\n示例：爬取多个分类")
    print("-" * 40)
    
    categories = [
        ("睡前故事", "https://www.gushi365.com/shuiqiangushi/"),
        ("寓言故事", "https://www.gushi365.com/yuyangushi/")
    ]
    
    async with OptimizedGushi365Spider(max_concurrent=8, request_delay=0.4) as spider:
        total_stories = 0
        
        for category_name, category_url in categories:
            print(f"\n开始爬取: {category_name}")
            
            success_count = await spider.crawl_category(
                category_url=category_url,
                max_pages=1,
                max_stories=10,
                stories_dir=f"example_{category_name}"
            )
            
            total_stories += success_count
            print(f"{category_name} 完成，爬取了 {success_count} 个故事")
        
        print(f"\n总共爬取了 {total_stories} 个故事")

async def example_single_story():
    """示例：爬取单个故事"""
    print("\n示例：爬取单个故事")
    print("-" * 40)
    
    async with OptimizedGushi365Spider(max_concurrent=1, request_delay=0.5) as spider:
        # 解析单个故事内容
        story_data = await spider.parse_story_content(
            "https://www.gushi365.com/info/8194.html"
        )
        
        if story_data:
            print(f"故事标题: {story_data.title}")
            print(f"内容长度: {len(story_data.content)} 字符")
            print(f"作者: {story_data.author}")
            print(f"分类: {story_data.category}")
            
            # 保存故事
            success = await spider.save_story(story_data, "single_story_example")
            if success:
                print("故事保存成功")
        else:
            print("故事解析失败")

async def main():
    """主函数：运行所有示例"""
    print("故事365异步爬虫使用示例")
    print("=" * 50)
    
    # 运行示例
    await example_single_category()
    await example_multiple_categories()
    await example_single_story()
    
    print("\n所有示例完成！")

if __name__ == "__main__":
    asyncio.run(main())
