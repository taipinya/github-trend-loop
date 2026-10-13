# GitHub 趋势项目观察 - 2026-10-13

## 本次结论

本次 Top 3 呈现出三条截然不同但都极具“系统级工程”气质的技术路线：一是把 LLM Agent 与逆向工程工具链（Ghidra/Hopper/MCP）缝合起来的 REA；二是用纯 Rust 从零重写 Photoshop 级图像编辑器的 PhotoCraft；三是尝试把 PS5 可执行文件重链接到 Linux/Windows 原生格式、而非走模拟器路线的 AnyPS5。三者共同点是：都在挑战“被少数商业闭源工具长期垄断”的领域（逆向工具、图像编辑、主机游戏运行时），并且都选择用现代语言或现代 Agent 范式重新实现底层能力。

需要特别说明：本次运行 baseline 为 False，但输入数据中并未提供 3 天增量对比所需的完整历史窗口，因此**本次没有 3 天增量数据，下一次运行才有 delta**。下文中的 delta_stars / delta_forks / delta_subscribers 字段按输入原样引用，但读者应将其理解为“本次采集窗口内的增量”，而非严格的 3 日增量。

## 报告重点

- REA 的 stars 量级（17.8 万）与 delta_stars（12.3 万）在本次数据中异常突出，topic 覆盖 agent-skills、mcp、ghidra、decompiler、ctf，说明“Agent + 逆向”是一个正在被大量关注的方向。
- PhotoCraft 用“clean-room reimplementation of Adobe Photoshop, rebuilt in pure Rust”定位自己，Apache-2.0 许可，适合研究大型 GUI/图像处理系统的 Rust 工程化。
- AnyPS5 明确声明“No emulation or separate runtime process”，走 relinker + 系统 prx 库动态链接路线，GPL-2.0，工程复杂度高，属于典型的“系统编程 + 图形栈”交叉项目。

## Top 3 项目

### 1. morluto/rea
- URL：https://github.com/morluto/rea

#### 项目简介
REA 属于“AI Agent 驱动的逆向工程工具链”领域。从 README 摘要看，它把自己定位为 “One MCP for reverse engineering across binaries, applications, and runtime behavior”，即通过 Model Context Protocol（MCP）把 LLM Agent 与逆向分析能力连接起来。可能的技术原理是：以 MCP 作为 Agent 与工具之间的协议层，把二进制分析、反汇编/反编译（topic 中出现 ghidra、hopper、decompiler、disassembler）、静态分析（static-analysis）等能力封装成 Agent 可调用的 skill，从而让 Agent 完成“从应用行为一路下探到原生二进制”的分析任务。语言为 TypeScript，说明其主体更偏向 CLI/插件/协议编排层，而非底层反汇编引擎本身。

#### 为什么值得关注
- 体量信号极强：stars 178346、forks 42934、subscribers 586，delta_stars 123059、delta_forks 32347、delta_subscribers 407，在本次 Top 3 中热度最高。
- topic 组合非常有信息量：agent-skills、ai-agents、claude-code、codex、mcp、model-context-protocol 说明它紧跟 Agent 生态；binary-analysis、decompiler、ghidra、hopper、ctf、reverse-engineering 说明它扎根传统逆向工具链。这种“新 Agent 范式 × 老逆向领域”的交叉，正是当前值得研究的方向。
- 最近 push 时间 2026-10-13，open_issues 562，说明项目处于高频迭代且社区讨论活跃。
- README 结构上提供多语言版本（英/简中/繁中/日/韩/土耳其/俄/越/泰/德/西/法/乌克兰/波兰/葡/阿/波斯/印尼/意），这种国际化 README 布局通常意味着项目在主动扩大贡献者与用户范围。
- MIT 许可证对二次开发和课程项目友好。

#### README 摘要
中文说明：README 采用居中排版，顶部是多语言切换链接，主标题为 “REA: Reverse Engineer Anything”，副标题强调 “One MCP for reverse engineering across binaries, applications, and runtime behavior”。整体结构像是“定位声明 + 能力概览 + 使用/集成入口”的典型开源项目 README，重点在讲清楚它能覆盖哪些逆向对象（二进制、应用、运行时行为）以及它如何通过 MCP 与 Agent 协作。

