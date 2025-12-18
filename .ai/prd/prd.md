# 1. Title: Minos 隐私合规扫描程序 PRD

<version>1.0.0</version>

## Status: Approved

## Intro

Minos 是一个针对 Android 应用的隐私合规扫描程序，目标是帮助研发与合规团队识别 APK 或源码中可能违反各地隐私法规（如 GDPR、CCPA、LGPD、PIPL 等）的风险，支持在 CI/CD 流程中快速出报告，降低人工审核成本。

## Goals

- 清晰的项目目标：提供一键化的静态/动态隐私合规扫描能力，覆盖常见法规与地区差异。
- 可衡量的结果：扫描报告需包含风险项、法规条款映射与定位信息（文件/组件/域名等）。
- 成功标准：在 CI 中完成 APK/源码扫描并生成报告（HTML+JSON）；无阻断策略，误报率可控。
- 关键 KPI：扫描耗时（PR 级别 < 10 分钟）、规则覆盖率（主要法规条款）、报告可读性与定位精度。

## Features and Requirements

- 功能需求：
  - 支持选择法规或发布地区，自动映射规则集扫描 APK/源码；UI 默认地区多选，提供高级模式手动增删法规，报告标注规则来源（地区映射/手动）。
  - 静态分析：Manifest 权限/导出组件、第三方 SDK、敏感 API/字符串、出网域名、明文密钥。
  - 构建后校验：支持对混淆后的 APK 做静态扫描，核对依赖与配置。
  - 动态扩展：预留接口对接 Frida/mitmproxy（放在后续迭代或 nightly）。
  - 规则文档转换：从“法规参考链接”抓取 HTML/PDF 文档，使用通用框架 + 站点适配器转换为规则 YAML（不使用 LLM）。
- 报告：HTML + JSON 输出，标注风险等级、法规条款、证据定位与建议。
- CI 集成：提供 CLI/容器镜像，支持 PR 阶段快速扫描与发布前深度扫描；stdout 简洁摘要（风险计数、报告路径）；无阻断策略。
- 扫描规则驱动：扫描引擎应从 YAML 规则中读取匹配逻辑（pattern/范围/证据提取等），减少硬编码；保留少量兜底规则但可被 YAML 覆盖/禁用。
- 非功能需求：
  - 扫描速度可配置，支持缓存/并行（PR 级 < 10 分钟）。
  - 规则引擎可扩展，规则以数据驱动（YAML/JSON）管理，易于新增法规映射。
  - 兼容常用 CI（GitHub Actions/GitLab CI 等），无网或受限网络模式下可运行。
- 用户体验需求：
  - 清晰的命令行输出，失败原因易理解；报告链接或工件易获取。
  - 可通过配置文件指定地区/法规、规则开关；无阻断策略，报告为主。
  - 终端与日志文件需输出足够的进度与调试信息，便于排查问题（含阶段进度、规则加载、扫描目标、错误提示等）。
- 集成要求：
  - 支持直接读取 Gradle 构建产物（如 assemble 后的 APK 和相关输出路径）进行扫描。
  - 可读取项目依赖/配置（gradle 文件、AndroidManifest）。
  - CI stdout 输出摘要（风险计数、报告路径）；报告以 HTML+JSON 工件输出。
  - 支持本地直接运行（安装依赖后通过 CLI），同时提供 Docker/OCI 镜像便于 CI 集成。
- 合规要求：
  - 覆盖 GDPR/CCPA/CPRA/LGPD/PIPL 等主流法规基本规则。
  - 支持地区→法规映射与手工追加法规的并集逻辑。

### 可选地区集合（示例，支持多选）

- EU（欧洲经济区）
- US-CA（美国加州）
- US（美国其他州/联邦层面）
- BR（巴西）
- CN（中国内地）
- JP（日本）
- 其他：支持配置扩展（如 KR、AU、UK、IN 等）

### 可选规则/法规集合（示例，支持多选并扩展）

- GDPR（欧盟）
- CCPA/CPRA（美国加州）
- LGPD（巴西）
- PIPL（中国内地）
- 其他：支持导入/扩展的法规规则集（如 PDPA 等），与地区映射组合使用

