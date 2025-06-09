# Boss-Agent 企业级智能平台开发计划

## 1. 全局命名替换
- [x] 1.1 代码仓库、前端、后端所有“ii-agent”字符串替换为“boss-agent”
- [x] 1.2 检查 package.json、README、.env.example、docker-compose.yml、配置文件等全局命名
- [x] 1.3 检查API路由、服务名、前端title/描述等UI可见名称
- [x] 1.4 在 README.md 中补充知识库配置规范

## 2. 移除开发者工具集成
- [x] 2.1 移除前端页面“code”、“terminal”、“open with vscode”等入口、按钮、菜单
- [x] 2.2 删除相关 React/Vue 组件、hooks、状态和样式代码
- [x] 2.3 移除后端对应的API接口及服务逻辑
- [x] 2.4 根据您的指示，移除了前端的文件上传功能

## 3. 内外网内容搜索功能
- [x] 3.1 后端实现从“网站爬虫”重构为“本地文件系统检索引擎”
    - [x] 3.1.1 支持从 `config.ini` 配置文件中读取知识库根目录
    - [x] 3.1.2 支持递归搜索本地文件，并提取 .pdf, .docx, .txt 等多种格式的文本内容
- [x] 3.2 保留/完善外网内容搜索
- [x] 3.3 前端实现内外网搜索模式切换
- [x] 3.4 API参数增加search_mode，后端根据模式动态路由请求

## 4. 非对话式报告生成器 - 财务板块
- [x] 4.1 前端新增“财务报告”独立页面
- [x] 4.2 提供财报类型下拉选择
- [x] 4.3 提供时间维度选择组件
- [x] 4.4 提供“生成报告”按钮
- [x] 4.5 后端实现报告生成逻辑
    - [x] 4.5.1 根据前端选择的维度，在知识库中查找匹配的源文件
    - [x] 4.5.2 读取文件内容，并结合预设的 Prompt 模板，调用 LLM 生成结构化的报告
- [x] 4.6 在前端以图表和文本结合的方式展示报告
- [x] 4.7 在前端展示“打印”和“导出PDF”按钮（功能待实现）

## 5. 非对话式报告生成器 - 人事板块
- [x] 5.1 前端新增“人事”Tab/页面
- [x] 5.2 提供人事相关报表/分析类型下拉
- [x] 5.3 时间维度选择组件
- [x] 5.4 “生成报告”按钮与专属prompt模板
- [x] 5.5 展示人事报告内容
- [x] 5.6 后端API与权限校验

## 6. UI/UX 整体优化
- [x] 6.1 实现“顶部-内容-底部”三段式布局
- [x] 6.2 顶部包含 Logo、Slogan 和板块导航（助理、财务、人事）
- [x] 6.3 底部包含版权信息和链接
- [x] 6.4 修复内容区域高度和滚动问题
- [x] 6.5 修复输入框高度自适应问题
- [x] 6.6 对 UI 进行中文化处理

---

## 进阶与可选任务
- [ ] A.1 UI风格统一切换为明亮企业主题，适配Boss-Agent品牌色
- [ ] A.2 支持各板块权限与角色管理（如财务、人事、普通员工等）
- [ ] A.3 日志记录与操作审计
- [ ] A.4 支持多语言、国际化
- [ ] A.5 持续完善测试用例、自动化CI/CD


## Knowledge Base Setup (Important)

Boss-Agent is designed to work with a structured "Knowledge Base" on your local file system. This allows it to securely access and reason about your company's internal data.

### 1. Directory Structure

We recommend organizing your knowledge base by department and business function. This structure helps Boss-Agent to understand the context of your data and perform more accurate searches. Here is an example structure:

```
/path/to/your/knowledge_base/
├── finance/
│   ├── financial_reports/
│   ├── expense_reports/
│   └── invoices/
├── hr/
│   ├── employee_data/
│   └── performance_reviews/
├── sales/
│   ├── weekly_reports/
│   └── customer_feedback/
└── marketing/
    └── ...
```

### 2. File Naming Convention

A consistent file naming convention is crucial for time-based queries and reports. We recommend the following format:

`[YYYY-MM-DD]_[Theme]_[Optional-Description].[ext]`

**Examples:**
- `2024-Q2_income-statement.pdf`
- `2023_annual-report.txt`
- `2024-W26_sales-summary.html`

### 3. Supported File Formats

- **Directly Supported (Text-based):** `.txt`, `.md`, `.html`, `.csv`, `.json`
- **Automatic Text Extraction:** `.pdf`, `.docx`
- **Other Formats:** For other formats like Excel (`.xlsx`), we recommend exporting the data to a supported format (e.g., `.csv`) before placing it in the knowledge base.

### 4. Configuration

You must specify the path to your knowledge base in the `config.ini` file located in the root of the project.

```ini
[knowledge_base]
path = /path/to/your/knowledge_base
```
