# 已确认问题 #188 的独立提交检查

日期：2026-09-24。受测 ParserCheck 提交：`476e8aeabfdd7672a360029c2d867eb662d1c67d`。
上游基线：`c1174741f8fd5c9b827af7b9148884413e5ebfdd`。

## 维护者确认

Yoorkin 已在 [#188](https://github.com/moonbitlang/parser/issues/188#issuecomment-5809735774) 确认负数常量模式的位置缺陷，并欢迎修复 PR。他同时说明 OCaml 实现也存在同类问题，将先修复参考实现。#189 未取得同样确认，不包含在本次独立提交中。

## 本轮执行

[Verify confirmed issue 188 independently #1](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35976306257) 从干净上游检出目录创建临时克隆，直接通过 `git am` 应用现有的 `review/issue-188.patch`。检查范围为两个实现文件和一个回归文件。

流程保留补丁内的测试文件，先恢复未修改的实现，确认原版失败；再恢复完整补丁中的实现，运行相同回归及完整套件。既不应用 #189，也不修改原有预期。

| 检查 | 实际结果 |
| --- | --- |
| 原实现上的新增测试编译 | 启用 --deny-warn，通过 |
| 原实现上的 7 个回归 | 6 项断言失败，1 项正数对照通过 |
| 独立 #188 补丁后的相同回归 | 7/7 通过 |
| 格式与类型检查 | moon fmt --check、moon check --deny-warn 通过 |
| 完整套件 wasm | 2845/2845 |
| 完整套件 wasm-gc | 2842/2842 |
| 完整套件 JS | 2842/2842 |
| 完整套件 native | 2847/2847 |
| 修改范围 | 两个实现文件与一个回归文件，与完整补丁一致 |
| 原始工作副本 | 未修改 |

上游完整套件包含既有测试；本项仍为 7 个新增回归。此处计数与此前两项联合补丁的计数分开，少了 #189 的 10 个用例。

工具链为 moon 0.1.20260920、moonc v0.10.14+7d59c7ec9。测试执行时间为 08:37:32–08:42:24 UTC；本轮完整编译和测试来自上述 CI。本地检查了脚本语法、下载附件和原始结果，不声称本地重新编译了 MoonBit。

## 下载后核对

已下载 `confirmed-issue188-evidence`（附件 ID `10798307668`），读取修复前后断言、四后端完整套件日志和修改文件列表。20 份命令日志的 SHA256 均与 result.json 相符；下载补丁与仓库中的既有补丁一致。

- 附件 ZIP SHA256：`a1c0bcd20751cbddbfc82349063f34a5fcb8d8c2ee383ecbd2a758c326095d4f`。
- 独立补丁 SHA256：`537eb21b6786a8724f58c90816a67d6ff561779a3d846798e7c7ffca26a7ce87`。
- 两个实现文件：`handrolled_parser/parser.mbt`、`untyped_cst/internal/lower/pattern.mbt`。
- 回归文件：`test/manual_test/negative_pattern_loc_test.mbt`。

PR 文案位于 [issue-188-pr.md](../review/issue-188-pr.md)。当前只有补丁与提交说明，正式上游 PR 尚未创建；账号侧 fork 入口仍待准备。维护者回复、历史任务状态及具体阻塞见 [UPSTREAM_STATUS.md](../docs/UPSTREAM_STATUS.md)。
