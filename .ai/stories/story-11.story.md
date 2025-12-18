# Epic-1 - Story-11
# 规则同步单一入口与默认 URL 映射

**As a** 规则发布/维护者  
**I want** 通过单一 `rulesync` 命令完成法规链接→规则缓存的全流程，并按法规自动填充默认官方链接  
**so that** 首版规则同步更简单安全，默认只支持 PRD 白名单且避免本地/自定义源误用

## Status

Draft

## Context

- 首版约束：默认仅支持 PRD “法规参考链接”白名单域名；不暴露独立转换命令，规则同步只有 `rulesync`。  
- 需求变更：`rulesync --from-url` 支持按 regulation 自动填充官方链接；URL 可省略，version 参数可选。  
- 默认禁用本地文件/导入 YAML/非白名单源，仅在受控环境下通过显式开关放开。

## Estimation

Story Points: 2

## Tasks

1. - [x] 设计测试用例（TDD 先行）  
   - [x] 1.1 场景覆盖：省略 URL 自动填充成功（reg=gdpr 等）；未映射法规报错；非白名单 URL 拒绝；本地/自定义源未开关时拒绝；开启 `--allow-local-sources`/`--allow-custom-sources` 后成功；version 未传时默认值写入校验；缓存落地与激活检查；参数值大小写混用仍能匹配（不区分大小写）。  
   - [x] 1.2 断言：stdout/stderr 文案、退出码；metadata（version/source_url/installed_at/active）；缓存目录结构；白名单/开关警示信息；参数值大小写归一处理验证。  

2. - [x] 实现测试用例  
   - [x] 2.1 根据 1.x 设计编写并落地自动化测试，覆盖成功/失败/开关/默认版本场景。  

3. - [ ] 功能实现  
   - [x] 3.1 CLI：`rulesync --from-url --regulation <reg> [--version <ver>] [--allow-local-sources] [--allow-custom-sources]`，参数可选且值不区分大小写；未给 URL 按映射填充（默认 PRD 白名单），未给 regulation 默认同步 PRD 列出的全部法规。  
   - [ ] 3.2 流程：下载→转换→写入缓存/metadata→激活；内部调用转换模块但不对外暴露独立命令；version 可选默认值写入缓存与 metadata 一致。  

4. - [ ] 文档与验收  
   - [ ] 4.1 运行并通过 1.x 的测试用例，验证失败路径与警示文案符合设计。  
   - [ ] 4.2 更新 README / CI / 容器文档：仅展示 `rulesync --from-url` 单步用法（URL 可省略），说明默认限制、映射表、开关行为。  
   - [ ] 4.3 更新 PRD/变更记录：记录默认 URL 映射、version 可选、单一入口与禁用本地/自定义源的约束。  
   - [ ] 4.4 验收用例：最小命令成功、白名单校验、开关场景、缓存落地检查。

## Constraints

- 默认仅支持 PRD 白名单域名（GDPR/CCPA-CPRA/LGPD/PIPL/APPI 对应官方链接）；未映射法规且未提供 URL 直接报错。  
- 本地文件/导入 YAML/非白名单源默认禁用；需显式 `--allow-local-sources` 或 `--allow-custom-sources` 才放开，并给出警示。  
- 对外只暴露 `rulesync` 单一入口；转换模块为内部实现，不单独使用。  
- `--version` 可选，未提供时使用默认版本标识，但需写入 metadata 与缓存路径一致。  
- 不使用 LLM。

## Data Models / Schema

- 缓存结构：`~/.minos/rules/<regulation>/<version>/rules.yaml + metadata.json`；metadata 记录 version/source_url/installed_at/active。  
- 默认 URL 映射来自 PRD 法规参考链接；白名单校验按域名匹配。

## Dev Notes

- 需确保旧的本地导入路径在未开启开关时直接返回明确错误，避免默默成功。  
- 默认版本标识可考虑 `latest` 或日期戳（需在任务中确定并统一）。  
- 错误提示需指明开启开关的后果（仅受控环境）。  
- 内部转换仍复用现有适配器，但不在文档对外暴露。

## Test Plan

- 缺省 URL + regulation=gdpr：自动填充 GDPR 链接，退出码=0，metadata.source_url=GDPR URL，版本写入默认值，缓存落地并激活。  
- 缺省 regulation（同步全部）：按 PRD 链接列表逐个同步，生成 gdpr/ccpa/lgpd/pipl/appi 缓存目录，全部退出码=0。  
- 未映射法规 reg=unknown 且无 URL：退出码非零，stderr 提示需自定义源，metadata/缓存不生成。  
- 非白名单 URL：退出码非零，stderr 提示需 `--allow-custom-sources`，无缓存落地。  
- 本地文件（file:// 或路径）无开关：退出码非零，stderr 提示需 `--allow-local-sources`。  
- 开启 `--allow-local-sources` 导入本地规则包：退出码=0，metadata.source_url 标记为本地，缓存落地并激活。  
- 开启 `--allow-custom-sources` 同步非白名单 URL：退出码=0，metadata.source_url=自定义 URL，缓存落地并激活。  
- 参数值大小写混用（如 `--regulation GDPR`）：仍匹配映射并成功，缓存路径使用小写规约。  

### Assertions（对应 1.2）
- 退出码：成功场景=0，拒绝/未映射/未开关等错误场景非零；stderr 包含原因关键词（非白名单/需 allow-custom-sources、本地需 allow-local-sources、未映射需自定义源）。  
- stdout：成功时输出同步的法规列表与缓存路径，regulation 名统一小写；失败时不输出成功摘要。  
- metadata：成功时包含 version（默认值或用户值）、source_url（填充/用户/本地标记）、installed_at（ISO8601）、active=true；失败场景不生成 metadata。  
- 缓存目录：成功时 `~/.minos/rules/<reg>/<ver>/rules.yaml` 存在且 <reg> 为小写；失败场景不创建目录/文件。  
- 大小写不敏感：输入 `--regulation GDPR`、`--version V1` 仍按小写落地路径与 metadata，且匹配默认 URL。  
