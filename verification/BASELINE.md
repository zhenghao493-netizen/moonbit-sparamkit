# 上游基线 — 2026-09-23

上游：`moonbitlang/parser@a01fd77e599c12cf9a2182df3456990e74f53ced`，模块 0.4.0。

执行记录：[Parser topic baseline #1](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35854953554)。下载并核对 `parser-baseline` 附件后，实际结果如下：

| 后端 | 上游原有测试 |
| --- | --- |
| wasm | 2746/2746 |
| wasm-gc | 2743/2743 |
| JS | 2743/2743 |
| native | 2748/2748 |

`moon update`、`moon check --deny-warn` 和 `moon test --target all` 均退出 0；执行后没有修改受跟踪的上游文件。完整测试命令耗时 438.48 秒。工具链为 moon 0.1.20260920 / moonc 0.10.14。

这些是上游既有测试，不是本项目新增成果。首批新输入在 `fixtures/pilot.json`，差分试验由 `tools/pilot.py` 单独执行，不与上述基线数量混算。

本地已用同一版本 `mooninfo` 筛选输入：最初 20 份候选中有一份语法错误、三份包含弃用语法标记，因此仅保留符合贡献指南条件的 16 份。手写解析器和生成解析器的对照结果应读取后续 pilot 附件，不能把参考语法检查当成两种解析器已通过。

本地原始源码包包含依赖源码，但没有 registry index、native include 和 yacc 预构建缓存，本地 probe 尝试未完成。已将相同试验交给具有完整开发依赖的云端环境执行；不会将这些环境阻塞算作解析器缺陷。
