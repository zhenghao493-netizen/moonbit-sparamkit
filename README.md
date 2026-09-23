# MoonBit SParamKit

[![Tests](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml)
[![Workbench](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml)
[![Package](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/package.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/package.yml)
[![Platforms](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/platforms.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/platforms.yml)

SParamKit 是一个用 MoonBit 编写的射频网络参数工具，支持 `.s1p`、`.s2p` 文件的解析、检查和可视化。导入文件后，可以查看 S 参数的幅度、相位曲线，并将结果导出为 CSV 或 JSON。

项目包含可复用的 MoonBit 核心库、离线浏览器工作台和命令行工具，适用于射频实验教学、文件检查和本地数据分析。

版本：`0.1.0-dev.8` · [使用指南](docs/GETTING_STARTED.md) · [演示与验收](docs/ACCEPTANCE.md) · [格式支持](docs/COMPATIBILITY.md)

## 功能

- **文件解析**：读取一端口、二端口 Touchstone 数据，支持注释、科学计数法、跨行记录和常见换行格式。
- **数值处理**：统一 Hz / kHz / MHz / GHz 单位，转换 RI / MA / DB 表示，提供复数值、幅度、分贝和相位查询。
- **数据检查**：定位非法选项、不完整记录、频率顺序和已识别的端口阻抗冲突，返回错误码、行列位置及原因，可一键选中错误字段。
- **离线工作台**：支持文件选择、拖放与文本粘贴，切换 S 参数和频率轴；通过曲线、滑块和方向键逐点读数，并查看分页数据表。
- **完整导出**：输出全部频点和参数的 CSV / JSON；浏览器与 CLI 使用同一套 MoonBit 核心。

## 快速体验

在 [工具构建页面](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml) 选择一次成功运行，从 **Artifacts** 下载 `sparamkit-tool`。解压后，用桌面浏览器打开 `index.html`。

工作台不需要安装 MoonBit、启动服务器或联网。首次打开会载入双端口陷波样例，也可以切换到单端口 RC 负载，或直接导入自己的文件。内置样例为合成电路数据。

选择 S11 / S21 / S12 / S22 查看曲线，按需切换线性或对数频率轴，再点击 CSV 或 JSON 导出。编辑输入后重新解析即可。逐点查看和错误定位的操作见 [曲线读数指南](docs/WORKBENCH.md)。

## 从源码构建

准备 [MoonBit 工具链](https://www.moonbitlang.com/download/)、Node.js 22 和 Python 3.11+：

```bash
git clone https://github.com/zhenghao493-netizen/moonbit-sparamkit.git
cd moonbit-sparamkit
moon build bridge --target js --release --deny-warn
python tools/build_web.py
```

构建结果位于 `dist/`，浏览器打开 `dist/index.html` 即可使用。

### 命令行

```bash
# 读取双端口文件，输出 JSON
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format json

# 导出 CSV 到新文件
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format csv -o result.csv

# 非标准后缀的文件可手动指定端口数
node dist/cli.cjs input.txt --ports 1 --format json
```

CLI 根据 `.s1p` / `.s2p` 后缀识别端口数，也可用 `- --ports 1` 从标准输入读取。`-o` 将结果写入新的 UTF-8 文件，已有文件不会被覆盖。更多示例见 [命令行指南](docs/CLI.md)。

退出码为 `0`（成功）、`1`（数据检查失败）、`2`（文件或命令参数错误）。

### MoonBit API

在本地工作区的入口包中使用核心库，`moon.pkg` 配置如下。独立项目还需要配置模块依赖和 `moon.work`，完整步骤见 [库接入指南](docs/LIBRARY.md)：

```moonbit
import {
  "ttxiangshang/sparamkit" @sparam,
}

pkgtype(kind: "executable")
```

```moonbit
fn main {
  let text = "# GHz S RI R 50\n1 0.1 0 0.8 -0.1 0.7 -0.2 0.2 0\n"
  match @sparam.parse_touchstone(text, 2) {
    Ok(network) => {
      let s21 = network.get_s(0, 2, 1).unwrap()
      println(s21.magnitude())
      println(network.to_csv())
    }
    Err(error) =>
      println("line \{error.line}:\{error.column}: \{error.message}")
  }
}
```

`get_s(0, 2, 1)` 获取第一个频点的 S21：样本索引从 0 开始，端口从 1 开始。更多接口见 [API 定义](pkg.generated.mbti)。目前通过运行包或源码使用，Mooncakes 包列入后续发布计划。

## 格式支持

| 项目 | 支持范围 |
| --- | --- |
| 文件 | Touchstone 1.x 的一端口、二端口 S 参数子集 |
| 数值格式 | RI、MA、DB；频率单位为 Hz、kHz、MHz、GHz |
| 参考阻抗 | 各端口共用一个正实数参考阻抗，保留文件头的 R 值 |
| 文本 | UTF-8、LF / CRLF / CR 换行、一个开头 BOM、注释与科学计数法 |
| 工作台与 CLI 输入 | 文件不超过 2 MiB，最多 20,000 个频点 |

数据前需要 `#` 选项行，频率须非负且严格递增。二端口文件按 S11、S21、S12、S22 顺序读取。零幅度的分贝与相位在界面中留空，在 JSON 中记为 `null`。

暂不支持 Touchstone 2.0 关键字、多端口、噪声参数和阻抗重归一化。对识别到的 `Port Impedance` 声明会检查其与文件头是否一致；其他厂商扩展的处理方式、资源限制和绘图约定见 [兼容性说明](docs/COMPATIBILITY.md)。

## 开发与测试

```bash
# 核心检查、构建和测试（JS / wasm-gc）
bash tools/verify.sh

# 构建工作台后，运行 CLI 与运行包检查
python tools/test_host.py

# 检查源码包并在新目录中重新构建
python tools/check_package.py

# 在独立 MoonBit 项目中验证公开 API
python tools/test_consumer.py
```

Windows 下用 `./tools/verify.ps1` 运行核心检查，其余 Python / Node 命令相同。

核心库包含 96 个测试（含 10 个公开 API 黑盒测试），分别运行在 JS 和 wasm-gc 上。CI 还覆盖 scikit-rf 数值对照、公开文件样例、Windows / Linux 离线交互和源码包重建。复现方法见 [演示与验收指南](docs/ACCEPTANCE.md)，环境与结果见 [测试记录](verification/)。

解析、数值转换、诊断和数据导出在 MoonBit 中实现；`bridge/` 提供调用入口，`web/` 负责界面，`tools/` 包含 CLI 包装、构建和测试脚本。Python 与 scikit-rf 用于构建及测试。

## 项目与许可

本项目参加 2026 MoonBit 黑客松，方向为数据处理。开发中使用 AI 辅助编码、测试和文档整理，格式参考与测试数据来源分别见 [参考资料](docs/REFERENCES.md) 和 [测试数据说明](docs/TEST_DATA.md)。

采用 [MIT 许可证](LICENSE)。
