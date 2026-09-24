# 两项源码位置修复的审阅入口

当前审阅基线为 `moonbitlang/parser@c1174741f8fd5c9b827af7b9148884413e5ebfdd`，由 `upstream.review.lock.json` 固定。CST 拆分后，模式转换代码位于 `untyped_cst/internal/lower/pattern.mbt`。

## 补丁划分

| 问题 | 完整提交补丁 | 修改范围 | 回归用例 |
| --- | --- | --- | --- |
| [#188](https://github.com/moonbitlang/parser/issues/188)：负数模式漏掉负号的位置 | [issue-188.patch](../review/issue-188.patch) | 手写解析器、CST 模式转换 | 7 个 |
| [#189](https://github.com/moonbitlang/parser/issues/189)：分组扩大类型约束的位置 | [issue-189.patch](../review/issue-189.patch) | CST 模式转换 | 10 个 |

每份完整补丁都包含对应的 MoonBit 回归测试，分别从同一个上游基线生成，可以单独审阅或应用。`patches/current/` 仅保存实现差异，供自动化测试使用；原 `patches/` 下的旧补丁与历史记录仍对应 `a01fd77e`，不要混用。

## 单项审阅

以 #188 为例，在上游仓库创建自己的分支后应用补丁：

```bash
git switch -c review-pattern-sign c1174741f8fd5c9b827af7b9148884413e5ebfdd
git am /absolute/path/to/parsercheck/review/issue-188.patch
moon update
moon test test/manual_test/negative_pattern_loc_test.mbt --target js --deny-warn
```

#189 使用另外一个从同一基线创建的分支，应用 `issue-189.patch`，测试文件为 `test/manual_test/grouped_constraint_loc_test.mbt`。在新分支中依次应用两份补丁后，可运行 `moon test --target all` 进行联合回归。

## 自动复现修复前后的结果

在 ParserCheck 工作目录中，准备 MoonBit `moonc v0.10.14+7d59c7ec9`、Node.js、Python 3.11+ 与用于 native 测试的 C 编译环境：

```bash
git clone https://github.com/moonbitlang/parser.git upstream
git -C upstream checkout c1174741f8fd5c9b827af7b9148884413e5ebfdd
python tools/prepare_review.py upstream
```

脚本创建临时克隆，不在传入的工作副本上修改源码。它会依次：

1. 核对上游版本，检查 17 份输入是否被参考工具接受。
2. 分别运行两份回归测试，检查原版断言失败、单独应用对应补丁后通过。
3. 共同应用两份补丁，运行格式、类型检查及四后端完整测试。
4. 生成两份独立 `git format-patch`，在另一个干净克隆中通过 `git am` 重放，并比较重放后与受测文件的字节。

结果写入独立的 `reports/current-review/run-*/` 目录。`result.json` 记录状态、命令、原始日志位置和补丁哈希；`ready/` 包含生成的完整提交补丁。只有顶层状态为 `passed` 的结果才代表整条流程完成。本轮执行结果见 [CURRENT_REVIEW.md](../verification/CURRENT_REVIEW.md)。

源码位置的预期来自原始文本切片与三个解析入口的一致性。`mooninfo` 用于确认语法有效性，其空位置字段不充当位置参考。原 pilot 中的 `ApplyAttr` 导出差异不在这两项补丁的处理范围内。

上游是否接收修改，以 #188、#189 的维护者意见为准。
