#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
365夜童话故事爬虫 - 完整版
用于爬取 https://www.lovechinese.org/reading/site/series/6 的所有故事
"""

from story_spider import StorySpider

def main():
    print("=" * 60)
    print("365夜童话故事爬虫 - 完整版")
    print("=" * 60)
    
    # 创建爬虫实例
    spider = StorySpider()
    
    # 目标URL
    target_url = "https://www.lovechinese.org/reading/site/series/6"
    
    print(f"开始爬取网站: {target_url}")
    print("注意: 这将爬取所有故事，可能需要较长时间...")
    
    # 询问用户是否继续
    user_input = input("是否继续？(y/n): ").lower().strip()
    
    if user_input not in ['y', 'yes', '是']:
        print("已取消爬取")
        return
    
    try:
        # 开始爬取所有故事
        stories = spider.crawl_stories(target_url)
        
        print("\n" + "=" * 60)
        print(f"爬取完成！")
        print(f"总共获取 {len(stories)} 个故事")
        print(f"故事文件保存在: stories/")
        print(f"汇总信息保存在: stories/stories_summary.json")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n用户中断了爬取过程")
    except Exception as e:
        print(f"\n爬取过程中出现错误: {e}")

if __name__ == "__main__":
    main()
