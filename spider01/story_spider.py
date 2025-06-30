import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urljoin, urlparse
import re

class StorySpider:
    def __init__(self, base_url="https://www.lovechinese.org"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_page(self, url, max_retries=3):
        """获取页面内容"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except requests.RequestException as e:
                print(f"获取页面失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise
    
    def parse_story_list(self, url):
        """解析故事列表页面"""
        print(f"正在解析故事列表: {url}")
        html = self.get_page(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        stories = []
        
        # 查找所有故事链接
        story_links = soup.find_all('a', href=re.compile(r'/reading/site/story/\d+'))
        
        for link in story_links:
            story_url = urljoin(self.base_url, link['href'])
            story_title = link.get_text(strip=True)
            
            if story_title and story_url:
                stories.append({
                    'title': story_title,
                    'url': story_url,
                    'id': story_url.split('/')[-1]
                })
        
        print(f"找到 {len(stories)} 个故事")
        return stories
    
    def parse_story_content(self, story_url):
        """解析单个故事内容"""
        print(f"正在解析故事: {story_url}")
        
        try:
            html = self.get_page(story_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取故事标题
            title_element = soup.find('h1') or soup.find('title')
            title = title_element.get_text(strip=True) if title_element else "无标题"
            
            # 提取故事内容 - 尝试多种可能的选择器
            content = ""
            
            # 尝试常见的内容容器
            content_selectors = [
                'div.story-content',
                'div.content',
                'div.article-content',
                'div.main-content',
                'div.story',
                'article',
                'div.entry-content',
                '.story-text'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            # 如果没有找到特定的内容容器，尝试查找包含大量文本的div
            if not content_element:
                divs = soup.find_all('div')
                for div in divs:
                    text = div.get_text(strip=True)
                    if len(text) > 100:  # 假设故事内容至少有100个字符
                        content_element = div
                        break
            
            if content_element:
                # 清理内容
                # 移除脚本和样式
                for script in content_element(["script", "style"]):
                    script.decompose()
                
                # 获取文本内容
                content = content_element.get_text(separator='\n', strip=True)
                
                # 处理段落格式 - 将短句合并成完整段落
                content = self.format_story_content(content)
                
                # 清理多余的空行
                content = re.sub(r'\n\s*\n', '\n\n', content)
                content = content.strip()
            
            return {
                'title': title,
                'content': content,
                'url': story_url
            }
            
        except Exception as e:
            print(f"解析故事内容失败: {e}")
            return None
    
    def format_story_content(self, content):
        """格式化故事内容，将短句合并成完整段落"""
        lines = content.split('\n')
        formatted_lines = []
        current_paragraph = []
        in_dialogue = False
        
        for line in lines:
            line = line.strip()
            if not line:
                # 空行，结束当前段落
                if current_paragraph:
                    paragraph_text = ''.join(current_paragraph)
                    formatted_lines.append(paragraph_text)
                    current_paragraph = []
                # 保持空行作为段落分隔
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                continue
            
            # 检查是否是作者信息行
            if line.startswith('作者：') or line.startswith('〔') and '〕' in line:
                if current_paragraph:
                    paragraph_text = ''.join(current_paragraph)
                    formatted_lines.append(paragraph_text)
                    current_paragraph = []
                formatted_lines.append(line)  # 作者信息单独一行
                continue
            
            # 处理破折号连接的特殊情况
            if line.endswith('—') and not line.endswith('——'):
                current_paragraph.append(line)
                continue
            elif line.startswith('—') and current_paragraph:
                current_paragraph.append(line)
                # 破折号结束后检查句子是否完整
                if self.is_sentence_end(line):
                    paragraph_text = ''.join(current_paragraph)
                    formatted_lines.append(paragraph_text)
                    current_paragraph = []
                continue
            
            # 检查对话状态
            if line.startswith('"') or line.startswith('"'):
                in_dialogue = True
            
            # 将当前行添加到段落中
            current_paragraph.append(line)
            
            # 检查是否应该结束当前段落
            should_end_paragraph = False
            
            if in_dialogue:
                # 在对话中，只有对话结束才分段
                if (line.endswith('"') or line.endswith('"')) and not line.endswith('："') and not line.endswith('："'):
                    should_end_paragraph = True
                    in_dialogue = False
            else:
                # 非对话状态，按句号等标点分段
                if self.is_sentence_end(line):
                    should_end_paragraph = True
            
            # 特殊情况：如果这行很长且有明显的句子结束，也分段
            if len(line) > 50 and ('。' in line or '！' in line or '？' in line):
                # 检查是否有多个句子
                sentence_count = line.count('。') + line.count('！') + line.count('？')
                if sentence_count >= 2:
                    should_end_paragraph = True
            
            if should_end_paragraph:
                paragraph_text = ''.join(current_paragraph)
                formatted_lines.append(paragraph_text)
                current_paragraph = []
        
        # 处理最后一个段落
        if current_paragraph:
            paragraph_text = ''.join(current_paragraph)
            formatted_lines.append(paragraph_text)
        
        # 清理连续的空行，最多保留一个空行
        cleaned_lines = []
        prev_empty = False
        for line in formatted_lines:
            if line == '':
                if not prev_empty:
                    cleaned_lines.append(line)
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False
        
        return '\n'.join(cleaned_lines)
    
    def is_sentence_end(self, line):
        """判断是否是句子结尾"""
        # 去掉引号后检查
        line_clean = line.rstrip('""''')
        
        # 句子结束标志
        sentence_endings = ['。', '！', '？', '."', '!"', '?"', '。"', '！"', '？"']
        
        # 检查是否以句子结束符号结尾
        for ending in sentence_endings:
            if line_clean.endswith(ending):
                return True
        
        # 检查是否是对话结束（没有标点但有引号）
        if line.endswith('"') or line.endswith('"'):
            return True
            
        return False
    
    def crawl_stories(self, list_url, output_dir="stories", max_stories=None):
        """爬取所有故事"""
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 获取故事列表
        stories = self.parse_story_list(list_url)
        
        if max_stories:
            stories = stories[:max_stories]
        
        all_stories = []
        
        for i, story_info in enumerate(stories, 1):
            print(f"\n进度: {i}/{len(stories)} - {story_info['title']}")
            
            # 解析故事内容
            story_content = self.parse_story_content(story_info['url'])
            
            if story_content:
                # 合并故事信息
                story_data = {**story_info, **story_content}
                all_stories.append(story_data)
                
                # 保存单个故事到文件
                safe_title = re.sub(r'[^\w\s-]', '', story_info['title'])
                safe_title = re.sub(r'[-\s]+', '-', safe_title)
                filename = f"{story_info['id']}_{safe_title}.txt"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"标题: {story_content['title']}\n")
                    f.write(f"链接: {story_content['url']}\n")
                    f.write(f"ID: {story_info['id']}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(story_content['content'])
                
                print(f"已保存: {filename}")
            else:
                print(f"跳过故事: {story_info['title']}")
            
            # 添加延迟以避免请求过快
            time.sleep(1)
        
        # 保存所有故事的汇总信息
        summary_file = os.path.join(output_dir, "stories_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(all_stories, f, ensure_ascii=False, indent=2)
        
        print(f"\n爬取完成！共获取 {len(all_stories)} 个故事")
        print(f"故事保存在: {output_dir}")
        print(f"汇总信息保存在: {summary_file}")
        
        return all_stories
