# MoonBit SParamKit

[![Verify SParamKit](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml)
[![Build SParamKit Tool](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml)

MoonBit 原生的一端口、二端口 Touchstone S 参数解析、数值归一化与离线可视化工具。

**状态：已有可运行的离线工作台与文件 CLI，仍为开发预览，尚未发布 Mooncakes，也不是完整标准兼容性认证或比赛验收结论。**

## 直接体验

在 [已验证的工具构建运行](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35732045186) 中获取 `sparamkit-tool` artifact，解压后用现代浏览器打开 `index.html`。下载 GitHub Actions artifact 可能需要登录 GitHub；下载并解压后的工作台不需要登录或联网。该运行的附件保留 30 天，之后可从源码重建。

打开后自动显示合成的双端口陷波网络。可以选择本地 `.s1p` / `.s2p` 文件、拖入文件或粘贴文本；切换 S11 / S21 / S12 / S22、线性或对数频率轴，查看幅度和相位曲线，再导出 CSV / JSON。表格分页只影响屏幕显示，导出仍包含全部采样点和参数。

这是自包含的单 HTML 文件，不调用在线 API、不使用外部字体、不发送遥测。页面使用 Blob Web Worker 调用实际编译的 MoonBit 核心；JavaScript 只处理文件、消息、界面和绘图。编辑输入或解析失败后会清空旧图表并禁用旧结果导出。

已用 Chromium 验证本地 `file://` 打开、文件选择、导出及 390px 响应式布局；尚未做 Android/iOS 真机、Safari 或所有浏览器验证。项目尚未部署 GitHub Pages。

## 当前验证结果

代码提交 `0b34674c33134c446d16128ccd043305e2e386d8` 于 2026-09-22 已通过：

| 验证层 | 实际结果 |
| --- | --- |
| MoonBit JS | check、build、54/54 tests、内置 CSV 示例，全部启用 `--deny-warn` |
| MoonBit wasm-gc | check、build、54/54 tests、内置 CSV 示例，全部启用 `--deny-warn` |
| 独立数值对照 | scikit-rf 1.8.0，77 份合成文件、4398 个复数参数值及 CSV 导出对照通过 |
| 浏览器交互 | Chromium 本地文件模式，15 项场景检查通过 |

同一套 54 个用例分别运行在两个后端，不是 108 个独立用例。独立对照覆盖双方共同支持的合成数据子集，不代表全部格式、极端数值或真实仪器测量均已验证。详细证据、运行链接、版本和限制见 [verification/STATUS.md](verification/STATUS.md)。

## 构建离线工作台与 CLI

先安装 [MoonBit 官方工具链](https://www.moonbitlang.com/download/)，准备 Python 3 和 Node.js 22：

```bash
git clone https://github.com/zhenghao493-netizen/moonbit-sparamkit.git
cd moonbit-sparamkit
bash tools/verify.sh
moon build bridge --target js --release --deny-warn
python tools/build_web.py
```

浏览器打开生成的 `dist/index.html`。文件输入 CLI 使用相同的编译产物：

```bash
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format json
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format csv > result.csv
node dist/cli.cjs input.txt --ports 1 --format json
```

CLI 主机包装只负责文件读取与参数处理，解析、转换和 CSV 序列化由 MoonBit 完成。退出码：0 成功；1 输入未通过解析（标准输出为结构化 JSON）；2 文件或命令参数错误（标准错误输出）。`cmd/main` 仍是内置合成 CSV 示例，不是文件输入 CLI。

## MoonBit 核心 API

- `parse_touchstone(text, ports)`：调用方明确给出 1 或 2 个端口；支持选项行、注释、CRLF、科学计数法与跨行记录。
- Hz/kHz/MHz/GHz 归一化到 Hz；RI/MA/DB 归一化到实部/虚部。
- `Network::get_s(sample_index, output_port, input_port)` 查询；端口从 1 开始，样本索引从 0 开始。
- `Complex::magnitude`、`magnitude_db`、`phase_degrees`；零幅度没有有限 dB 值或定义好的相位。
- `Network::to_csv` 导出全部参数的长表。
- `analyze_touchstone_json`、`export_touchstone_csv_json`：浏览器与 CLI 共用的受限、带版本号 JSON 边界。

在本地工作区的其他包导入 `"ttxiangshang/sparamkit" @sparam` 后：

```moonbit nocheck
let text = "# GHz S RI R 50\n1 0.1 0 0.8 -0.1 0.7 -0.2 0.2 0\n"
match @sparam.parse_touchstone(text, 2) {
  Ok(network) => {
    let s21 = network.get_s(0, 2, 1).unwrap()
    println(s21.magnitude())
    println(network.to_csv())
  }
  Err(error) => println("line \{error.line}:\{error.column}: \{error.message}")
}
```

尚未发布到 Mooncakes；请从仓库构建，不要假设 `moon add` 已可用。

## 明确的支持边界

这是严格子集，不是完整 Touchstone 标准实现：

- 数据前要求一个 `#` 选项行；省略的选项取 GHz / S / MA / 50 Ω 默认值。
- 仅一端口、二端口 S 参数及单一正实数参考阻抗；二端口文件顺序为 **S11、S21、S12、S22**。
- 每条逻辑记录从新行开始，可延伸至后续行；频率非负且严格递增，不自动排序、去重或插值。
- 不支持噪声参数块、版本 2 关键字、多端口、Y/Z/H/G 参数、仪器控制、校准或去嵌入。
- 非有限输入及非零十进制数下溢为零时报错；零复数的相位和有限 dB 为 `None`，JSON 报告写作 `null`，不伪装为 0。
- 底层文本解析上限 8 Mi UTF-16 code units，默认最多 100000 样本；每行最多 16 个 token，每个 token 最多 128 code units。
- JSON 交互接口进一步限制为 2 Mi UTF-16 code units、20000 样本；浏览器和 CLI 文件输入另外限制为 2 MiB UTF-8 文件。
- 一次性文本解析，不是流式接口；不自动处理 BOM；公开结构可由调用方构造，解析成功约束不自动适用于任意外部构造值。
- 对数频率轴省略 0 Hz 点，但表格与导出保留；相位主值跨越 ±180° 时不连线；不做相位展开。

`samples/` 和内置 RC / RLC 演示均为合成数据，不是真实仪器测量。测试通过不等于测量准确性认证。

## 重现独立核验

```bash
python -m pip install scikit-rf==1.8.0 numpy==2.2.6 scipy==1.15.3 playwright==1.55.0
python -m playwright install chromium
python tools/crosscheck.py
python tools/test_browser.py
```

先按上文构建 `dist/`。Linux 上可能需要 Playwright 的系统依赖。工具工作流会保存 JSON 报告、逐步日志与截图，数值或浏览器测试失败时不会上传成功工具附件。

Windows 的 `tools/verify.ps1` 尚未实机验证。格式化门禁、发布包验证、代表性真实仪器数据、完整规范兼容表、赛事方选题审核和报名仍待完成。

## 独立性与来源

本项目是独立新编写源码，不包含或拆分 WaveKit 音频、CalendarKit 日历或 PixelKit 寻路代码。AI 辅助用于实现、测试和文档，参赛者仍需理解并审阅成果。Python/scikit-rf 仅用于独立测试，不是运行时解析器，也不复制其源码。

参考资料见 [docs/REFERENCES.md](docs/REFERENCES.md)。MIT 许可证。
