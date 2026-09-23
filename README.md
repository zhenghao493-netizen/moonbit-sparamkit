# MoonBit ParserCheck

为 `moonbitlang/parser` 补充语法回归用例、最小复现和修复补丁。项目复用官方解析器与测试框架，对照 Handrolled、MoonYacc、CST 转换和工具链参考 AST，定位解析结果及源码位置的不一致。

需求来源：[Community-Tasks #142：moonbitlang/parser 测试和修复](https://github.com/moonbit-community/Community-Tasks/issues/142)。

[项目说明](docs/PROPOSAL.md) · [选题依据](docs/TOPIC.md) · [基线记录](verification/BASELINE.md)

## 当前贡献

### 负数模式的位置范围

对于 `match` 中的 `-1`，Handrolled 和 CST 转换生成的位置只覆盖数字 `1`，MoonYacc 则覆盖完整的 `-1`。候选补丁统一这两个实现的起止位置，保留原有常量值和 AST 字段。

- 上游讨论：[moonbitlang/parser #188](https://github.com/moonbitlang/parser/issues/188)。
- [源码补丁](patches/0001-negative-pattern-locations.patch)：修改手写解析器和 CST 转换，共两处实现文件。
- [七个回归用例](regressions/negative_pattern_loc_test.mbt)：覆盖整数、浮点、空白、区间、或模式、嵌套和正数对照。
- [执行记录](verification/NEGATIVE_PATTERNS.md)：原版 6 项失败、1 项通过；应用补丁后 7 项全部通过，四个后端的完整上游测试通过。

补丁已完成本分支验证，正在请求上游确认位置约定，尚未合并到官方仓库。

## 运行回归验证

准备 MoonBit 工具链、Node.js、Python 3.11+；native 测试还需要本地 C 编译环境。当前验证环境为 moonc `v0.10.14+7d59c7ec9`，上游提交由 `upstream.lock.json` 固定。

```bash
git clone https://github.com/moonbitlang/parser.git upstream
git -C upstream checkout a01fd77e599c12cf9a2182df3456990e74f53ced
(cd upstream && moon update)
python tools/verify_patch.py upstream
```

脚本先编译并运行新增测试，确认原版能复现问题；随后应用补丁、运行相同测试，再执行 `moon test --target all`。日志和 JSON 结果保存在 `reports/negative-patterns/`。

请使用单独的上游工作副本：脚本会添加回归文件并应用补丁，结束后保留这些改动供检查。只核对未修改的基线时，在另一个干净检出目录执行 `python tools/baseline.py <目录>`。

## 差异筛查

`probe/` 用 MoonBit 调用三种解析入口；`tools/probe.cjs` 提供 JSON 进出通道。探针可同时保留或隐藏源码位置，便于将 AST 内容差异与位置差异分开检查。探针构建见 [工作流](.github/workflows/parser-triage.yml)。

首轮 16 份输入的原始参考对照保存在 [PILOT.md](verification/PILOT.md)。其中的 `ApplyAttr::NoAttr` 导出结构差异单独跟踪，不通过删字段或更新参考快照消除。负数模式补丁不涉及这部分输出。

后续贡献沿用上游 [贡献指南](https://github.com/moonbitlang/parser/blob/master/CONTRIBUTING.md)：有效语法、最小复现、问题确认、针对性回归和小范围修复。

## 开发与许可

新增修复和回归逻辑使用 MoonBit；Python 负责执行测试及整理报告。上游现有源码和测试作为基线，本期新增工作按补丁与测试文件记录。

本分支为 `reselect/parser-conformance`，原 SParamKit 主分支与发布版本保留。改题申报信息见 [项目说明](docs/PROPOSAL.md)。

采用 [Apache-2.0](LICENSE)。上游作者和版权说明保持原样。开发中使用 AI 辅助测试设计、问题定位和文档整理。
