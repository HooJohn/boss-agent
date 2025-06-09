<div align="center">
  <img src="assets/boss.png" width="200"/>

# Boss Agent: 智能决策与分析AI平台

[![GitHub stars](https://img.shields.io/github/stars/Intelligent-Internet/boss-agent?style=social)](https://github.com/Intelligent-Internet/boss-agent/stargazers)
[![Discord Follow](https://dcbadge.vercel.app/api/server/yDWPsshPHB?style=flat)](https://discord.gg/yDWPsshPHB)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

</div>

**Boss-Agent** 是一个开源的、为企业设计的智能决策与分析AI平台。它旨在通过先进的AI Agent技术，将大型语言模型（LLM）的能力与企业内部数据和业务流程深度融合，从而赋能企业，实现数据驱动的智能决策。

与传统的被动式工具不同，Boss-Agent 是一个能够自主理解、规划并执行复杂任务的智能系统，致力于成为企业管理者和员工的得力AI助手。


---

## 核心功能

Boss-Agent 提供了一系列强大的功能，使其能够胜任多种复杂的业务场景：

-   **多模态交互**: 支持处理和理解文本、PDF、Word文档等多种格式的信息。
-   **强大的工具集**:
    -   **内外网搜索**: 结合Tavily、SerpAPI等工具，实现全面的互联网信息检索与企业内部知识库的精准搜索。
    -   **浏览器自动化**: 内置基于Playwright的浏览器控制工具，能够自主浏览网页、提取信息、填充表单，完成复杂的在线任务。
    -   **文件操作**: 支持读、写、修改本地文件，能够生成报告、编写代码、整理数据。
    -   **代码执行**: 能够在安全的环境中执行Shell命令，完成系统操作和自动化脚本任务。
-   **ReAct工作流**: 基于“思考-行动”（Reason-Act）的先进Agent工作流，使其能够分解复杂任务、制定执行计划、并根据中间结果进行调整和反思。
-   **实时交互界面**: 提供基于React和WebSocket的现代化Web界面，用户可以实时观察Agent的思考过程和每一步行动，极大地提升了透明度和信任感。
-   **可扩展的架构**: 系统设计高度模块化，可以轻松集成不同的LLM（已支持Anthropic Claude, Google Gemini, OpenAI GPT系列）和自定义工具。
-   **企业知识库**: 能够连接到本地文件系统，构建企业专属知识库，让AI在充分理解企业内部信息的基础上进行决策和分析。

## 技术架构

项目采用前后端分离的现代Web架构，确保了系统的灵活性和可扩展性。

-   **后端**: 使用 **Python 3.10+** 和 **FastAPI** 框架构建，通过 **WebSocket** 提供实时通信服务。
-   **前端**: 使用 **Next.js (React)** 和 **TypeScript** 构建，提供响应式、交互友好的用户界面。
-   **核心Agent**: 基于 **ReAct** 模式，结合 **LangChain** 和 **LlamaIndex** 的思想，实现了强大的工具调用和任务规划能力。

### 架构示意图

```mermaid
graph TD
    subgraph 前端 (浏览器)
        A[用户界面 (React/Next.js)] --> B{应用/UI状态 (React Context)};
        B --> A;
        A -- 用户操作 --> C[WebSocket通信钩子];
        C -- 服务端事件 --> B;
        C -- 发送消息 --> D[后端WebSocket];
    end

    subgraph 后端 (服务器)
        D -- 接收消息 --> E[FastAPI WebSocket服务器];
        E -- 创建/管理 --> F[Agent核心 (AnthropicFC)];
        F -- 使用 --> G[工具管理器];
        G -- 执行 --> H[具体工具 (网页搜索, 浏览器等)];
        F -- 交互 --> I[LLM客户端 (Anthropic/Gemini/OpenAI)];
        F -- 推送/接收事件 --> J[内存消息队列];
        E -- 从队列消费 --> J;
        J -- 推送事件 --> D;
        F -- 持久化 --> K[数据库 (SQLite)];
        E -- 读取 --> K;
    end

    I -- API调用 --> L[外部LLM API];
    H -- 执行动作 --> M[外部世界 (网络, 文件系统)];

    style A fill:#cde4ff
    style E fill:#d5f0d5
```

## 安装与启动

我们推荐使用 Docker 进行一键部署，同时也提供完整的手动安装步骤。

### 1. 环境准备

-   安装 [Docker](https://www.docker.com/) 和 Docker Compose。
-   安装 [Python 3.10+](https://www.python.org/)。
-   安装 [Node.js 18+](https://nodejs.org/) 和 npm。
-   准备至少一个LLM的API Key（Anthropic, Google Gemini, 或 OpenAI）。
-   准备一个搜索服务的API Key（推荐 [Tavily](https://tavily.com/)）。

### 2. 配置

项目需要两个 `.env` 文件来分别配置前端和后端。

#### a. 后端配置

在项目的**根目录**下，复制 `.env.example` 并重命名为 `.env`。

```bash
# .env 文件

# 静态文件基础URL (用于访问工作区文件)
STATIC_FILE_BASE_URL=http://localhost:8000/

# LLM API Keys (至少选择一个)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
GEMINI_API_KEY=xxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxx

# 搜索服务 API Key (必需)
TAVILY_API_KEY=tvly-xxxxxxxx

# 其他可选的高级服务API Keys
# JINA_API_KEY=...
# FIRECRAWL_API_KEY=...
# SERPAPI_API_KEY=...
```

#### b. 前端配置

在 `frontend/` 目录下，创建一个 `.env` 文件。

```bash
# frontend/.env 文件

# 指向你的后端服务地址
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### c. 知识库与Agent配置

在项目**根目录**下，编辑 `config.ini` 文件。

```ini
[knowledge_base]
# 指定你的企业知识库的本地路径
path = /path/to/your/knowledge_base

[agent]
# Agent执行任务的最大循环次数
max_turns = 200
# Agent每次调用LLM时生成的最大token数
max_output_tokens_per_turn = 32000
```

### 3. 启动项目

#### a. Docker 启动 (推荐)

这是最简单、最稳定的启动方式。

```bash
# 赋予启动/停止脚本执行权限
chmod +x start.sh stop.sh

# 启动服务
./start.sh

# 如果遇到Docker相关的错误，可以尝试强制重新创建容器
# ./start.sh --force-recreate
```

服务启动后，通过浏览器访问 `http://localhost:3000` 即可使用。

要停止服务，运行 `./stop.sh`。

#### b. 手动启动 (用于开发)

如果你想对代码进行修改和调试，可以选择手动启动。

**启动后端:**

```bash
# 1. (可选) 创建并激活Python虚拟环境
python -m venv .venv
source .venv/bin/activate  # 在 Windows 上: .venv\Scripts\activate

# 2. 安装依赖
pip install -e .

# 3. 启动WebSocket服务器
python ws_server.py --port 8000
```

**启动前端:**

打开**新的**终端窗口。

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

服务启动后，通过浏览器访问 `http://localhost:3000`。

## 测试指南

为确保代码质量和功能稳定性，我们使用 `pytest` 作为后端的测试框架。

### 运行现有测试

在项目根目录下，激活Python虚拟环境后，直接运行：

```bash
pytest
```

`pytest` 会自动发现并执行 `tests/` 目录下的所有测试用例。

### 当前测试覆盖

项目目前包含以下几个方面的单元测试：

-   **消息历史**: `tests/test_message_history.py`
-   **核心工具**:
    -   Bash命令执行: `tests/tools/test_bash_tool.py`
    -   序列化思考: `tests/tools/test_sequential_thinking_tool.py`
    -   字符串替换: `tests/tools/test_str_replace_tool.py`
-   **LLM模块**:
    -   上下文摘要: `tests/llm/context_manager/test_llm_summarizing.py`

### 编写新测试

当您为项目添加新功能（尤其是新的工具）时，请务必为其编写配套的测试用例。

1.  在 `tests/` 目录下，参照现有结构创建新的测试文件，文件名以 `test_` 开头。
2.  在文件中，使用标准的 `pytest` 语法编写断言和测试函数。

**前端测试**:
前端目前暂未配置测试脚本。未来的工作可以考虑引入 [Jest](https://jestjs.io/) 和 [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) 来进行单元测试和组件测试。

## 项目结构概览

```
.
├── config.ini              # Agent和知识库配置文件
├── README.md               # 本文档
├── start.sh                # Docker启动脚本
├── ws_server.py            # 后端WebSocket服务器主入口
├── pyproject.toml          # 后端项目与依赖配置
├── frontend/
│   ├── package.json        # 前端项目与依赖配置
│   ├── next.config.ts      # Next.js 配置文件
│   ├── app/                # Next.js App Router 核心目录
│   │   ├── layout.tsx      # 全局布局
│   │   └── page.tsx        # 主页面入口
│   ├── components/         # React UI组件
│   │   ├── home-content.tsx # 主界面核心组件
│   │   └── ...
│   ├── context/
│   │   └── app-context.tsx # 全局状态管理
│   └── hooks/              # 自定义React Hooks
└── src/
    └── boss_agent/         # 后端核心代码
        ├── agents/         # Agent实现
        ├── llm/            # LLM客户端封装
        ├── tools/          # 所有可用工具的实现
        └── ...
