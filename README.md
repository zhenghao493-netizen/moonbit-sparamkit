# MoonBit ParserCheck

为 `moonbitlang/parser` 补充语法回归用例、最小复现和修复补丁。项目复用官方解析器与测试框架，对照 Handrolled、MoonYacc、CST 转换和工具链参考 AST，定位解析结果及源码位置的不一致。

需求来源：[Community-Tasks #142：moonbitlang/parser 测试和修复](https://github.com/moonbit-community/Community-Tasks/issues/142)。

[项目说明](docs/PROPOSAL.md) · [选题依据](docs/TOPIC.md) · [基线记录](verification/BASELINE.md)

## 当前贡献

| 问题 | 候选修复 | 新增回归 | 上游讨论 |
| --- | --- | --- | --- |
| 负数常量模式的位置漏掉负号 | 手写解析器与 CST 转换保留完整符号范围 | 7 个用例 | [#188](https://github.com/moonbitlang/parser/issues/188) |
| 多层括号扩大类型约束模式的位置 | CST 转换保留内层约束的位置 | 10 个用例 | [#189](https://github.com/moonbitlang/parser/issues/189) |

两份补丁均已验证修复前失败、修复后通过，并共同通过四个后端的完整上游测试。当前等待维护者确认位置约定，尚未合并到官方仓库。

第一份补丁处理 `-1` 被定位成 `1` 的问题，见 [补丁](patches/0001-negative-pattern-locations.patch)、[测试](regressions/negative_pattern_loc_test.mbt) 和 [记录](verification/NEGATIVE_PATTERNS.md)。

第二份补丁处理 `((x : Int))` 中约束位置被多余括号扩大的问题，见 [补丁](patches/0002-grouped-constraint-locations.patch)、[测试](regressions/grouped_constraint_loc_test.mbt) 和 [联合回归记录](verification/GROUPED_CONSTRAINTS.md)。

## 运行回归验证

准备 MoonBit 工具链、Node.js、Python 3.11+；native 测试还需要本地 C 编译环境。当前验证环境为 moonc `v0.10.14+7d59c7ec9`，上游提交由 `upstream.lock.json` 固定。

```bash
git clone --branch reselect/parser-conformance \
  https://github.com/zhenghao493-netizen/moonbit-sparamkit.git parsercheck
cd parsercheck
git clone https://github.com/moonbitlang/parser.git upstream
git -C upstream checkout a01fd77e599c12cf9a2182df3456990e74f53ced
(cd upstream && moon update)
python tools/verify_grouped_patch.py upstream
```

脚本先编译并运行分组约束的新测试，确认原版有 7 项断言失败、3 项对照通过；只应用分组补丁后，同一套 10 个测试通过。随后加入负数模式补丁及其 7 个用例，再执行 `moon test --target all`。日志和 JSON 结果保存在 `reports/grouped-constraints/`。

只检查第一份补丁时，在另一个干净上游副本中运行 `python tools/verify_patch.py <目录>`。仅核对原有基线使用 `python tools/baseline.py <目录>`。这些命令不要共用已经应用补丁的工作副本。

两份补丁新增的是 17 个回归用例；完整上游套件的数量不计入本期新增成果。脚本保留受测改动和失败输出，不自动删除源码或更新快照。

## 差异筛查

`probe/` 用 MoonBit 调用三种解析入口；`tools/probe.cjs` 提供 JSON 进出通道。探针可同时保留或隐藏源码位置，便于将 AST 内容差异与位置差异分开检查。探针构建见 [工作流](.github/workflows/parser-triage.yml)。

首轮 16 份输入的原始参考对照保存在 [PILOT.md](verification/PILOT.md)。其中的 `ApplyAttr::NoAttr` 导出结构差异单独跟踪。`tools/pilot.py` 发现原始差异时返回非零，与上述定向修复验证分别报告；两份位置补丁均不修改 AST 导出字段。

后续贡献沿用上游 [贡献指南](https://github.com/moonbitlang/parser/blob/master/CONTRIBUTING.md)：有效语法、最小复现、问题确认、针对性回归和小范围修复。

## 开发与许可

新增修复和回归逻辑使用 MoonBit；Python 负责执行测试及整理报告。上游现有源码和测试作为基线，本期新增工作按补丁与测试文件记录。

本项目位于 `reselect/parser-conformance` 分支，原 SParamKit 主分支与发布版本保留。改题申报信息见 [项目说明](docs/PROPOSAL.md)。

采用 [Apache-2.0](LICENSE)。上游作者和版权说明保持原样。开发中使用 AI 辅助测试设计、问题定位和文档整理。
