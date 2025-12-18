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

1. 需求与设计  
   - [ ] 1.1 梳理 CLI 接口：`rulesync --from-url --regulation <reg> [--version <ver>] [--allow-local-sources] [--allow-custom-sources]`，无 URL 时按映射填充；version 可选（默认值策略）。  
   - [ ] 1.2 设计 regulation→默认 URL 映射（来源 PRD）与白名单校验策略，未映射/非白名单时的错误提示文案。  
   - [ ] 1.3 设计开关行为与警示信息：本地文件、导入 YAML、非白名单源仅在显式开关下启用。
2. 实现与测试  
   - [ ] 2.1 实现 CLI 流程：单步完成下载→转换→写入缓存/激活；内部调用转换模块但不对外暴露独立命令。  
   - [ ] 2.2 实现默认 URL 自动填充与白名单校验；version 默认值与覆盖写入 metadata。  
   - [ ] 2.3 测试覆盖：  
        - 默认成功路径（reg=gdpr 等，省略 URL）  
        - 未映射法规报错  
        - 非白名单 URL 拒绝  
        - 本地/自定义源在未开启开关时拒绝，在开启时成功  
        - version 未传时默认值写入校验  
        - 规则缓存落地与激活验证
3. 文档与发布  
   - [ ] 3.1 更新 README / CI / 容器文档：仅展示 `rulesync --from-url` 单步用法（URL 可省略），说明默认限制与开关。  
   - [ ] 3.2 更新 PRD/变更记录：记录默认 URL 映射、version 可选、仅单一入口的约束。  
   - [ ] 3.3 验收用例：最小命令成功、白名单校验、开关场景、缓存落地检查。

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
