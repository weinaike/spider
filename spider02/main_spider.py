import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin
import re
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class StoryInfo:
    id: str
    title: str
    url: str

@dataclass
class StoryData:
    title: str
    content: str
    author: str = ""
    category: str = ""
    url: str = ""

class OptimizedGushi365Spider:
    def __init__(self, max_concurrent=8, request_delay=0.8):
        self.base_url = "https://www.gushi365.com"
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        self.semaphore = None
        self.session = None
        self.cache = {}  # 简单的内存缓存
        
        # 增强的请求头 - 模拟真实浏览器
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 配置连接池和超时 - 更保守的设置
        connector = aiohttp.TCPConnector(
            limit=30,   # 降低总连接池大小
            limit_per_host=8,  # 降低每个主机的连接数
            ttl_dns_cache=300,  # DNS缓存时间
            use_dns_cache=True,
            keepalive_timeout=30,  # 保持连接时间
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=15,   # 增加总超时时间
            connect=8,  # 增加连接超时
            sock_read=8  # 增加读取超时
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        
        # 预热：先访问主页，建立会话
        await self._warmup_session()
        
        return self
    
    async def _warmup_session(self):
        """预热会话，模拟真实用户访问"""
        try:
            logger.info("预热会话，访问主页...")
            await self.get_page(self.base_url)
            await asyncio.sleep(2.0)  # 停留2秒
            logger.info("会话预热完成")
        except Exception as e:
            logger.warning(f"会话预热失败，但继续执行: {e}")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    def _get_cache_key(self, url: str) -> str:
        """生成缓存键"""
        return hashlib.md5(url.encode()).hexdigest()
    
    async def get_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """异步获取页面内容，带缓存和增强的反反爬虫策略"""
        cache_key = self._get_cache_key(url)
        
        # 检查缓存
        if cache_key in self.cache:
            logger.debug(f"从缓存获取: {url}")
            return self.cache[cache_key]
        
        async with self.semaphore:  # 限制并发数
            for attempt in range(max_retries):
                try:
                    logger.debug(f"获取页面: {url} (尝试 {attempt + 1}/{max_retries})")
                    
                    # 随机延迟，模拟人类行为
                    if attempt > 0:
                        import random
                        delay = random.uniform(1.0, 3.0)
                        await asyncio.sleep(delay)
                    
                    # 动态更新Referer头
                    headers = self.headers.copy()
                    if '/info/' in url:
                        # 详情页请求时添加分类页面作为Referer
                        if 'tonghuagushi' in url:
                            headers['Referer'] = 'https://www.gushi365.com/tonghuagushi/'
                        elif 'yuyangushi' in url:
                            headers['Referer'] = 'https://www.gushi365.com/yuyangushi/'
                    
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text(encoding='utf-8', errors='ignore')
                            
                            # 缓存结果
                            self.cache[cache_key] = content
                            
                            # 添加请求延时，随机化延迟时间
                            if self.request_delay > 0:
                                import random
                                actual_delay = random.uniform(self.request_delay * 0.8, self.request_delay * 1.2)
                                await asyncio.sleep(actual_delay)
                            
                            return content
                        elif response.status == 403:
                            logger.warning(f"HTTP 403 (被拒绝访问): {url}")
                            # 403错误时增加更长的延迟
                            await asyncio.sleep(3.0 * (attempt + 1))
                        else:
                            logger.warning(f"HTTP {response.status}: {url}")
                            
                except asyncio.TimeoutError:
                    logger.warning(f"请求超时: {url} (尝试 {attempt + 1})")
                    # 超时后增加延迟
                    await asyncio.sleep(2.0 * (attempt + 1))
                except Exception as e:
                    logger.warning(f"请求失败: {url} - {e} (尝试 {attempt + 1})")
                    # 其他错误也增加延迟
                    await asyncio.sleep(1.5 * (attempt + 1))
                
                if attempt < max_retries - 1:
                    # 递增延迟，给服务器更多时间
                    await asyncio.sleep(2.0 * (attempt + 1))
            
            logger.error(f"获取页面最终失败: {url}")
            return None
    
    async def parse_story_list(self, category_url: str, max_pages: Optional[int] = None) -> List[StoryInfo]:
        """异步解析故事分类列表页面"""
        logger.info(f"正在解析分类: {category_url}")
        
        all_stories = []
        page = 1
        
        # 并发获取多个页面
        page_tasks = []
        
        while True:
            # 构建页面URL
            if page == 1:
                page_url = category_url
            else:
                base_path = category_url.rstrip('/')
                page_url = f"{base_path}/index_{page}.html"
            
            page_tasks.append(self.parse_single_page(page_url, page))
            
            if max_pages and page >= max_pages:
                break
            
            # 每次批量处理5页，避免过度并发
            if len(page_tasks) >= 5:
                break
                
            page += 1
        
        # 并发执行页面解析
        page_results = await asyncio.gather(*page_tasks, return_exceptions=True)
        
        for result in page_results:
            if isinstance(result, Exception):
                logger.error(f"页面解析失败: {result}")
                continue
            
            if result:  # result 是 (page_num, stories) 元组
                page_num, stories = result
                logger.info(f"第{page_num}页找到 {len(stories)} 个故事")
                
                for story in stories:
                    # 避免重复
                    if not any(s.id == story.id for s in all_stories):
                        all_stories.append(story)
        
        logger.info(f"总共找到 {len(all_stories)} 个故事")
        return all_stories
    
    async def parse_single_page(self, page_url: str, page_num: int) -> Optional[tuple]:
        """解析单个列表页面"""
        try:
            html = await self.get_page(page_url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找故事链接
            story_links = soup.find_all('a', href=re.compile(r'/info/\d+\.html'))
            
            if not story_links:
                logger.debug(f"第{page_num}页没有找到故事链接")
                return None
            
            stories = []
            for link in story_links:
                story_url = urljoin(self.base_url, link['href'])
                story_title = link.get_text(strip=True)
                
                # 提取故事ID
                story_id = re.search(r'/info/(\d+)\.html', link['href'])
                story_id = story_id.group(1) if story_id else None
                
                if story_title and story_url and story_id:
                    stories.append(StoryInfo(
                        id=story_id,
                        title=story_title,
                        url=story_url
                    ))
            
            return (page_num, stories)
            
        except Exception as e:
            logger.error(f"解析第{page_num}页失败: {e}")
            return None
    
    async def parse_story_content(self, story_url: str) -> Optional[StoryData]:
        """异步解析单个故事内容"""
        try:
            html = await self.get_page(story_url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取故事标题
            title_element = soup.find('h1')
            if not title_element:
                title_links = soup.find_all('a', href=re.compile(r'/info/\d+\.html'))
                for link in title_links:
                    if story_url.endswith(link['href']):
                        title_element = link
                        break
            
            title = title_element.get_text(strip=True) if title_element else "无标题"
            
            # 清理标题
            title = re.sub(r'\s*-\s*故事365.*$', '', title)
            title = re.sub(r'\s*【.*?】.*$', '', title)
            
            # 提取故事内容
            content = self._extract_story_content(soup)
            
            # 提取作者和分类信息
            author = self._extract_author(soup)
            category = self._extract_category(soup)
            
            return StoryData(
                title=title,
                content=content,
                author=author,
                category=category,
                url=story_url
            )
            
        except Exception as e:
            logger.error(f"解析故事内容失败 {story_url}: {e}")
            return None
    
    def _extract_story_content(self, soup):
        """提取故事内容的主要逻辑"""
        # 移除不需要的元素
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # 查找故事内容
        paragraphs = soup.find_all('p')
        story_paragraphs = []
        long_paragraph = None
        max_length = 0
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            
            if len(text) < 10:
                continue
                
            # 过滤网站信息
            skip_keywords = [
                '故事365', '收藏', '分享', '评论', '阅读', '次数', 
                '版权', '标签', '作者', '日期', '分类', '发表评论',
                '用户名', '密码', '验证码', '注册', '登录',
                '相关故事', '推荐', '热门', '最新', '随机',
                '博客浏览', '在线投稿', '微信关注', '建站服务',
                '赞', '订阅', '继续阅读', '全文', '搜索', '导航',
                '首页', '幼儿', '童话', '发现', '少儿', '感人',
                'TAG', '影音', '图片', '儿童', '睡前', '益智',
                '排行榜', '上一篇', '下一篇'
            ]
            
            if any(keyword in text for keyword in skip_keywords):
                continue
            
            # 检查中文标点符号
            if any(punct in text for punct in ['。', '，', '！', '？', '：', '；', '"', '"']):
                story_paragraphs.append(text)
                
                if len(text) > max_length:
                    max_length = len(text)
                    long_paragraph = text
        
        # 选择最佳内容
        content = ""
        if long_paragraph and len(long_paragraph) > 500:
            content = long_paragraph
        elif story_paragraphs:
            filtered_paragraphs = []
            
            for para in story_paragraphs:
                if long_paragraph and para in long_paragraph:
                    continue
                if para == long_paragraph:
                    continue
                filtered_paragraphs.append(para)
            
            if filtered_paragraphs:
                if content:
                    content += '\n\n' + '\n\n'.join(filtered_paragraphs)
                else:
                    content = '\n\n'.join(filtered_paragraphs)
        
        # 清理内容
        if content:
            content = self._clean_content(content)
        
        return content
    
    def _clean_content(self, content):
        """清理故事内容"""
        lines = content.split('\n')
        cleaned_lines = []
        seen_lines = set()
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5 or line.isdigit():
                continue
                
            skip_keywords = [
                '故事365', '收藏', '分享', '评论', '阅读', '次数', 
                '版权', '标签', '作者', '日期', '分类', '发表评论',
                '用户名', '密码', '验证码', '注册', '登录',
                '相关故事', '推荐', '热门', '最新', '随机',
                '博客浏览', '在线投稿', '微信关注', '建站服务',
                '赞', '订阅', '继续阅读', '全文', '搜索', '导航',
                '首页', '幼儿', '童话', '发现', '少儿', '感人',
                'TAG', '影音', '图片', '儿童', '睡前', '益智',
                '排行榜', '上一篇', '下一篇', '鸟类中的骗子',
                '｜', '——'
            ]
            
            if any(keyword in line for keyword in skip_keywords):
                continue
                
            if line.startswith('http') or '点击' in line:
                continue
            
            if line in seen_lines:
                continue
            seen_lines.add(line)
                
            cleaned_lines.append(line)
        
        content = '\n\n'.join(cleaned_lines)
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r'([。！？])\n([^\"\'])', r'\1\n\n\2', content)
        
        return content.strip()
    
    def _extract_author(self, soup):
        """提取作者信息"""
        author = ""
        
        author_patterns = [
            soup.find(text=re.compile(r'作者[：:]')),
            soup.find('span', text=re.compile(r'作者')),
            soup.find('div', class_=re.compile(r'author')),
        ]
        
        for pattern in author_patterns:
            if pattern:
                if hasattr(pattern, 'parent'):
                    author_text = pattern.parent.get_text(strip=True)
                else:
                    author_text = str(pattern).strip()
                
                author_match = re.search(r'作者[：:]\s*([^\s]+)', author_text)
                if author_match:
                    author = author_match.group(1)
                    break
        
        return author
    
    def _extract_category(self, soup):
        """提取分类信息"""
        category = ""
        
        category_patterns = [
            soup.find('a', href=re.compile(r'/(shuiqiangushi|yuyangushi)/')),
            soup.find(text=re.compile(r'分类[：:]')),
            soup.find('span', text=re.compile(r'分类')),
        ]
        
        for pattern in category_patterns:
            if pattern:
                if hasattr(pattern, 'get_text'):
                    category = pattern.get_text(strip=True)
                elif hasattr(pattern, 'parent'):
                    category = pattern.parent.get_text(strip=True)
                else:
                    category = str(pattern).strip()
                break
        
        return category
    
    async def save_story(self, story_data: StoryData, stories_dir: str = "stories") -> bool:
        """异步保存故事到文件"""
        if not story_data or not story_data.content:
            logger.debug("故事内容为空，跳过保存")
            return False
            
        if not os.path.exists(stories_dir):
            os.makedirs(stories_dir)
        
        # 清理文件名
        safe_title = re.sub(r'[<>:"/\\|?*]', '', story_data.title)
        safe_title = safe_title.replace(' ', '_')
        
        # 从URL提取ID
        story_id = story_data.url.split('/')[-1].replace('.html', '')
        filename = f"{story_id}_{safe_title}.txt"
        filepath = os.path.join(stories_dir, filename)
        
        # 避免重复保存
        if os.path.exists(filepath):
            logger.debug(f"文件已存在，跳过: {filename}")
            return True
        
        try:
            # 使用异步文件操作
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(f"标题: {story_data.title}\n")
                if story_data.author:
                    await f.write(f"作者: {story_data.author}\n")
                if story_data.category:
                    await f.write(f"分类: {story_data.category}\n")
                await f.write(f"来源: {story_data.url}\n")
                await f.write("-" * 50 + "\n\n")
                await f.write(story_data.content)
            
            logger.info(f"保存成功: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"保存失败 {filename}: {e}")
            return False
    
    async def crawl_category(self, category_url: str, max_pages: Optional[int] = None, 
                           max_stories: Optional[int] = None, stories_dir: Optional[str] = None) -> int:
        """异步爬取指定分类的所有故事"""
        logger.info(f"开始爬取分类: {category_url}")
        
        # 解析故事列表
        stories = await self.parse_story_list(category_url, max_pages)
        
        if max_stories:
            stories = stories[:max_stories]
        
        logger.info(f"准备爬取 {len(stories)} 个故事")
        
        if not stories:
            return 0
        
        # 并发爬取故事内容
        save_dir = stories_dir or "stories"
        
        # 创建任务列表，每次处理的并发数
        batch_size = min(self.max_concurrent, len(stories))
        success_count = 0
        
        for i in range(0, len(stories), batch_size):
            batch = stories[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}: {len(batch)} 个故事")
            
            # 并发处理一批故事
            tasks = [self.process_single_story(story, save_dir) for story in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计成功数量
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"处理故事失败: {result}")
                elif result:
                    success_count += 1
            
            logger.info(f"批次完成，当前成功: {success_count}")
        
        logger.info(f"完成！成功保存 {success_count}/{len(stories)} 个故事")
        return success_count
    
    async def process_single_story(self, story_info: StoryInfo, save_dir: str) -> bool:
        """处理单个故事"""
        try:
            logger.debug(f"处理故事: {story_info.title}")
            
            # 解析故事内容
            story_data = await self.parse_story_content(story_info.url)
            
            if story_data:
                # 保存故事
                return await self.save_story(story_data, save_dir)
            else:
                logger.warning(f"解析故事内容失败: {story_info.title}")
                return False
                
        except Exception as e:
            logger.error(f"处理故事失败 {story_info.title}: {e}")
            return False

# 使用示例
async def main():
    # 配置爬虫参数
    spider_config = {
        'max_concurrent': 15,  # 并发数
        'request_delay': 0.3,  # 请求间隔（秒）
    }
    
    # 定义要爬取的分类
    categories = [
        ("睡前故事", "https://www.gushi365.com/shuiqiangushi/"),
        ("寓言故事", "https://www.gushi365.com/yuyangushi/")
    ]
    
    async with OptimizedGushi365Spider(**spider_config) as spider:
        for category_name, category_url in categories:
            logger.info(f"\n{'='*60}")
            logger.info(f"开始爬取: {category_name}")
            logger.info(f"{'='*60}")
            
            try:
                # 创建分类专用目录
                stories_dir = f"stories_{category_name}"
                
                # 记录开始时间
                start_time = time.time()
                
                # 爬取该分类
                success_count = await spider.crawl_category(
                    category_url, 
                    max_pages=3, 
                    max_stories=50, 
                    stories_dir=stories_dir
                )
                
                # 记录耗时
                elapsed_time = time.time() - start_time
                logger.info(f"{category_name} 爬取完成！")
                logger.info(f"成功数量: {success_count}")
                logger.info(f"耗时: {elapsed_time:.2f} 秒")
                
            except Exception as e:
                logger.error(f"爬取 {category_name} 失败: {e}")
                continue
    
    logger.info("\n所有分类爬取完成！")

if __name__ == "__main__":
    asyncio.run(main())
