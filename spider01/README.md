# 365夜童话故事爬虫

这个爬虫用于爬取 https://www.lovechinese.org/reading/site/series/6 页面上的童话故事内容。

## 功能特点

- 自动解析故事列表页面，获取所有故事链接
- 逐个爬取每个故事的完整内容
- **智能段落格式化**：将短句合并成完整段落，提升阅读体验
- 智能内容提取，支持多种页面结构
- 自动保存故事到本地文件
- 生成JSON格式的汇总文件
- 包含错误处理和重试机制
- 添加请求延迟避免过快访问

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 测试运行（爬取前5个故事）

```bash
python story_spider.py
```

这将爬取前5个故事作为测试，确保爬虫正常工作。

### 2. 爬取所有故事

```bash
python crawl_all_stories.py
```

这将爬取网站上的所有365个童话故事。程序会询问确认后开始爬取。

### 3. 自定义爬取

```python
# 创建爬虫实例
spider = StorySpider()

# 爬取指定数量的故事
stories = spider.crawl_stories(
    "https://www.lovechinese.org/reading/site/series/6",
    output_dir="my_stories",  # 自定义输出目录
    max_stories=10            # 限制爬取数量
)
```

### 4. 重新格式化已爬取的文件

如果你已经爬取了一些故事但格式不理想，可以使用格式化工具：

```bash
python reformat_stories.py
```

这将重新处理 `stories/` 目录中的所有故事文件，将短句合并成完整段落。

```python
# 创建爬虫实例
spider = StorySpider()

# 爬取指定数量的故事
stories = spider.crawl_stories(
    "https://www.lovechinese.org/reading/site/series/6",
    output_dir="my_stories",  # 自定义输出目录
    max_stories=10            # 限制爬取数量
)
```

## 输出结构

程序会创建一个 `stories` 目录（或你指定的目录），包含：

1. **单个故事文件**：每个故事保存为单独的txt文件
   - 文件名格式：`{故事ID}_{故事标题}.txt`
   - 包含标题、链接、ID和完整内容

2. **汇总文件**：`stories_summary.json`
   - JSON格式，包含所有故事的元数据和内容

## 示例输出

```
stories/
├── 634_49只纸船和49只风筝.txt
├── 635_一个萝卜.txt
├── 636_一只笨老狼.txt
├── ...
└── stories_summary.json
```

## 配置选项

### 修改请求头
```python
spider = StorySpider()
spider.session.headers.update({
    'User-Agent': '你的User-Agent'
})
```

### 修改延迟时间
在 `crawl_stories` 方法中修改：
```python
time.sleep(1)  # 修改为你想要的延迟秒数
```

## 注意事项

1. **请求频率**：程序默认在每个请求之间添加1秒延迟，请尊重网站的访问规则
2. **网络问题**：如果遇到网络错误，程序会自动重试最多3次
3. **内容解析**：程序使用多种策略来提取故事内容，适应不同的页面结构
4. **文件名**：自动处理特殊字符，确保文件名在各操作系统下都有效

## 错误处理

- 网络请求失败会自动重试
- 解析失败的故事会被跳过并记录
- 程序会显示详细的进度信息

## 扩展功能

你可以轻松扩展这个爬虫：

1. **添加更多输出格式**：支持CSV、XML等格式
2. **数据库存储**：将故事保存到数据库
3. **图片下载**：如果故事包含图片，可以添加图片下载功能
4. **多线程**：添加多线程支持提高爬取速度

## 法律声明

请确保你的使用符合网站的服务条款和相关法律法规。本工具仅供学习和研究使用。
