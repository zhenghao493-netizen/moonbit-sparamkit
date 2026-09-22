# MoonBit SParamKit

[![Verify SParamKit](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml)
[![Build SParamKit Tool](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml)
[![Package verification](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/package.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/package.yml)
[![Cross-platform delivery](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/platforms.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/platforms.yml)

MoonBit 原生的一端口、二端口 Touchstone S 参数解析、数值表示归一化与离线可视化工具。

**版本：`0.1.0-dev.5`，开发预览。尚未发布 Mooncakes，也不是完整标准兼容性认证或比赛验收结论。** 这里的归一化指频率单位及 RI/MA/DB 表示转换，不是将任意参考阻抗转换为 50 Ω。

## 直接体验

在成功的 [工具构建运行](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35748629493) 中下载 `sparamkit-tool`，解压后打开 `index.html`。获取 Actions 附件可能需要登录 GitHub；下载后的工作台不需要登录、安装 MoonBit 或联网。附件保留 30 天，之后可从源码重建。未部署 GitHub Pages。

选择、拖入 `.s1p` / `.s2p` 或粘贴文本，切换 S11 / S21 / S12 / S22 与线性/对数频率轴，查看幅度、相位曲线并导出全量 CSV / JSON。分页不截断导出；内置 RC / RLC 样例为合成数据。

自包含 HTML 无在线 API、外部字体和遥测。Blob Worker 调用实际编译的 MoonBit 核心；JavaScript 只处理文件、消息、界面和绘图。输入变更或解析失败会清空旧曲线、禁用导出。同一文件可再次选择；旧的异步请求不会覆盖新输入的结果或解锁仍在进行的新分析。

首次使用见 [试用与交付说明](docs/GETTING_STARTED.md)。完整运行包另有 `manifest.json` 和 `verify_download.py`，Python 可检查包内文件是否一致；校验和不是数字签名。单独保存 HTML 的使用不需要 Python。

## 当前验证与修正

继续“MoonBit 数据处理核心＋离线工具”的定位，不扩成射频仿真平台。保留 dev.4 的 `! Port Impedance` 一致性保护：仅接受与头部 R 完全一致的单行逐端口纯实数声明；冲突、复阻抗、不完整或歧义形式返回带位置的 `UnsupportedMetadata`。这不是通用 HFSS 导入或阻抗重归一化。

本轮修正同文件重复导入、异步分析按钮状态和重复 CSV 操作，统一构建文本与测试子进程的 UTF-8 编码，并增加可核对的版本和文件清单。核心算法及 86 个 MoonBit 单元用例保持不变。

| 实际验证层 | 结果 |
| --- | --- |
| MoonBit JS / wasm-gc | 各 86/86；严格类型检查、构建、示例通过 |
| Windows | 实际运行 PowerShell 验证脚本、源码包重建和文件 CLI；默认 cp1252、UTF-8 模式关闭时中文测试通过 |
| 浏览器 | Linux Chromium / Firefox / WebKit、Windows Chromium，各 22 项本地文件场景通过 |
| CLI 与运行包 | 14 组检查；11 个运行包文件的哈希校验通过 |
| 独立数值回归 | 77 份合成文件 / 4398 个复数值，以及 2 份公开样例 / 141 个复数值通过 |
| 源码包 | 49 个文件，独立解压后重建、测试和工作台生成通过 |

证据、实际浏览器版本、提交和运行标识见 [DELIVERY.md](verification/DELIVERY.md)。这是同一套用例在不同环境重复执行，不虚增独立用例数；WebKit 测试不等于苹果 Safari，390px 视口不等于手机真机。历史记录见 [METADATA_GUARD.md](verification/METADATA_GUARD.md)、[HARDENING.md](verification/HARDENING.md) 和 [STATUS.md](verification/STATUS.md)。

## 从源码构建

准备官方 MoonBit 工具链、Node.js 22 和 Python 3.11+：

```bash
git clone https://github.com/zhenghao493-netizen/moonbit-sparamkit.git
cd moonbit-sparamkit
bash tools/verify.sh
moon build bridge --target js --release --deny-warn
python tools/build_web.py
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format json
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format csv > result.csv
python dist/verify_download.py
python tools/test_host.py
python tools/check_package.py
```

浏览器打开 `dist/index.html`。CLI 默认从 `.s1p` / `.s2p` 后缀识别端口；其他后缀用 `--ports 1` 或 `--ports 2`。退出码：0 成功；1 解析失败（结构化 JSON）；2 文件或参数错误（标准错误输出）。`cmd/main` 是内置 CSV 示例，文件 CLI 是 `dist/cli.cjs`。Windows 可用 PowerShell 运行 `./tools/verify.ps1`，再执行上面相同的构建与 Python / Node 命令；该脚本已在云端 Windows 验证。

## 核心 API

- `parse_touchstone(text, ports)` 返回 `Result[Network, Diagnostic]`，显式指定 1 / 2 端口。
- `Network::get_s(sample_index, output_port, input_port)`：样本索引从 0、端口从 1 开始。
- `Complex::magnitude`、`magnitude_db`、`phase_degrees`；零幅度的有限 dB 和相位为 `None`，JSON 为 `null`。
- `Network::to_csv` 导出全量长表；`analyze_touchstone_json`、`export_touchstone_csv_json` 是浏览器/CLI 共用的带版本号 JSON 接口。

在本地工作区其他包的 `moon.pkg` 导入 `"ttxiangshang/sparamkit" @sparam` 后：

```moonbit nocheck
let text = "# GHz S RI R 50\n1 0.1 0 0.8 -0.1 0.7 -0.2 0.2 0\n"
match @sparam.parse_touchstone(text, 2) {
  Ok(network) => println(network.to_csv())
  Err(error) => println("line \{error.line}:\{error.column}: \{error.message}")
}
```

尚未发布，不要假设 `moon add` 已可用。

## 支持边界

仅明确限定的 Touchstone 1.x 一/二端口 S 参数、单一有限正实数参考阻抗。二端口顺序为 S11、S21、S12、S22。要求一个 `#` 选项行；缺省 GHz / S / MA / 50 Ω；频率非负、严格递增；每条逻辑记录从新行开始，可跨行。支持 LF/CRLF/CR、一个初始 BOM、注释、科学计数法、RI/MA/DB 及四种频率单位。

不支持 2.0 关键字、多端口、Y/Z/H/G、噪声块、仪器控制、校准、去嵌入、任意厂商元数据或阻抗重归一化。已识别 `Port Impedance` 只做一致性保护，未知标签仍可能按普通注释处理。完整限制见 [COMPATIBILITY.md](docs/COMPATIBILITY.md)。

核心上限 8 Mi UTF-16 code units / 100000 样本；交互 JSON 上限 2 Mi code units / 20000 样本；文件上限 2 MiB UTF-8。非法数值、溢出、非零十进制数下溢为零时报错。公开结构可由外部构造，解析器保证不自动适用于这些外部数据。

对数轴只在图上省略 0 Hz；表格与导出保留。相位为主值，不跨 ±180° 跳变连线，不做展开、插值或平滑。

## 独立核验与交付

```bash
python -m pip install scikit-rf==1.8.0 numpy==2.2.6 scipy==1.15.3 playwright==1.55.0
python -m playwright install chromium
python tools/crosscheck.py
python tools/test_measured.py
python tools/test_browser.py
```

先构建 `dist/`；Linux 可能还需要 Playwright 系统依赖。可额外安装 Firefox / WebKit，并设置 `BROWSER_NAME=firefox` 或 `BROWSER_NAME=webkit` 运行同一浏览器脚本；完整步骤见 `.github/workflows/platforms.yml`。

公开样例的版本、内容哈希、来源与限定见 [TEST_DATA.md](docs/TEST_DATA.md)。上游标注的测量样例不是本项目重新采集的数据。复现步骤见 [ACCEPTANCE.md](docs/ACCEPTANCE.md)。源包验证不等于已发布 Mooncakes。

Android / iOS 真机、苹果 Safari、macOS 及外部用户独立试用仍未完成；自动化测试不替代这些验证。

## 独立性与来源

本项目独立于 WaveKit 音频、CalendarKit 日历和 PixelKit 寻路，不通过改名或拆分旧项目构成本期成果。Python/scikit-rf 仅用于构建或独立测试，不是运行时解析器，不复制其解析器源码。AI 辅助用于实现、测试和文档，参赛者负责理解、审阅与交付质量。

[参考资料](docs/REFERENCES.md) · [MIT 许可证](LICENSE)。
