# 分组类型约束的位置回归

执行日期：2026-09-23。上游问题：[moonbitlang/parser #189](https://github.com/moonbitlang/parser/issues/189)。

上游基线：`a01fd77e599c12cf9a2182df3456990e74f53ced`。受测补丁与用例提交：`fc9dc89747fe7dc8f867ac1ffc2421150315a856`。

## 问题

```moonbit
fn f(x) { let ((x : Int)) = x; x }
```

关闭位置输出时，三个解析入口的 AST 一致，且都没有语法诊断。打开位置后，`Pattern::Constraint` 的范围不同：

| 入口 | 位置 | 对应源码 |
| --- | --- | --- |
| Handrolled | `1:16-1:25` | `(x : Int)` |
| MoonYacc | `1:16-1:25` | `(x : Int)` |
| CST 转换 | `1:15-1:26` | `((x : Int))` |

`lower_tuple_pattern` 原来会将任何已经转换为 Constraint 的子模式，重新赋予当前分组节点的位置。内层类型约束经过额外括号分组时，原有范围因此被扩大。补丁只在直接子节点为 `Pattern_Constraint` 时设置当前括号范围；额外分组保留内层位置。

上游已有的 grouped-pattern 位置用例只比较 Handrolled 和 MoonYacc。本次用例同时检查 CST 转换、源码切片和三种入口的完整带位置 AST。

## 实际验证

[任务 35875522683](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35875522683) 在干净的上游检出目录执行。下载附件后检查了 result.json、修复前后日志、完整套件日志及实际测试文件。

| 阶段 | 结果 |
| --- | --- |
| 从新增测试中提取的 10 份输入 | mooninfo 均无语法错误和弃用语法标记 |
| 应用补丁前编译测试文件 | 通过，启用 --deny-warn |
| 原版运行 10 个新测试 | 7 个断言失败、3 个对照通过 |
| 只应用本次分组补丁 | 相同 10 个测试全部通过 |
| 加入前一份负数模式补丁 | 两份补丁可共同应用 |
| 格式和严格检查 | moon fmt --check、moon check --deny-warn 通过 |
| 联合完整测试：wasm | 2763/2763 |
| 联合完整测试：wasm-gc | 2760/2760 |
| 联合完整测试：JS | 2760/2760 |
| 联合完整测试：native | 2765/2765 |

本次新增 10 个测试；与前一份修复合计 17 个。四后端总数包含上游既有测试，不作为本项目新增数量。新用例覆盖双层和多层分组、元组类型约束、构造器、数组、嵌套约束、跨行括号，以及直接约束和无约束模式对照。

修复前实际断言示例：`["((x : Int))"] != ["(x : Int)"]`。修复后不改预期、不更新快照，三种入口的位置与源码切片一致。联合完整套件耗时 475.118 秒。

工具链：moon 0.1.20260920，moonc v0.10.14+7d59c7ec9。

## 证据与复现

附件：`grouped-constraint-patch-evidence`，ID `10757956873`。

- 附件 ZIP SHA256：`f68f0a00a50ad9086371ae00902407a1304110a2760a1ac43f63079984b42e1e`。
- 本次补丁 SHA256：`3f235a8c229aea228a83aad6a240d708e36ea43069dec3bf22d608d669ad031a`。
- 前次补丁 SHA256：`07491adda3a8e0d2114f4ec90c9d3d6aead4d753f2191f469ad9ea69d94bce5d`。

下载后的两份实际格式化测试文件与本地受审文件逐字节一致；云端 combined.patch 应用后，也与本地两份补丁组合生成的实现文件一致。

在干净、可丢弃的上游工作副本中执行：

```bash
git clone https://github.com/moonbitlang/parser.git upstream
git -C upstream checkout a01fd77e599c12cf9a2182df3456990e74f53ced
(cd upstream && moon update)
python tools/verify_grouped_patch.py upstream
```

脚本会添加测试并应用两份候选补丁，结束后保留改动供检查。不要与 `tools/verify_patch.py` 共用已经修改过的目录。

## 对照边界与上游状态

位置预期依据源码切片、Handrolled / MoonYacc 一致行为及分组语法；当前 mooninfo 导出的位置为空，不能作为带位置的参考输出。另一个带完整类型的本地演示程序使用相同分组形式，严格检查通过并输出 42，说明这一形式可以用于正常程序。

本地已执行原版三入口探针、参考语法检查和补丁应用一致性检查。完整上游编译因本地缺少 registry 索引而未执行成功；上面的修复前后与四后端结果来自本轮云端实际运行，不混称本地结果。

已向上游提交 #189，请维护者确认位置约定；#188 本轮查询时仍无评论。两份修复 PR 尚未提交或合并。原 pilot 中的 ApplyAttr 导出模式差异继续单独保留，本记录不表示整个原始差分试验已经一致。
