import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urljoin, urlparse, parse_qs
import re

class Gushi365Spider:
    def __init__(self):
        self.base_url = "https://www.gushi365.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def get_page(self, url, max_retries=3):
        """获取页面内容"""
        for attempt in range(max_retries):
            try:
                print(f"获取页面: {url} (尝试 {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except requests.RequestException as e:
                print(f"获取页面失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3 * (attempt + 1))  # 递增延迟
                else:
                    raise
    
    def parse_story_list(self, category_url, max_pages=None):
        """解析故事分类列表页面"""
        print(f"正在解析分类: {category_url}")
        
        all_stories = []
        page = 1
        
        while True:
            # 构建页面URL
            if page == 1:
                page_url = category_url
            else:
                # 根据网站结构，分页URL格式为 /category/index_2.html
                base_path = category_url.rstrip('/')
                page_url = f"{base_path}/index_{page}.html"
            
            try:
                html = self.get_page(page_url)
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找故事链接 - 根据网站结构，故事链接格式为 /info/数字.html
                story_links = soup.find_all('a', href=re.compile(r'/info/\d+\.html'))
                
                if not story_links:
                    print(f"第{page}页没有找到故事链接，停止爬取")
                    break
                
                page_stories = []
                for link in story_links:
                    story_url = urljoin(self.base_url, link['href'])
                    story_title = link.get_text(strip=True)
                    
                    # 提取故事ID
                    story_id = re.search(r'/info/(\d+)\.html', link['href'])
                    story_id = story_id.group(1) if story_id else None
                    
                    if story_title and story_url and story_id:
                        story_info = {
                            'id': story_id,
                            'title': story_title,
                            'url': story_url
                        }
                        
                        # 避免重复
                        if not any(s['id'] == story_id for s in all_stories):
                            page_stories.append(story_info)
                            all_stories.append(story_info)
                
                print(f"第{page}页找到 {len(page_stories)} 个新故事")
                
                # 检查是否有下一页
                next_page_link = soup.find('a', text='下一页') or soup.find('a', text=re.compile(r'下一页|下页'))
                if not next_page_link or (max_pages and page >= max_pages):
                    break
                
                page += 1
                time.sleep(2)  # 延迟避免频繁请求
                
            except Exception as e:
                print(f"解析第{page}页失败: {e}")
                break
        
        print(f"总共找到 {len(all_stories)} 个故事")
        return all_stories
    
    def parse_story_content(self, story_url):
        """解析单个故事内容"""
        print(f"正在解析故事: {story_url}")
        
        try:
            html = self.get_page(story_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取故事标题
            title_element = soup.find('h1')
            if not title_element:
                # 如果没有h1标签，从URL或其他地方提取标题
                title_links = soup.find_all('a', href=re.compile(r'/info/\d+\.html'))
                for link in title_links:
                    if story_url.endswith(link['href']):
                        title_element = link
                        break
            
            title = title_element.get_text(strip=True) if title_element else "无标题"
            
            # 移除网站后缀
            title = re.sub(r'\s*-\s*故事365.*$', '', title)
            title = re.sub(r'\s*【.*?】.*$', '', title)
            
            # 提取故事内容
            content = self._extract_story_content(soup)
            
            # 提取作者信息
            author = self._extract_author(soup)
            
            # 提取分类信息
            category = self._extract_category(soup)
            
            return {
                'title': title,
                'content': content,
                'author': author,
                'category': category,
                'url': story_url
            }
            
        except Exception as e:
            print(f"解析故事内容失败: {e}")
            return None
        
    def _extract_story_content(self, soup):
        """提取故事内容的主要逻辑"""
        content = ""
        
        # 移除不需要的元素
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # 查找故事内容 - 根据调试结果，故事内容主要在p标签中
        paragraphs = soup.find_all('p')
        story_paragraphs = []
        long_paragraph = None  # 用于存储最长的段落
        max_length = 0
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            
            # 过滤掉太短的段落
            if len(text) < 10:
                continue
                
            # 过滤掉包含网站信息的段落
            if any(keyword in text for keyword in [
                '故事365', '收藏', '分享', '评论', '阅读', '次数', 
                '版权', '标签', '作者', '日期', '分类', '发表评论',
                '用户名', '密码', '验证码', '注册', '登录',
                '相关故事', '推荐', '热门', '最新', '随机',
                '博客浏览', '在线投稿', '微信关注', '建站服务',
                '赞', '订阅', '继续阅读', '全文', '搜索', '导航',
                '首页', '幼儿', '童话', '发现', '少儿', '感人',
                'TAG', '影音', '图片', '儿童', '睡前', '益智',
                '排行榜', '上一篇', '下一篇'
            ]):
                continue
            
            # 检查是否包含中文标点符号（故事内容的特征）
            if any(punct in text for punct in ['。', '，', '！', '？', '：', '；', '"', '"']):
                story_paragraphs.append(text)
                
                # 记录最长的段落（通常是完整故事）
                if len(text) > max_length:
                    max_length = len(text)
                    long_paragraph = text
        
        # 优先使用最长的段落（如果它足够长，说明是完整故事）
        if long_paragraph and len(long_paragraph) > 500:
            content = long_paragraph
        elif story_paragraphs:
            # 如果没有足够长的单个段落，则检查是否需要组合多个段落
            # 但要避免包含已经被长段落覆盖的内容
            filtered_paragraphs = []
            
            for para in story_paragraphs:
                # 如果这个段落是长段落的子集，就跳过
                if long_paragraph and para in long_paragraph:
                    continue
                # 如果这个段落本身就是最长的段落，就跳过（避免重复）
                if para == long_paragraph:
                    continue
                filtered_paragraphs.append(para)
            
            # 如果有剩余的不重复段落，添加到内容中
            if filtered_paragraphs:
                if content:  # 如果已经有长段落
                    content += '\n\n' + '\n\n'.join(filtered_paragraphs)
                else:  # 如果没有长段落，使用组合的短段落
                    content = '\n\n'.join(filtered_paragraphs)
        else:
            # 备选方案：查找包含故事内容的div
            divs = soup.find_all('div')
            best_div = None
            max_story_length = 0
            
            for div in divs:
                div_text = div.get_text(strip=True)
                
                # 跳过太短的内容
                if len(div_text) < 200:
                    continue
                    
                # 跳过包含网站导航信息的div
                if any(keyword in div_text for keyword in [
                    '导航', '首页', '幼儿', '童话', '发现', '少儿', '感人',
                    'TAG', '影音', '图片', '儿童', '睡前', '益智', '排行榜'
                ]):
                    continue
                
                # 计算故事内容的得分（基于中文标点符号的数量）
                story_score = sum(div_text.count(punct) for punct in ['。', '，', '！', '？'])
                
                if story_score > max_story_length:
                    max_story_length = story_score
                    best_div = div
            
            if best_div:
                content = best_div.get_text(separator='\n', strip=True)
        
        # 清理内容
        if content:
            content = self._clean_content(content)
        
        return content
    
    def _clean_content(self, content):
        """清理故事内容"""
        # 移除无关信息
        lines = content.split('\n')
        cleaned_lines = []
        seen_lines = set()  # 用于去重
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 跳过包含这些关键词的行
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
                
            # 跳过纯数字或很短的行
            if len(line) < 5 or line.isdigit():
                continue
                
            # 跳过链接文本
            if line.startswith('http') or '点击' in line:
                continue
            
            # 去重 - 避免重复的段落
            if line in seen_lines:
                continue
            seen_lines.add(line)
                
            cleaned_lines.append(line)
        
        # 合并段落
        content = '\n\n'.join(cleaned_lines)
        
        # 处理段落格式
        content = re.sub(r'\n{3,}', '\n\n', content)  # 多个空行合并为两个
        content = re.sub(r'([。！？])\n([^\"\'])', r'\1\n\n\2', content)  # 句末换行改为段落分隔
        
        return content.strip()
    
    def _extract_author(self, soup):
        """提取作者信息"""
        author = ""
        
        # 查找作者信息
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
                
                # 提取作者名
                author_match = re.search(r'作者[：:]\s*([^\s]+)', author_text)
                if author_match:
                    author = author_match.group(1)
                    break
        
        return author
    
    def _extract_category(self, soup):
        """提取分类信息"""
        category = ""
        
        # 查找分类信息
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
    
    def save_story(self, story_data, stories_dir="stories"):
        """保存故事到文件"""
        if not story_data or not story_data.get('content'):
            print("故事内容为空，跳过保存")
            return False
            
        if not os.path.exists(stories_dir):
            os.makedirs(stories_dir)
        
        # 清理文件名
        title = story_data['title']
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = safe_title.replace(' ', '_')
        
        # 使用ID和标题作为文件名
        story_id = story_data.get('url', '').split('/')[-1].replace('.html', '')
        filename = f"{story_id}_{safe_title}.txt"
        filepath = os.path.join(stories_dir, filename)
        
        # 避免重复保存
        if os.path.exists(filepath):
            print(f"文件已存在，跳过: {filename}")
            return True
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"标题: {story_data['title']}\n")
                if story_data.get('author'):
                    f.write(f"作者: {story_data['author']}\n")
                if story_data.get('category'):
                    f.write(f"分类: {story_data['category']}\n")
                f.write(f"来源: {story_data['url']}\n")
                f.write("-" * 50 + "\n\n")
                f.write(story_data['content'])
            
            print(f"保存成功: {filename}")
            return True
            
        except Exception as e:
            print(f"保存失败 {filename}: {e}")
            return False
    
    def crawl_category(self, category_url, max_pages=None, max_stories=None, stories_dir=None):
        """爬取指定分类的所有故事"""
        print(f"开始爬取分类: {category_url}")
        
        # 解析故事列表
        stories = self.parse_story_list(category_url, max_pages)
        
        if max_stories:
            stories = stories[:max_stories]
        
        print(f"准备爬取 {len(stories)} 个故事")
        
        success_count = 0
        for i, story_info in enumerate(stories, 1):
            print(f"\n进度: {i}/{len(stories)} - {story_info['title']}")
            
            try:
                # 解析故事内容
                story_data = self.parse_story_content(story_info['url'])
                
                if story_data:
                    # 保存故事
                    save_dir = stories_dir or "stories"
                    if self.save_story(story_data, save_dir):
                        success_count += 1
                else:
                    print("解析故事内容失败")
                
                # 延迟避免频繁请求
                time.sleep(2)
                
            except Exception as e:
                print(f"处理故事失败: {e}")
                continue
        
        print(f"\n完成！成功保存 {success_count}/{len(stories)} 个故事")
        return success_count

if __name__ == "__main__":
    spider = Gushi365Spider()
    
    # 定义要爬取的分类
    categories = [
        ("童话故事", "https://www.gushi365.com/tonghuagushi/"),
        ("寓言故事", "https://www.gushi365.com/yuyangushi/")
    ]
    
    for category_name, category_url in categories:
        print(f"\n{'='*60}")
        print(f"开始爬取: {category_name}")
        print(f"{'='*60}")
        
        try:
            # 创建分类专用目录
            stories_dir = f"stories_{category_name}"
            if not os.path.exists(stories_dir):
                os.makedirs(stories_dir)
            print(f"创建目录: {stories_dir}")
            # 爬取该分类（限制前50页，每页约20个故事，防止过度爬取）
            spider.crawl_category(category_url, max_pages=50, max_stories=1000, stories_dir=stories_dir)
            
        except Exception as e:
            print(f"爬取 {category_name} 失败: {e}")
            continue
    
    print("\n所有分类爬取完成！")
