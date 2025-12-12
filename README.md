<<<<<<< HEAD
# Multi-Agent Code Generation System

## 1. 概述

本项目是一个多代理协作系统，旨在从自然语言任务描述开始，自主完成整个软件开发项目。它利用大语言模型（LLM）来理解需求、规划任务、生成代码，并通过一个复杂的测试与修复循环进行自我纠错。

该系统在构建时以稳健性和可靠性为核心，其独特的“Test-Driven Fix”（测试驱动修复）循环确保了生成的代码不仅语法正确，而且功能健全、可直接运行。

## 2. 架构

系统由一个中央控制器 `Orchestrator` 协调的几个专业化代理组成：

*   **`Planner Agent`**: 将高层目标分解为一系列具体的、可执行的任务。
*   **`Coder Agent`**: 为每个任务生成代码。它采用“两阶段流程”（骨架 -> 完整实现）来处理复杂文件，并避免 LLM 输出被截断的问题。
*   **`Test Agent`**: 作为自我纠错机制的核心。它对生成的代码运行测试，包括：
    *   **语法编译**: 使用 `py_compile` 检查语法错误。
    *   **运行时执行**: 运行脚本以捕捉像 `ImportError` 这样的运行时错误。
    *   **功能断言**: 验证代码是否产生预期的输出或产物（例如，检查 `stdout` 中的成功消息或特定文件的创建）。
*   **`Fixer Agent`**: 从 `Test Agent` 获取错误日志，并指示 LLM 修复代码。它被特别提示去处理常见的错误，如 `ImportError`、`SyntaxError` 和“静默失败”（例如，脚本运行了但什么也没做）。
*   **`Orchestrator`**: 管理整个工作流程，在“生成 -> 测试 -> 修复”的循环中协调各个代理，以确保最终产出是一个完整且功能正常的项目。

## 3. 核心功能

*   **Test-Driven Fix Cycle**: 系统不仅仅是验证代码，而是主动对其进行测试。如果测试失败，错误会反馈给 `Fixer` Agent，从而创建一个强大的自愈循环，可以解决语法和运行时错误。
*   **两阶段生成**: 为了处理长而复杂的文件，`Coder` Agent 首先生成一个最小化的、可运行的文件骨架。在骨架被验证通过后，它才会继续填充完整的实现。这极大地提高了生成大型代码库的可靠性。
*   **纯代码生成**: 系统的架构设计让 LLM 只生成纯代码，而不是 JSON。所有数据结构都由 Python 代码负责封装，这从根本上消除了由 LLM 生成不规范 JSON 导致的解析错误（如 `Unterminated string`, `Expecting ',' delimiter` 等）。
*   **安全 Shell 执行**: `Test` Agent 可以运行命令，但只允许严格白名单上的命令（例如 `py`, `pip`, `mkdir`）。这可以防止 LLM 执行像 `rm` 或 `curl` 这样有潜在风险的命令。
*   **隔离的输出**: 所有生成的项目文件都放置在一个独立的 `project/` 目录中（可通过 `local.env` 中的 `OUTPUT_DIR` 配置），保持了代理自身源代码的整洁。

## 4. 安装与配置

**先决条件**:
*   Python 3.10+

**步骤**:

1.  **克隆仓库**:
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **创建虚拟环境并安装依赖**:
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate
    
    # macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    
    # 安装依赖
    pip install -r requirements.txt
    ```

3.  **配置你的 LLM API Key**:
    *   在项目根目录下创建一个名为 `local.env` 的文件。
    *   添加你的 LLM 提供商的配置。本系统与任何兼容 OpenAI 的 API 都兼容。

    **示例：Qwen (DashScope):**
    ```env
    LLM_PROVIDER=qwen
    LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode
    LLM_MODEL=qwen-plus
    LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    
    # 推荐配置以保证稳定性
    LLM_TEMPERATURE=0.1
    LLM_MAX_TOKENS=8192
    
    # 运行时设置
    OUTPUT_DIR=project
    ALLOW_SHELL=true
    ```

    **示例：DeepSeek:**
    ```env
    LLM_PROVIDER=deepseek
    LLM_BASE_URL=https://api.deepseek.com
    LLM_MODEL=deepseek-chat
    LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    
    # 推荐配置以保证稳定性
    LLM_TEMPERATURE=0.1
    LLM_MAX_TOKENS=8192
    
    # 运行时设置
    OUTPUT_DIR=project
    ALLOW_SHELL=true
    ```

## 5. 如何运行

本系统设计为通过命令行运行，其强大的 `--phased --auto-fix` 模式能够处理整个代码生成和自我纠错的过程。

**推荐执行方式:**

1.  **运行自动生成与修复流程**:
    ```bash
    py -3.12 -m src.main --phased --auto-fix
    ```
    *   `--phased`: 此标志启用稳健的、多阶段的生成计划（骨架 -> JS 逻辑 -> 数据获取 -> 构建），该计划已在 `Orchestrator` 中硬编码以实现最高可靠性。
    *   `--auto-fix`: 此标志激活“Test-Driven Fix”循环。在每个步骤之后，`Test` Agent 将验证生成的代码，如果发现任何问题，`Fixer` Agent 将尝试修复它们。

2.  **手动运行最终的构建脚本**:
    *   `--auto-fix` 流程会生成并修复 Python 脚本，但构建网站的最后一步需要手动运行。
    ```bash
    py -3.12 project/arxiv_cs_daily/src/build_site.py
    ```
    *   你应该能看到表明构建过程正在运行并成功完成的输出。

3.  **查看生成的网站**:
    *   在你的浏览器中打开 `project/arxiv_cs_daily/index.html` 文件，即可看到最终的、功能齐全的网站。

这个过程将在 `project/arxiv_cs_daily` 目录中创建一个完整、可运行且功能正确的 Web 应用程序，完全满足测试用例的所有要求。
=======
# coding_agent
>>>>>>> a287e076d4eb3beeee590de58fec0c4e78e298e6
