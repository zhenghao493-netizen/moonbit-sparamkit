# 上游反馈与提交状态

核对日期：2026-09-24。

| 项目 | 当前状态 | 下一步 |
| --- | --- | --- |
| parser #188：负数模式位置 | 维护者已确认缺陷，欢迎修复 PR | 单独提交两处实现修改和 7 个回归用例 |
| parser #189：分组约束位置 | 已报告，尚无维护者确认 | 保留独立候选补丁，不夹带进 #188 |
| Community-Tasks #142 | 所属历史活动已结束；仍欢迎开源贡献 | 仅作为历史线索，不作为本期任务资格 |
| 九月比赛改题 | 未取得本次改题批准记录 | 按比赛方流程审查，不与上游状态混同 |

## 维护者原始回复

[#188 的确认](https://github.com/moonbitlang/parser/issues/188#issuecomment-5809735774) 明确说明问题已确认、OCaml 实现也有同类问题，并欢迎向本仓库提交修复 PR。

[#142 的说明](https://github.com/moonbit-community/Community-Tasks/issues/142#issuecomment-5809898434) 明确该列表原属 J139 小队，活动已结束；开源贡献继续遵循各仓库 `CONTRIBUTING.md`。

## #188 提交准备

使用 `review/issue-188.patch`，基于 `c1174741f8fd5c9b827af7b9148884413e5ebfdd`。该文件包含两个实现文件与一个 7 用例回归文件，没有 #189、组合测试工具、项目文档或 CI 修改。

正式 PR 说明在 [issue-188-pr.md](../review/issue-188-pr.md)。`tools/verify_issue188.py` 在临时克隆中直接应用这份完整补丁，复现原版断言，再检查修复后及四后端完整套件。结果单独保存，不沿用联合补丁的计数。

当前 GitHub 连接可以提交文件与创建 PR，但未提供创建 fork 的操作；账号可见仓库中尚未找到 `moonbitlang/parser` 的 fork。没有创建正式上游 PR。fork 准备并可访问后，应从上游基线创建 `fix/negative-pattern-location` 分支，只应用本项补丁，目标为 `moonbitlang/parser:master`。不从存放项目资料的 SParamKit 分支直接向上游发起 PR。

GitHub 的标准流程见 [从 fork 创建 PR](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request-from-a-fork)。本文件记录操作状态；不会把本地准备好的补丁或说明文件称为已提交的 PR。