摘要线索：
- “One MCP for reverse engineering across binaries, applications, and runtime behavior.”
- “See a feature you like. Understand how it works, down to the b…”（摘要被截断，但可推断是在讲“看到某个功能，就能理解它到底怎么实现”的逆向目标）
- 多语言 README 文件命名规范（README_zh.md、README_ja.md 等），说明文档维护有体系。

#### 具体怎么用
建议从三条线入手理解：
1. **协议层**：先看 MCP 相关部分，理解 Agent 与逆向工具之间是如何定义工具描述、调用参数和返回结果的。这是理解“Agent 如何驱动逆向”的关键。
2. **工具封装层**：关注 topic 中 ghidra、hopper、decompiler、disassembler 对应的模块，看它是把已有逆向工具包装成 skill，还是自己实现了部分分析逻辑。
3. **Agent 编排层**：结合 agent-skills、claude-code、codex 等 topic，观察它如何把“分析目标 → 选择工具 → 执行 → 汇总结论”串成一条可复用的分析流水线。
不建议一上来就装环境，先读 README 的能力边界和 MCP 接口设计，再决定是否深入某个具体逆向后端。

#### 适合谁关注
- 对逆向工程、CTF、二进制安全感兴趣，同时想了解 Agent 如何介入传统安全工具链的学生。
- 想做“LLM + 工具调用”课程设计或毕业设计的同学，REA 是一个现成的复杂工具编排案例。
- 研究型工程实践者：可以研究 MCP 在专业垂直领域（而非通用聊天）中的协议设计取舍。

#### 应用场景示例
- 安全研究中的样本行为分析：让 Agent 先观察应用层行为，再逐层下探到二进制实现，辅助分析恶意样本或闭源软件。
- CTF 与漏洞挖掘教学：把反汇编/反编译工具通过 MCP 暴露给 Agent，用于自动化初筛可疑函数。
- 软件供应链审计：对第三方二进制依赖做静态分析，辅助判断是否存在可疑行为。
- 逆向工程课程实验：以 REA 为参照，设计一个“Agent 调用反汇编器完成指定分析任务”的小型实验。

#### 风险或局限
- 数据中 stars/delta 量级异常高，与 forks/subscribers 比例不完全协调，读者应保持审慎，建议自行核对仓库真实活跃度。
- open_issues 562，说明问题积压较多，维护压力可能较大。
- 逆向工程本身涉及法律与合规边界，用于闭源软件分析时需注意许可与当地法规。
- 依赖 Ghidra/Hopper 等外部工具，工程环境成本不低；MCP 生态仍在快速变化，接口可能不稳定。
- README 摘要被截断，具体能力边界、支持的分析粒度、是否支持动态调试等信息不足，需要进一步阅读完整文档确认。

### 2. storytold/photocraft
- URL：https://github.com/storytold/photocraft

#### 项目简介
PhotoCraft 属于“图像编辑软件 / 创意工具”领域，定位是 Adobe Photoshop 的开源 clean-room 重实现，且完全用纯 Rust 从零编写。README 摘要明确列出其能力范围：图层（Layers）、蒙版（Masks）、调整图层（Adjustment layers）、图层样式（Layer styles）、文字（Type）、矢量（Vectors）、画笔（Brushes）以及真实 PSD 文件支持。技术原理上，它需要处理图像合成管线、图层混合模式、颜色管理、矢量渲染、字体排版，以及 PSD 这一复杂二进制格式的解析与写回。语言为 Rust，说明项目在追求内存安全与原生性能，同时避免依赖现有图像编辑框架。

#### 为什么值得关注
- stars 55027、forks 9227、subscribers 229，delta_stars 17575、delta_forks 3837、delta_subscribers 89，热度稳定且社区参与度高。
- topic 为 art、image-editing、image-editing-software、image-editor、images、photo-editing、rust，方向清晰，几乎没有噪音 topic。
- README 中强调 “100% Rust” 徽章、“open source, offline, and yours”，说明其价值主张是“离线、开源、可拥有”，这对关注数据主权和本地化工具的人有吸引力。
- 最近 push 2026-10-13，open_issues 1316，说明功能请求和缺陷讨论都非常活跃，项目处于快速演进期。
- Apache-2.0 许可证，对个人项目和课程项目都较友好。
- 从工程角度，PSD 解析 + 图层合成 + 矢量/文字渲染是一个极佳的“大型 Rust 应用架构”研究样本。

