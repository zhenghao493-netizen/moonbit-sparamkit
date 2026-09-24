# MoonBit ParserCheck

为 `moonbitlang/parser` 补充语法回归用例、最小复现和修复补丁。项目复用官方解析器与测试框架，对照 Handrolled、MoonYacc、CST 转换和工具链参考 AST，定位解析结果及源码位置的不一致。

需求来源：[Community-Tasks #142：moonbitlang/parser 测试和修复](https://github.com/moonbit-community/Community-Tasks/issues/142)。

[项目说明](docs/PROPOSAL.md) · [审阅与复现](docs/REVIEW.md) · [本轮验证](verification/CURRENT_REVIEW.md) · [选题依据](docs/TOPIC.md)

## 当前贡献

| 问题 | 候选修复 | 新增回归 | 上游讨论 |
| --- | --- | --- | --- |
| 负数常量模式的位置漏掉负号 | 手写解析器与 CST 转换保留完整符号范围 | 7 个用例 | [#188](https://github.com/moonbitlang/parser/issues/188) |
| 多层括号扩大类型约束模式的位置 | CST 转换保留内层约束的位置 | 10 个用例 | [#189](https://github.com/moonbitlang/parser/issues/189) |

两份补丁已适配上游 `c1174741` 的 CST 模块拆分。分别验证原版失败、单独修复后通过，再共同运行四个后端的完整测试。当前等待维护者确认位置约定，尚未合并到官方仓库。

完整提交补丁位于 [review/](review/)，每份都包含实现和测试，可以分别通过 `git am` 应用。自动化流程还会重新应用导出的补丁，核对其与受测源码一致。

## 运行当前版本验证

准备 MoonBit 工具链、Node.js、Python 3.11+；native 测试还需要本地 C 编译环境。本次工具链为 moonc `v0.10.14+7d59c7ec9`，上游版本由 `upstream.review.lock.json` 固定。

```bash
git clone --branch reselect/parser-conformance \
  https://github.com/zhenghao493-netizen/moonbit-sparamkit.git parsercheck
cd parsercheck
git clone https://github.com/moonbitlang/parser.git upstream
git -C upstream checkout c1174741f8fd5c9b827af7b9148884413e5ebfdd
python tools/prepare_review.py upstream
```

脚本在临时克隆中执行，不修改传入的上游工作副本。报告保存在独立的 `reports/current-review/run-*/` 目录；`ready/` 包含完整提交补丁。具体步骤见 [审阅指南](docs/REVIEW.md)。

两份补丁新增的是 17 个回归用例；完整上游套件数量不计入本期新增成果。源码切片和完整带位置 AST 都参与判断，不以更新参考快照消除失败。

## 历史记录与差异筛查

原始上游基线 `a01fd77e` 保留在 `upstream.lock.json`。旧补丁、`tools/verify_patch.py` 和 `tools/verify_grouped_patch.py` 继续用于复现当时的结果，见 [负数模式记录](verification/NEGATIVE_PATTERNS.md) 和 [分组模式记录](verification/GROUPED_CONSTRAINTS.md)。新旧补丁不要混用。

`probe/` 用 MoonBit 调用三种解析入口；`tools/probe.cjs` 提供 JSON 进出通道。探针可以保留或隐藏源码位置，将 AST 内容差异与位置差异分开检查。

首轮 16 份输入的参考对照见 [PILOT.md](verification/PILOT.md)。其中的 `ApplyAttr::NoAttr` 导出结构差异单独跟踪；本轮位置修复没有修改这部分输出。

贡献流程遵循上游 [贡献指南](https://github.com/moonbitlang/parser/blob/master/CONTRIBUTING.md)：有效语法、最小复现、问题确认、针对性回归和小范围修复。

## 开发与许可

新增修复和回归逻辑使用 MoonBit；Python 负责执行测试及整理报告。上游现有源码和测试作为基线，本期新增工作按补丁与测试文件记录。

本项目位于 `reselect/parser-conformance` 分支，原 SParamKit 主分支与发布版本保留。改题申报信息见 [项目说明](docs/PROPOSAL.md)。

采用 [Apache-2.0](LICENSE)。上游作者和版权说明保持原样。开发中使用 AI 辅助测试设计、问题定位和文档整理。
