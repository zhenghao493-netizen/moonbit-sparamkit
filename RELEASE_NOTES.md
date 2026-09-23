# SParamKit 0.1.0

MoonBit 原生的 Touchstone 文件解析、检查与离线分析工具，面向一端口和二端口 S 参数数据。

## 下载

- **SParamKit-0.1.0-submission.zip**：完整交付包，包含离线工作台、源码、使用文档、演示讲稿和本次测试报告。完整解压后打开根目录 `index.html`。
- **SParamKit-0.1.0.html**：单文件离线工作台，保存后用桌面浏览器打开。
- **SHA256SUMS.txt**：上述文件的 SHA256 校验值。

## 功能

支持 RI / MA / DB、四种频率单位、结构化错误诊断、S 参数逐点读数和全量 CSV / JSON 导出。文件 CLI 与浏览器共用 MoonBit 核心；库可通过源码工作区接入其他 MoonBit 项目。

本版沿用 RC3 已终检的实现，统一正式版本和交付文档。核心库包含 104 个测试；完整测试日志、独立数值对照和源码包重建结果随交付包提供。

## 使用范围

读取 Touchstone 1.x 的一端口、二端口 S 参数子集，各端口共用文件头指定的正实数参考阻抗。工作台和文件 CLI 支持不超过 2 MiB、20,000 个频点的 UTF-8 文件。完整规则见源码中的 `docs/COMPATIBILITY.md`。

采用 MIT 许可证。Mooncakes 发布另行安排，本次提供 GitHub 交付文件与源码。
