# SParamKit 申报功能对应表

本次交付沿用申报范围：一端口、二端口 Touchstone 文件的解析、检查、曲线展示和全量导出，以及供其他 MoonBit 项目使用的核心库。

## 功能与核验入口

| 申报内容 | 实现入口 | 演示或测试方式 |
| --- | --- | --- |
| Network、Sample、Complex、Diagnostic 数据模型和统一解析入口 | `types.mbt`、`parser.mbt` | `core_wbtest.mbt`、`api_test.mbt` |
| 选项、注释、科学计数法和跨行记录 | `lexer.mbt`、`options.mbt`、`parser.mbt` | `compatibility_wbtest.mbt`；导入带 BOM / CR 换行的样例 |
| Hz / kHz / MHz / GHz 与 RI / MA / DB 表示转换 | `parser.mbt`、`types.mbt` | `tools/crosscheck.py`；`tools/test_numeric.py` |
| 正确查询 S11、S21、S12、S22 | `Network::get_s` | 非对称双端口单元测试及独立模块接入测试 |
| 幅度、分贝、相位和零值处理 | `Complex` 方法、`report.mbt` | `numeric_wbtest.mbt`；工作台数值边界与导出检查 |
| 有位置的错误诊断与输入限制 | `parser.mbt`、`metadata.mbt`、`report.mbt` | 错误定位按钮；非法数据、阻抗冲突、20,001 频点拒绝测试 |
| 全量 CSV / JSON 导出 | `export.mbt`、`report.mbt` | 20,000 个双端口频点导出，CSV 共 80,000 行参数数据 |
| 离线工作台、文件 / 拖放 / 文本输入、曲线和分页表格 | `bridge/`、`web/` | `tools/test_browser.py`；逐点读数和频率轴切换 |
| 文件 CLI 与可复用 MoonBit 库 | `tools/cli.cjs`、根包公开 API | `tools/test_cli.py`、`tools/test_file_faults.py`、`tools/test_consumer.py` |
| 测试、README 示例和可重建交付 | `tools/`、`docs/` | `tools/prepare_submission.py`；从源码包解压后重建 |
| 公开开发记录、参考说明、许可证 | Git 提交 / PR、`docs/REFERENCES.md`、`LICENSE` | 仓库提交记录、来源文档与 MIT 许可证 |

表中的源码路径以仓库根目录为起点。对应申报时的 54 个核心测试，当前已有 104 个测试；同一套用例分别在 JS 和 wasm-gc 执行。具体结果使用提交包内本次运行的报告，而非仅依据表中列出的测试文件。

## 五分钟演示

1. 打开离线工作台，展示默认双端口陷波样例，切换 S21 / S11 与线性 / 对数频率轴。
2. 用曲线、滑块或方向键选择频点，展示原始复数值、分贝和相位；切换参数时保留同一频点。
3. 导入一份单端口文件，说明频率单位和参考阻抗，分别导出 CSV 和 JSON。
4. 载入错误样例并定位字段，修改或重新导入后恢复；演示错误输入不能继续导出旧结果。
5. 展示独立库接入、两套后端测试和数值对照报告；说明浏览器与 CLI 共用 MoonBit 核心。

可手算样例、命令和输出说明见 [使用指南](GETTING_STARTED.md) 与 [验收指南](ACCEPTANCE.md)。

## 交付文件

`tools/prepare_submission.py` 通过全部检查后生成统一提交包：

- `workbench/`：离线页面、CLI、合成样例和运行包校验清单。
- `source/`：与本次测试一致、可独立重建的源码和项目文档。
- `reports/`：本次执行的 JSON 报告、命令日志和界面截图。
- 根目录 `README.md`：评审入口；`manifest.json` 与 `verify_download.py`：文件核对工具。

代码采用 MIT 许可证。格式与数据来源见 [参考资料](REFERENCES.md) 和 [测试数据说明](TEST_DATA.md)。AI 辅助用于编码、测试和文档整理，主要实现与技术选择可按源码和开发记录说明。

格式支持仍以 [兼容性说明](COMPATIBILITY.md) 为准；本次不增加多端口、Touchstone 2.0、仪器控制、校准或去嵌入。Mooncakes 发布另行准备，现有交付可直接通过源码工作区使用核心库。
