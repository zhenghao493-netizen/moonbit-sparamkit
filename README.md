# MoonBit ParserCheck

面向 `moonbitlang/parser` 的语法一致性回归与缺陷修复项目。复用官方解析器和测试框架，将 MoonBit 源码的解析结果与工具链 `mooninfo` 导出的 AST 对照，产出可复现样例、回归测试和针对性的上游补丁。

需求来源：[Community-Tasks #142：moonbitlang/parser 测试和修复](https://github.com/moonbit-community/Community-Tasks/issues/142)。

## 本期工作

1. 固定上游提交及工具链，建立可重复执行的原有测试基线。
2. 对有效 MoonBit 语法补充组合用例，分别核对手写解析器、生成解析器和参考 AST。
3. 为差异生成最小复现输入；区分解析器缺陷、工具链版本差异和实验语法。
4. 对确认的缺陷提交小范围修复和回归测试，保留修复前后的输出。

不重写一套 MoonBit parser，也不将上游现有代码或测试数计入本期新增成果。AST 对照遵循上游 [贡献指南](https://github.com/moonbitlang/parser/blob/master/CONTRIBUTING.md)，正常语法是首期重点。

## 当前阶段

改题后的范围确认与基线验证。锁定信息在 `upstream.lock.json`；新申报说明在 `docs/PROPOSAL.md`，选题依据和排重记录在 `docs/TOPIC.md`。基线脚本不修改上游源文件，输出完整命令日志和结果 JSON。

```sh
git clone https://github.com/moonbitlang/parser.git upstream
git -C upstream checkout a01fd77e599c12cf9a2182df3456990e74f53ced
python tools/baseline.py upstream
```

需要 MoonBit 官方工具链和 Python 3.11+。仓库 Actions 中的 `Parser topic baseline` 会执行相同流程。

本分支用于重新申报和后续维护工作，原 Touchstone 项目的主分支及 `v0.1.0` 发布文件保持不变。正式提交新题前需由赛事方确认变更范围；社区任务是需求来源，不代表已获分配或九月报名批准。

## 来源与许可

上游 `moonbitlang/parser` 使用 Apache-2.0。本项目新增脚本和测试采用 Apache-2.0；上游代码、作者和许可证保持原样。AI 辅助用于测试设计、定位和文档。对上游的提交按其贡献流程进行。
