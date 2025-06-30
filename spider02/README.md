# 故事365异步爬虫 - 高性能版本

这是一个基于异步协程的高性能故事365网站爬虫，使用aiohttp和asyncio实现并发爬取。

## ✨ 特性

- 🚀 **高性能异步**: 基于协程的并发处理，性能提升5-10倍
- 🔄 **智能并发控制**: 可配置并发数量，避免过度请求
- 💾 **内存缓存**: 避免重复请求相同URL
- 📁 **批量处理**: 分批处理故事，优化内存使用
- 🛡️ **错误重试**: 智能重试机制，提高成功率
- 📝 **异步文件IO**: 使用aiofiles提升文件写入性能

## 📦 依赖安装

```bash
pip install aiohttp aiofiles beautifulsoup4 lxml
```

## 🚀 使用方法

### 基本使用

```python
import asyncio
from main_spider import OptimizedGushi365Spider

async def main():
    async with OptimizedGushi365Spider(max_concurrent=15, request_delay=0.3) as spider:
        success_count = await spider.crawl_category(
            category_url="https://www.gushi365.com/shuiqiangushi/",
            max_pages=3,
            max_stories=50,
            stories_dir="stories_睡前故事"
        )
        print(f"成功爬取 {success_count} 个故事")

if __name__ == "__main__":
    asyncio.run(main())
```

### 直接运行

```bash
python main_spider.py
```

### 批量爬取多个分类

```bash
python crawl_all_stories.py
```
## ⚙️ 配置参数

```python
spider_config = {
    'max_concurrent': 15,    # 最大并发数（建议10-20）
    'request_delay': 0.3,    # 请求间隔秒数（建议0.2-0.5）
}
```

## 📊 性能对比

| 版本 | 处理方式 | 性能提升 | 内存占用 |
|------|----------|----------|----------|
| 原版 | 串行 | 基准 | 低 |
| 异步版 | 协程并发 | **5-10倍** | 低 |

## 🎯 优化亮点

### 并发处理
- 使用asyncio协程实现真正的异步IO
- 信号量控制并发数量，避免过载
- 批量处理避免内存溢出

### 网络优化
- TCP连接池复用连接
- 智能缓存避免重复请求
- 优化的超时和重试策略

### 文件操作
- 异步文件IO避免阻塞
- 智能文件名处理
- 避免重复保存

## 📁 输出格式

每个故事保存为独立的txt文件：

```
标题: 故事标题
作者: 作者名称
分类: 故事分类
来源: 原始URL
--------------------------------------------------

故事内容...
```

## 🔧 高级配置

### 连接池配置
```python
connector = aiohttp.TCPConnector(
    limit=100,              # 总连接池大小
    limit_per_host=20,      # 每个主机连接数
    ttl_dns_cache=300,      # DNS缓存时间
)
```

### 超时配置
```python
timeout = aiohttp.ClientTimeout(
    total=10,               # 总超时时间
    connect=5,              # 连接超时
    sock_read=5             # 读取超时
)
```

## 🛡️ 最佳实践

1. **并发控制**: 根据目标网站负载调整并发数
2. **请求间隔**: 设置合理延时避免IP被封
3. **错误处理**: 监控成功率，调整重试策略
4. **内存管理**: 大批量爬取时分批处理

## ⚠️ 注意事项

1. 遵守网站robots.txt协议
2. 合理设置并发数和延时
3. 仅供学习和个人使用
4. 监控爬取状态和错误率

## 🐛 故障排除

### 常见问题
- **连接超时**: 降低并发数或增加延时
- **内存不足**: 减少批次大小
- **IP限制**: 增加请求间隔

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 性能监控

爬虫会自动记录：
- 请求成功率
- 平均响应时间
- 并发处理状态
- 文件保存结果
   A: 在 `crawl_all_stories.py` 中修改 `max_pages` 和 `max_stories` 参数

2. **Q: 爬取速度太慢？**
   A: 可以在 `story_spider.py` 中减少 `time.sleep()` 的时间，但不建议设置过小

3. **Q: 某些故事内容不完整？**
   A: 网站的HTML结构可能有变化，可以检查并修改内容提取逻辑

## 更新日志

- v1.0: 初始版本，支持睡前故事和寓言故事爬取