### 地区与法规映射（默认启用关系，可扩展/覆盖）

| 地区        | 默认法规集                    | 备注                                   |
| ----------- | ---------------------------- | -------------------------------------- |
| EU          | GDPR                         | 可叠加各成员国本地要求（可扩展）       |
| US-CA       | CCPA/CPRA                    | 可叠加 COPPA/GLBA/HIPAA 等（可扩展）   |
| US          | （空）                       | 可按需选择 COPPA/GLBA/HIPAA/州法等     |
| BR          | LGPD                         | -                                      |
| CN          | PIPL                         | 可扩展必要信息范围规定、行标等         |
| JP          | APPI                         | 可叠加本地指南（如 PPC 指南）或行业规制 |
| 其他地区    | 自定义                       | 支持导入/扩展法规规则集                |

说明：地区多选时取法规集并集；用户可在高级模式手动增删法规，最终以用户选择的并集为准。报告需标注每条规则来源（地区映射 / 手动选择）。

### 法规参考链接（官方/权威发布页）

- GDPR：<https://eur-lex.europa.eu/eli/reg/2016/679/oj>
- CCPA/CPRA：<https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5>
- LGPD：<https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/L13709.htm>
- PIPL（个人信息保护法）：<https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm>
- APPI（日本）：<https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/>
- 其他可扩展法规：支持用户自定义添加官方链接（如 PDPA、UK GDPR 等）。

### 法规文档适配范围（约定）

- 语言：默认英文；若页面不提供英文，使用页面默认语言。
- 文档类型：支持 HTML 与 PDF。
- 抽取范围：仅抽取“正文条款”，不包含附件、目录、索引等。
- 覆盖范围：仅支持 PRD “法规参考链接”中列出的法规站点（GDPR/CCPA/CPRA/LGPD/PIPL/APPI）；未知法规/地区的本地文档或在线链接默认不支持，需扩展适配器。

### 规则数据形态与管理

- 规则配置采用 YAML（可导出 JSON），字段包含：rule_id、法规来源（法规/地区）、严重级别、匹配范围（manifest/SDK/API/域名/资源等）、匹配条件（正则/AST/清单节点）、证据提取方式、建议、规则版本。
- 规则集支持版本管理、禁用/覆盖；规则数据驱动，无需改代码即可增改规则。
- 扫描引擎从 YAML 加载匹配逻辑：pattern/范围/证据提取等需要在 YAML 中定义，硬编码仅作兜底且可被禁用/覆盖。

### 法规文档转换输出字段（建议）

- 必填字段：rule_id、regulation、title、clause、description、source_url、version。
- 可选字段：severity（默认 medium）、pattern、evidence、recommendation、confidence（0~1）、issues（字符串数组）。
- 章节拆分：基于条款编号（Article/Section/Chapter 等），优先识别编号与标题；标题缺失时可用条款首句截断补齐。

### 规则获取与同步

