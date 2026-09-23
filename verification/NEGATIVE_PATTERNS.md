# 负数模式位置回归

日期：2026-09-23。上游问题：[moonbitlang/parser #188](https://github.com/moonbitlang/parser/issues/188)。

上游基线：`a01fd77e599c12cf9a2182df3456990e74f53ced`（parser 0.4.0）。本次测试的补丁与用例提交：`d11be531363d3acf0783d311849f0d6fc61a0e2b`。

## 问题与修改

最小输入：

```moonbit
fn f(x) { match x { -1 => 1; _ => 0 } }
```

Handrolled 和 CST 转换后的 `Pattern::Constant` 位置为 `1:22-1:23`，只覆盖数字 `1`；MoonYacc 的位置为 `1:21-1:23`，覆盖完整的 `-1`。三个入口都没有诊断，常量值也都是 `-1`。

补丁只修改两处源码：

- `handrolled_parser/parser.mbt`：在读取负号前保存起点，读取数值后生成完整位置。
- `untyped_cst/lower.mbt`：负数常量模式使用模式节点的完整位置，不再缩到数字子节点。

回归用例覆盖负整数、负浮点数、负号与数字间的空白、区间、或模式、构造器内嵌模式，以及正数对照。测试用位置切片核对原始源码，并比较三种入口的完整带位置 AST。

## 实际执行结果

[验证任务 35861953998](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35861953998) 在干净的上游检出目录执行。附件已下载并逐项核对日志。

| 阶段 | 结果 |
| --- | --- |
| 应用补丁前，编译新增用例 | 通过，启用 `--deny-warn` |
| 应用补丁前，执行新增用例 | 7 项中 6 项断言失败、1 项正数对照通过 |
| 应用补丁后，执行相同用例 | 7/7 通过，预期未修改 |
| 格式、严格检查 | `moon fmt --check`、`moon check --deny-warn` 通过 |
| 完整测试：wasm | 2753/2753 |
| 完整测试：wasm-gc | 2750/2750 |
| 完整测试：JS | 2750/2750 |
| 完整测试：native | 2755/2755 |

四个后端的总数包括上游既有用例，本次新增的是同一套 7 个测试。补丁没有修改参考快照或生成的 yacc 源码，也没有改变负数值的解析方式。

第一轮新增测试因重复导入 `IterVisitor` 触发严格编译警告；已改为限定名称后重新执行。首次探针构建还修正过工作区产物路径。上述失败记录保留，不算作上游缺陷。

工具链：moon 0.1.20260920，moonc v0.10.14+7d59c7ec9。完整测试命令耗时 449.93 秒。

附件：`negative-pattern-patch-evidence`，ID `10751341675`，ZIP SHA256：`09efa0b7f6c1e449090a53b1bf77d3442526ef2e10e932d28ef40667be4f9709`。内含修复前后日志、四后端日志、实际格式化后的测试文件和源码差异。

补丁 SHA256：`07491adda3a8e0d2114f4ec90c9d3d6aead4d753f2191f469ad9ea69d94bce5d`。

## 对照依据

本地用相同版本 `mooninfo` 检查了七份回归输入，均无语法错误或弃用语法标记。当前参考 AST 的位置字段为空，因此位置预期来自源码切片和 MoonYacc，而不是声称取得了带位置的官方参考输出。

上一轮的 `ApplyAttr::NoAttr` 差异继续作为 AST 导出结构兼容问题单独跟踪，不包含在本补丁中。其原始对照仍有差异，没有通过删除字段或更新快照将其改成通过。

## 复现

在本分支准备 MoonBit 工具链、Node.js、Python 3.11+ 和本地 C 编译环境，然后执行：

```bash
git clone https://github.com/moonbitlang/parser.git upstream
git -C upstream checkout a01fd77e599c12cf9a2182df3456990e74f53ced
(cd upstream && moon update)
python tools/verify_patch.py upstream
```

脚本会向这个上游检出目录添加测试并应用补丁，使用单独的工作副本运行。日志写入 `reports/negative-patterns/`。脚本保留受测改动供检查，不自动清理已有源码。

## 上游状态

已提交问题 #188，附最小复现、候选补丁、用例和完整测试结果。位置约定正在请求维护者确认；尚未提交或合并上游修复 PR。本次工作不代表赛事方已经批准改题。原 SParamKit 主分支和发布版本未改动。
