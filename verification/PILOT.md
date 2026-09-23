# 首轮差分试验

日期：2026-09-23。本轮目标是验证改题路线和对照流程，不将试验结果直接当作已经确认的上游缺陷。

## 已执行

- 上游固定为 `moonbitlang/parser@a01fd77e599c12cf9a2182df3456990e74f53ced`，模块 0.4.0。
- [原有测试基线](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35854953554) 在 wasm、wasm-gc、JS、native 均通过；未修改上游受跟踪源码。数量详见 [BASELINE.md](BASELINE.md)，不计入本项目新增成果。
- [新差分试验](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35856147393) 已实际运行，使用 MoonBit 编译器 0.10.14 和 JS 后端调用上游两种解析器。
- 16 份新输入全部由 `mooninfo` 确认为无语法错误、无弃用语法标记。每份分别由 Handrolled 与 MoonYacc 解析，共 32 次参考 AST 对照。

## 结果

22 次 AST 完全一致；另外 10 次有结构差异，涉及 5 份输入：`array_prefix`、`array_tail`、`closure_nested`、`labelled_call`、`local_function`。两种解析器均未产生语法诊断。

不一致的首个位置都是调用表达式：上游 parser 输出包含 `attr: {kind: "ApplyAttr::NoAttr", loc: null, children: {}}`，本次 `mooninfo` 参考输出缺少该字段。两种 MoonBit 解析器在这几份输入上的表现相同。这应先作为 AST 导出模式 / 版本兼容性问题核实，而不是声称发现 10 个解析器 bug。

差分工作流按严格比较返回失败；原始参考 JSON、解析器 stdout、编译日志和每次比较的第一处差异都保存在 `parser-pilot` 附件（ID 10747721963）。没有删除 `attr` 字段、覆盖快照或修改参考输出来制造通过结果。

试验程序有一项 `ToJson` 方法调用迁移提醒和一项未使用导入提醒；它们属于新增 probe 的清理工作，不是上游缺陷。核心解析器已执行，不能把这两项提醒描述为导致试验无法运行。

## 下一步范围

先与上游确认参考 AST 的版本和导出模式约定，再形成最小复现及针对性回归 / 修复。上游当前还有 CST 对照机制，后续新增测试应接入其现有框架，而不是另造一套生产解析器。

本阶段交付为：公开需求依据、锁定基线、新输入、可运行差分试验和待确认的问题记录。修复 PR、任务分配和九月改题审批均未完成。新申报说明见 [PROPOSAL.md](../docs/PROPOSAL.md)。