#### README 摘要
中文说明：README 采用居中品牌化排版，顶部是 ArtCraft 品牌 logo，主标题 PhotoCraft，副标题明确写出 “Image editing; an open-source, clean-room reimplementation of Adobe Photoshop, rebuilt in pure Rust.”，并列出核心功能关键词：Layers、masks、adjustment layers、layer styles、type、vectors、brushes、real PSD files。整体结构偏向“产品定位 + 功能清单 + 品牌展示”，并配有 “100% Rust” 徽章，强调技术选型。

摘要线索：
- “Layers, masks, adjustment layers, layer styles, type, vectors, brushes and real PSD files, in a native app written entirely in Rust.”
- “Open source, offline, and yours.”
- 徽章 “100% Rust”，说明项目把纯 Rust 实现当作核心卖点。

#### 具体怎么用
建议从四个模块切入理解：
1. **PSD 解析/序列化**：这是最能体现工程难度的部分，研究它如何用 Rust 处理 Photoshop 的复杂二进制结构。
2. **图层合成管线**：关注图层、蒙版、调整图层、图层样式之间的组合顺序与混合模式实现。
3. **渲染层**：文字、矢量、画笔分别涉及字体排版、路径渲染和笔刷引擎，可以看它如何组织这些相对独立的子系统。
4. **应用架构**：作为一个原生 GUI 应用，它的模块划分、状态管理和撤销/重做机制对做桌面软件课程设计很有参考价值。
不建议从安装开始，先读 README 的功能清单和 docs/brand 等目录结构，判断哪个子系统最值得深入。

#### 适合谁关注
- 想研究“用 Rust 写大型 GUI/图像处理应用”的计算机专业学生。
- 对图像编辑、图形学、文件格式解析感兴趣的个人开发者。
- 想做课程设计（如简易图层编辑器、PSD 解析器）但希望参考一个真实大型项目架构的实践者。

#### 应用场景示例
- 本地化图像处理工作流：在离线环境中完成图层化编辑，避免把素材上传到云端。
- 设计资产批处理：基于 PSD 解析能力，对设计稿做自动化检查或批量导出。
- 图像编辑教学工具：作为开源替代，用于讲解图层、蒙版、混合模式等概念。
- 图形文件格式研究：以 PSD 为案例，研究复杂二进制格式的解析与写回。
- 桌面软件架构实验：借鉴其 Rust 模块划分，设计自己的原生创意工具。

#### 风险或局限
- open_issues 1316，说明功能缺口和缺陷较多，距离“可替代 Photoshop”仍有明显距离。
- 作为 clean-room 重实现，法律与专利边界需要项目自身持续关注，使用者用于商业场景前应自行评估。
- 纯 Rust 从零实现意味着大量底层轮子需要自研，工程复杂度高，个人贡献门槛不低。
- README 摘要未给出性能数据、平台支持矩阵和 PSD 兼容性范围，实际成熟度需进一步验证。
- 数据中 stars/forks 量级较高，但 subscribers 相对少，说明“围观者”多、“深度参与者”可能有限。

### 3. boykopovar/AnyPS5
- URL：https://github.com/boykopovar/AnyPS5

#### 项目简介
AnyPS5 属于“主机可执行文件移植 / 系统级重链接”领域，目标是把 PS5 可执行文件自动移植到 Linux 和 Windows。README 明确说明它包含一个 relinker（core/relinker），把可执行文件转换为目标系统的原生格式，并提供适合动态链接的系统 prx 库实现（core/libs/prx）。关键点是它声明 “No emulation or separate runtime process”，即不走模拟器路线，而是尝试让目标系统原生加载和链接。topic 中出现 spir-v、vulkan，说明图形栈方面可能涉及着色器转换与 Vulkan 渲染路径。语言为 C++。

