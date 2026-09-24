# MoonBit ParserCheck

为 `moonbitlang/parser` 补充语法回归用例、最小复现和修复补丁。项目对照 Handrolled、MoonYacc、CST 转换与工具链参考结果，定位语法树内容和源码位置的不一致。

上游维护者已确认 [#188：负数模式的位置漏掉负号](https://github.com/moonbitlang/parser/issues/188#issuecomment-5809735774)，并欢迎提交修复 PR。当前优先推进这一项的独立提交。

[项目说明](docs/PROPOSAL.md) · [上游状态](docs/UPSTREAM_STATUS.md) · [审阅与复现](docs/REVIEW.md) · [组合回归](docs/LOCATION_MATRIX.md)

## 当前贡献

| 问题 | 修改范围 | 回归用例 | 上游状态 |
| --- | --- | --- | --- |
| [#188](https://github.com/moonbitlang/parser/issues/188)：负数常量模式位置漏掉负号 | 手写解析器与 CST 转换 | 7 个 | 已确认缺陷，准备独立 PR |
| [#189](https://github.com/moonbitlang/parser/issues/189)：多层括号扩大类型约束位置 | CST 转换 | 10 个 | 候选补丁，待确认 |

完整提交补丁位于 [review/](review/)，每份包含对应实现和测试。两项均已验证修复前失败、修复后通过，联合补丁通过四后端完整测试。当前修复尚未合并到官方仓库。

## 验证已确认的修复

准备 MoonBit、Node.js、Python 3.11+ 和 native 测试使用的 C 编译环境。当前审阅基线及工具链由 `upstream.review.lock.json` 固定。

```bash
git clone --branch reselect/parser-conformance \
  https://github.com/zhenghao493-netizen/moonbit-sparamkit.git parsercheck
cd parsercheck
git clone https://github.com/moonbitlang/parser.git upstream
git -C upstream checkout c1174741f8fd5c9b827af7b9148884413e5ebfdd
python tools/verify_issue188.py upstream
```

这条流程只应用 #188 的完整提交补丁，检查原版断言、修复后结果及四个后端的完整套件，不包含 #189。脚本使用临时克隆，传入的上游工作副本保持不变；结果位于 `reports/issue188/run-*/`。每次结果以该目录内的 `result.json` 和命令日志为准。

需要复现两份独立补丁与联合套件时，使用 `python tools/prepare_review.py upstream`，见 [审阅指南](docs/REVIEW.md)。

## 组合语法与文本布局

240 份定向输入覆盖字面量、模式上下文、中文与 emoji、LF / CRLF 和制表符。原版、两项单独修复和联合修复使用相同输入；联合修复后，三个入口的位置、源码切片和带位置 AST 全部一致。

```bash
python tools/test_location_cases.py
python tools/test_location_matrix.py upstream
```

组合检查使用 JS 后端，并附 4 个 MoonBit 取片测试、5 个 Python 辅助测试。240 份语料与 17 个上游回归用例分开统计。详细结果见 [组合回归记录](verification/LOCATION_MATRIX.md)。

## 历史记录

原基线 `a01fd77e` 保留在 `upstream.lock.json`；旧补丁和对应验证脚本用于复现当时结果。当前补丁适配 `c1174741` 的 CST 模块拆分，新旧文件不要混用。

首轮 16 份输入及 `ApplyAttr::NoAttr` 导出结构差异见 [PILOT.md](verification/PILOT.md)。位置修复没有删除这部分差异。`mooninfo` 可检查语法有效性，当前空位置字段不充当位置判据。

Community-Tasks #142 是早期选题线索，其所属活动已经结束。当前需求依据为已确认的具体上游问题，说明见 [选题记录](docs/TOPIC.md)。

## 开发与许可

修复、回归和探针逻辑使用 MoonBit；Python / Node.js 负责执行与报告。已有上游代码和测试作为基线，本期新增成果按补丁、用例及实际提交记录区分。

本项目位于 `reselect/parser-conformance` 分支，原 SParamKit 主分支和发布文件保留。贡献遵循上游 [CONTRIBUTING.md](https://github.com/moonbitlang/parser/blob/master/CONTRIBUTING.md)。

采用 [Apache-2.0](LICENSE)，保留上游作者和版权说明。开发使用 AI 辅助测试设计、定位及文档整理。