- 工具自带预置规则集（随版本发布）；支持从可信规则仓库/制品库拉取指定法规或全集并落地到本地规则目录。
- 支持 CLI/配置触发拉取与更新，包含版本校验与签名校验，支持离线使用本地缓存。
- 本地规则需与官方法规建立映射：每条规则记录所属法规及官方条款 URL；报告中可引用条款链接。
- 支持用户新增/覆盖规则文件及地区映射，无需改代码。
- 规则仓库与分发：规则以 YAML/JSON 打包发布在受控仓库（私有/公开 git 或 OCI 制品库），通过 https/git/oci 拉取；发布提供版本号与完整性校验（SHA256，可选 GPG），CLI（如 rulesync）负责同步/更新；保留旧版本便于回滚，并在文档列出工具版本与规则版本的兼容矩阵。
- 规则更新策略：默认手动更新（CLI rulesync），可选“检查新版本”提示，不自动覆盖；保留上一个版本便于回滚；文档列出工具版本与规则版本的兼容范围。
- 本地缓存/离线：本地缓存目录（如 ~/.minos/rules），记录版本和签名；失效策略=显式更新或手动清理；无网时使用最新缓存。
- 在线规则同步：rulesync 支持通过命令行指定法规集（如 `--regulations gdpr --regulations ccpa`），默认同步“法规参考链接”中列出的全部法规（GDPR、CCPA/CPRA、LGPD、PIPL、APPI 等）。
- 法规文档转换：内置“通用框架 + 站点适配器”将法规链接的 HTML/PDF 转换为规则 YAML，不依赖 LLM；站点结构变更需更新适配器。
- 缓存与落地：不同法规集在本地以隔离的规则集存储和命名（`~/.minos/rules/<regulation>`），互不覆盖，可并行存在，仅保留最新版本（覆盖旧版本）。
- 适配器扩展：适配器遵循开闭原则，通过接口与注册发现机制扩展站点支持，新增站点无需修改通用框架核心逻辑。
- **首版约束**：仅提供单一入口 `rulesync` 执行“在线拉取（PRD 白名单）→转换→写入缓存/激活”全流程，不对外暴露独立转换命令；默认禁止本地文件/自定义源。
- `rulesync --from-url --regulation <reg> [--version <ver>]`：URL 可省略，若未提供则按法规映射自动填充 PRD 默认链接；`--version` 可选（不填使用默认标识）。
- PRD 默认 URL 映射：gdpr→<https://eur-lex.europa.eu/eli/reg/2016/679/oj>；ccpa/cpra→<https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5>；lgpd→<https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/L13709.htm>；pipl→<https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm>；appi→<https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/>。未收录法规且未提供 URL 时直接报错。
- 开关（仅受控环境）：`--allow-local-sources` 放开本地文件/导入 YAML，`--allow-custom-sources` 放开非白名单在线源；默认关闭并给出警示。

### 报告结构（HTML/JSON 同步字段）

- 元信息：扫描目标、时间、工具版本、规则集版本、输入参数。
- 结果列表：rule_id、法规来源、地区来源、严重级别、命中文件/组件/行、片段/证据、建议。
- 统计摘要：风险计数分级、地区/法规分布；报告内可跳转到命中位置或片段。
- 报告 schema：定义 HTML/JSON 公共字段名/类型/必填性（meta/findings/stats）；在文档提供 JSON schema 便于前端/CI 消费一致。

### 日志与可观测性

- 日志级别：info/debug/error。默认 info，支持开启 debug。
- 必出 info 节点：配置解析、规则加载数、目标列表、阶段进度（manifest/SDK/API/APK 校验）、耗时摘要、输出路径；error 输出失败原因与上下文；debug 输出匹配细节样例（可选）。
- 日志输出：stdout 输出摘要；详细日志写入文件（如 output/logs/scan.log），支持 log-level；可选大小限制/轮转（如 10MB×3）。

### CI 运行参数（CLI 建议）

- --regions、--regulations、--ruleset-dir、--enable-rule/--disable-rule
- --mode (source|apk|both)、--output-dir、--format (html,json,both)
- --timeout、--threads、--log-level
- --manifest/--apk-path 覆盖、--config 配置文件路径
- 缺少输入时给出清晰错误；支持多 APK/多变体列表输入；默认扫描 release 变体，可通过参数指定；源码+APK 同时提供时，先源码再 APK，结果并集合并。

### 扫描范围与深度

- 源码：Kotlin/Java、资源/配置（AndroidManifest、res/xml、network_security_config、混入的 JSON/YAML）。
- APK：manifest、dex（反编译/字符串/常量池）、资源、assets、so 名称/导出符号（轻量）；可选传 mapping.txt 提升混淆后定位。
- 多变体/flavor：通过 CLI/配置指定目标产物路径或变体名，默认扫描 release APK。

### 性能与并行

- 默认并行度=min(核心数, 8)（可配置 --threads）；启用缓存（规则编译缓存、依赖签名缓存、域名解析缓存）。
- 支持阶段/全局超时（--timeout）；大文件/大 dex 分块处理；可通过参数关闭缓存；对内存占用大的阶段给出上限或提示。

### 兼容性

