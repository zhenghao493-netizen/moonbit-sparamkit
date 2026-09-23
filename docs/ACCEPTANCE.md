# SParamKit 演示与验收指南

本页提供项目演示步骤和测试命令。所有命令从仓库根目录执行，构建依赖为 MoonBit 工具链、Node.js 22 和 Python 3.11+。

## 完整验收与提交包

准备上述构建依赖，以及独立对照和浏览器测试依赖：

```bash
python -m pip install scikit-rf==1.8.0 numpy==2.2.6 scipy==1.15.3 playwright==1.55.0
python -m playwright install chromium
python tools/prepare_submission.py
```

Linux 如缺少浏览器系统依赖，使用 `python -m playwright install --with-deps chromium`。Git 工作区先提交改动；完整验收期间不要修改源码。

全部检查通过后，`_build/submission/` 中生成 `SParamKit-<版本>-submission.zip`。解压后直接打开 `workbench/index.html`。包中另有 `source/`、`reports/`、演示说明和整体文件清单。执行 `python verify_download.py` 可核对解压后的文件。

检查失败时不生成成功提交包；原因保存在 `_build/submission/submission-check.json`，失败命令日志为 `failed-step.log`。完整验收会实际打开本地 HTML，不使用注入页面替代此项检查。

[申报功能对应表](SUBMISSION.md) 提供逐项实现与演示入口。下面的命令用于单独复现各检查阶段。

## 1. 构建与演示

```bash
git clone https://github.com/zhenghao493-netizen/moonbit-sparamkit.git
cd moonbit-sparamkit
moon build bridge --target js --release --deny-warn
python tools/build_web.py
```

打开 `dist/index.html`，按以下顺序演示：

1. 查看默认双端口陷波样例，切换 S21 / S11 和线性 / 对数频率轴。
2. 切换单端口 RC 负载，查看频点数、参考阻抗和相位曲线。
3. 导入本地 `.s1p` / `.s2p`，分别导出 CSV 和 JSON。
4. 编辑输入，确认旧曲线和导出已清空；加载“错误诊断样例”查看行列位置，再切回正常样例。

可手算核对的两点样例见 [使用指南](GETTING_STARTED.md)。浏览器和 CLI 共用 MoonBit 编译核心；工作台离线运行，内置 RC / RLC 样例为合成数据。

文件 CLI 示例：

```bash
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format json
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format csv -o result.csv
```

## 2. 核心与交互测试

```bash
bash tools/verify.sh
python tools/test_host.py
python tools/test_distribution.py
```

Windows 下用 `./tools/verify.ps1` 替换第一条命令。

核心脚本运行格式检查，以及 JS / wasm-gc 的类型检查、构建、单元测试和内置示例，并启用 `--deny-warn`。主机测试覆盖文件 CLI、错误路径、中文路径、运行包完整性和旧构建产物保护。

运行独立数值与浏览器测试：

```bash
python -m pip install scikit-rf==1.8.0 numpy==2.2.6 scipy==1.15.3 playwright==1.55.0
python -m playwright install chromium
python tools/crosscheck.py
python tools/test_measured.py
python tools/test_browser.py
python tools/test_numeric_browser.py
python tools/test_numeric.py
python tools/test_consumer.py
```

Linux 如缺少浏览器系统依赖，可使用 `python -m playwright install --with-deps chromium` 安装。其他浏览器环境的执行方式见 [跨平台工作流](../.github/workflows/platforms.yml)。

| 脚本 | 核验内容 |
| --- | --- |
| `tools/crosscheck.py` | 与 scikit-rf 对照频率、参考阻抗、复数值、幅度、相位和 CSV 导出 |
| `tools/test_measured.py` | 核对固定版本的公开样例及其来源哈希，比较解析结果 |
| `tools/test_browser.py` | 在本地文件模式下检查导入、绘图、导出、错误恢复和异步交互 |

结果与日志保存在 `verification/`。测试数据的构成和来源见 [TEST_DATA.md](TEST_DATA.md)，各阶段运行记录见 [verification/](../verification/)；统一提交包的本次结果见包内 `reports/submission-check.json`。

## 3. 源码包重建

```bash
python tools/check_package.py
```

脚本生成源码包，检查文件路径、必要资源、许可证、格式和公共 API 定义，再解压到临时目录，重新运行两个目标的检查、构建与测试。最后构建桥接入口和工作台，并执行文件 CLI。

运行包的文件一致性可另行检查：

```bash
python dist/verify_download.py
```

## 4. 项目资料

| 文档 | 内容 |
| --- | --- |
| [README](../README.md) | 项目简介、功能与快速上手 |
| [使用指南](GETTING_STARTED.md) | 文件导入、曲线查看、导出与常见错误 |
| [兼容性说明](COMPATIBILITY.md) | 格式子集、输入限制、阻抗及绘图约定 |
| [参考资料](REFERENCES.md) | 格式与工具链资料 |
| [测试数据说明](TEST_DATA.md) | 合成数据、公开样例及来源 |
| [测试记录](../verification/) | 已执行的测试、环境、提交和构建标识 |

测试结果按记录中的版本与环境核对；项目功能范围以兼容性说明为准。
