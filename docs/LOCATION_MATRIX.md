# 模式位置组合回归

本检查将负数模式、类型约束和分组语法组合起来，分别验证原版解析器、单独应用每份补丁、共同应用两份补丁时的行为。

## 运行

使用 `reselect/parser-conformance` 分支，准备 MoonBit 编译器 `v0.10.14+7d59c7ec9`、Node.js 22、Python 3.11+。上游版本由 `upstream.review.lock.json` 指定。

```bash
git clone --branch reselect/parser-conformance \
  https://github.com/zhenghao493-netizen/moonbit-sparamkit.git parsercheck
cd parsercheck
git clone https://github.com/moonbitlang/parser.git upstream
git -C upstream checkout c1174741f8fd5c9b827af7b9148884413e5ebfdd
python tools/test_location_cases.py
python tools/test_location_matrix.py upstream
```

脚本会创建临时克隆并安装上游依赖，首次运行需要联网。传入的上游目录须干净；原目录不被修改。新增探针使用 MoonBit 访问三种解析入口、遍历模式及提取位置对应的源码；Node 只传输 JSON，Python 负责输入生成、执行和结果检查。

## 输出

每次运行写入独立的 `reports/location-matrix/run-*/`：

| 文件 | 内容 |
| --- | --- |
| `cases.json` | 完整的 240 份输入、预期原文和分类 |
| `reference/` | 原始源文件和 mooninfo 语法检查输出 |
| `baseline.raw.json` 等 | 四种补丁配置下三种解析入口的原始输出 |
| `*.comparisons.json` | 逐个输入的位置、原文和 AST 比较结果 |
| `formatted-probe/` | 实际格式化后参与构建的 MoonBit 探针 |
| `logs/` | 编译、执行、补丁应用与还原日志 |
| `result.json` | 汇总结果、文件哈希与工作副本状态 |

完整成功必须是顶层 `status: passed`。脚本会确认原版能暴露定向位置差异，单项修复只消除对应范围的差异，联合修复后全部一致；只报告最终配置通过不够。

同一输入必须同时通过零诊断、位置对应原文和完整带位置 AST 三类检查。额外的非位置 AST 内容检查用于防止位置补丁改变解析内容，不替代上述位置检查。

语料涵盖正负数、负零、指数形式、嵌套约束、中文和 emoji 注释、LF / CRLF 与制表符。它是两个问题的组合测试，不是 MoonBit 全部语法的一致性测试。供上游审阅的两个补丁和 17 个回归用例仍见 [审阅入口](REVIEW.md)。

实际运行记录见 [LOCATION_MATRIX.md](../verification/LOCATION_MATRIX.md)。