- 最低支持：JDK 11、Android Gradle Plugin 7.x+。
- 若使用 Python 编排：Python 3.10+；工具依赖（如 jadx/androguard）版本需列明。若需兼容 AGP 6.x/4.x，标记为“尽力支持”并提供测试样例。

### 扩展接口（预留）

- 定义动态检测插件接口：插件元数据、支持的钩子（API/流量）、输出结果格式与合并方式；首版仅声明接口，不实现。

### 验收标准（示例）

- 提供 2-3 个示例 APK（含特定权限、追踪 SDK、可疑域名）和源码样本（仓库内置或提供下载链接），附预期命中清单。
- 预期命中规则清单与报告截图/JSON 片段；CI 样例 workflow 成功跑通并生成工件。

### 规则 DSL 示例（用于校准）

- 示例条目包含：rule_id、法规条款 URL、严重级别、匹配条件（如 Manifest 权限/SDK 标识/域名正则）、证据提取、建议，格式为 YAML（可导出 JSON）。

### 安全与隐私

- 默认不上传任何扫描数据；本地临时文件存储在工作目录/缓存目录，任务结束可选清理；如需保留，提供配置开关。

## Epic List

### Epic-1: 规则供应与版本管理

### Epic-2: 地区/法规映射与配置

### Epic-3: 静态扫描与规则引擎

### Epic-4: CI 集成与报告输出

### Epic-N: 动态流量与运行时扩展（后续迭代）

## Epic 1: Story List

- Story 1: 规则同步与版本管理（rulesync）  
  Status:  
  Requirements:  
  - 从受控仓库拉取/校验规则包（版本与签名）  
  - 支持本地缓存与回滚；CLI 触发更新与检查版本  
  - 记录规则来源和版本，供扫描与报告引用  
  
- Story 2: 法规文档抓取与转换（通用框架 + 站点适配器）  
  Status:  
  Requirements:  
  - 通用框架：下载/清洗/分段/生成规则 YAML  
  - 站点适配器：GDPR/CCPA/CPRA/LGPD/PIPL/APPI  
  - 不使用 LLM，解析失败需输出定位信息  

## Epic 2: Story List

- Story 1: 地区→法规映射配置  
  Status:  
  Requirements:  
  - 维护地区与法规规则集的映射表  
  - 支持用户手动追加或裁剪法规集  

## Epic 3: Story List

- Story 1: Manifest 与权限扫描  
  Status:  
  Requirements:  
  - 解析 AndroidManifest 权限/导出组件  
  - 规则匹配（必要性、敏感权限）并输出风险  

- Story 2: SDK 与敏感 API 扫描  
  Status:  
  Requirements:  
  - 识别第三方 SDK/广告追踪库  
  - 扫描敏感 API/字符串（ID、密钥、域名）  

## Epic 4: Story List

- Story 1: CLI/容器化与报告  
  Status:  
  Requirements:  
  - 提供命令行与 Docker 镜像  
  - 输出 JSON/HTML 报告，含条款映射与证据  

- Story 2: 容器化交付与发布  
  Status:  
  Requirements:  
  - 提供可构建的 Docker/OCI 镜像（Dockerfile、入口脚本）  
  - 支持规则缓存挂载与无网运行；输出路径与本地一致  
  - 提供构建/运行示例与 smoke 验收（报告生成、退出码/摘要校验）  

- Story 3: CI 工作流示例  
  Status:  
  Requirements:  
  - 集成 GitHub Actions/GitLab CI 样例  
  - 支持 PR 级快速扫描与发布前深度扫描  

## Epic-N: Story List

- Story 1: 动态流量与运行时检测（预研）  
  Status:  
  Requirements:  
  - 预研 Frida/mitmproxy 集成方案
  - 定义可插拔的动态检测接口

## Change Log

| Change | Story ID | Description |
| --- | --- | --- |
| 法规文档转换方案 | story-10 | 增加通用框架 + 站点适配器的在线法规文档转换（不使用 LLM） |
| 适配范围与输出字段 | story-10 | 明确语言/文档类型/抽取范围与转换输出字段建议 |