#### 为什么值得关注
- stars 33568、forks 2901、subscribers 334，delta_stars 10069、delta_forks 962、delta_subscribers 66，热度可观且订阅者比例相对健康。
- topic 组合 anyps5、dynamic-library、game-porting、ps5、ps5-tools、spir-v、vulkan，指向非常明确的“主机移植 + 图形栈”方向。
- README 结构清晰，直接给出 Usage、Build instructions、Architecture、Technical debt、Conventions、Contributing 等文档入口，说明项目在工程规范上有意识投入。
- 最近 push 2026-10-13，open_issues 647，社区活跃但问题也不少。
- GPL-2.0 许可证，对衍生作品有传染性，使用前需注意。
- “No emulation” 这一技术路线本身就很有讨论价值：它绕开了模拟器的性能与兼容性难题，但换来了重链接与 ABI 适配的复杂度。

#### README 摘要
中文说明：README 结构简洁，先给 About 说明项目定位，然后列出核心组件（relinker、system prx libraries），并给出 Usage、Build、Architecture、TechnicalDebt、Conventions、Contributing 等文档链接。还包含 Status 徽章（libraries、shaders），说明项目用徽章展示库和着色器的支持进度。整体是一份偏工程导向的 README，强调架构文档和技术债透明度。

摘要线索：
- “Tool for automatic executables porting to Linux and Windows.”
- “Includes a relinker that converts executable to the target system's native format and implementations of system prx libraries suitable for dynamic linking.”
- “No emulation or separate runtime process.”
- 文档入口：docs/user/USAGE.md、docs/dev/BUILD.md、docs/dev/ARCHITECTURE.md、docs/dev/TechnicalDebt.md、docs/dev/CONVENTIONS.md。

#### 具体怎么用
建议从三条线理解：
1. **relinker 模块（core/relinker）**：这是项目核心，研究它如何把 PS5 可执行格式转换为 Linux/Windows 原生格式，涉及二进制重写、符号解析、重定位等系统编程知识。
2. **系统 prx 库（core/libs/prx）**：看它如何用动态库实现原本由 PS5 系统提供的接口，这是“不模拟、直接链接”路线的关键。
3. **图形栈**：结合 spir-v、vulkan topic，研究着色器转换和渲染后端适配思路。
另外，docs/dev/ARCHITECTURE.md 和 TechnicalDebt.md 是理解项目边界与难点的好材料，建议优先阅读。

#### 适合谁关注
- 对系统编程、二进制重链接、动态链接、ABI 适配感兴趣的高年级本科生或研究生。
- 想研究“非模拟器路线的主机移植”这一技术方向的工程实践者。
- 对 Vulkan/SPIR-V 图形栈和着色器转换感兴趣的同学。

#### 应用场景示例
- 主机游戏移植研究：探索把主机平台可执行文件适配到 PC 平台的技术路径。
- 二进制重链接工具链实验：以 relinker 为案例，研究可执行格式转换与重定位。
- 图形栈适配研究：研究 SPIR-V 着色器在目标平台上的转换与运行。
- 系统编程课程设计：围绕动态库实现、符号解析、ABI 兼容性设计实验。
- 兼容层架构对比研究：与模拟器路线对比，分析两种方案在性能与复杂度上的取舍。

#### 风险或局限
- 主机移植涉及版权、许可和平台条款，实际使用需高度注意法律风险。
- GPL-2.0 许可证对衍生作品有传染性，商业或闭源场景需谨慎评估。
- 项目自述包含 TechnicalDebt 文档，说明技术债是公开承认的问题，生产成熟度有限。
- open_issues 647，且涉及底层二进制与图形栈，调试和贡献门槛高。
- README 摘要未给出支持的游戏/可执行文件范围、成功率或性能数据，实际可用性需进一步验证。
- 依赖 C++ 工具链和 Vulkan/SPIR-V 相关环境，工程复杂度与依赖成本较高。

## 数据限制说明

- GitHub 官方并不直接提供全站 3 天增长榜。
- 本报告中的新增 Star、新增订阅、新增 Fork 来自本项目保存的本地 snapshot 对比。
- 第一次运行只是 baseline，第二次运行开始才有更有意义的 3 天增量。
- GitHub Trending 来源于 HTML 页面抓取，可能受页面结构变化影响。
- README 信息可能不完整，具体使用效果需要人工进一步试用确认。
