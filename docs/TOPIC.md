# 改题依据

核对日期：2026-09-23。

## 选择：官方解析器一致性回归与修复

需求来自 [Community-Tasks #142](https://github.com/moonbit-community/Community-Tasks/issues/142)，由 Yoorkin 于 2025-12-09 提出，核查时为 open、无 assignee、无评论。任务要求参考官方 parser 的贡献指南，提供问题报告、回归测试或修复 PR。

上游 [moonbitlang/parser](https://github.com/moonbitlang/parser) 是 MoonBit 自身的 lexer / AST / parser 实现，不是假设存在的领域用户。仓库仍在维护，本次锁定提交 `a01fd77e599c12cf9a2182df3456990e74f53ced`（模块 0.4.0）。新增工作必须以该基线之上的测试与补丁呈现，而非重新发布完整上游作为原创成果。

上游已有 AST 差分与快照框架，因此复用这些机制，重点补有实际价值的用例、最小复现和缺陷修复。贡献指南以有效、非实验语法的参考 AST 一致性为准；不得把工具链版本差异或错误恢复策略差异直接当作 bug。

## 已排除的方向

- 覆盖率展示：社区任务 #82 已有人接手并有阶段产出；当前 `moonbitlang/coverage` 已提供多种报告和上传能力。不再写一套同功能工具。
- 通用静态站点生成：任务 #87 有公开需求，但 Lattice 等 MoonBit 实现已有页面索引、双向链接、Schema、模板和预览功能；不再把通用 SSG 当成空白。
- 进程与网络包装：现有 `moonbitlang/async` 已覆盖相关基础能力，不凭旧任务标题判断未实现。

参考：
- https://github.com/moonbit-community/Community-Tasks/issues/82
- https://github.com/moonbit-community/Community-Tasks/issues/82#issuecomment-3264020723
- https://github.com/moonbitlang/coverage
- https://github.com/moonbit-community/Community-Tasks/issues/87
- https://github.com/0x4m4d3u5/lattice
- https://github.com/moonbitlang/awesome-moonbit

## 申报与实施顺序

先提交需求来源、维护型项目范围与本期新增标准，确认九月赛事接受此改题；目前只做固定基线和小规模差分试验。没有取得任务分配、主办方批准或上游合并结果，不将任何一项写成已取得。

验收产出按“新增样例 → 差异定位 → 最小复现 → 回归 / 修复 PR → 未修改参考预期下测试通过”组织。不能只增加测试数量，不能通过更新全部快照掩盖差异，也不预先承诺能发现多少个缺陷。
