# MoonBit SParamKit

[![Verify SParamKit](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml)
[![Build SParamKit Tool](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml)
[![Package verification](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/package.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/package.yml)

MoonBit 原生的一端口、二端口 Touchstone S 参数解析、数值归一化与离线可视化工具。

**版本：`0.1.0-dev.3`，开发预览。尚未发布到 Mooncakes，不是完整标准兼容性认证或比赛验收结论。**

## 直接体验

在成功的 [工具构建运行](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/web.yml) 中下载 `sparamkit-tool`，解压后用现代浏览器打开 `index.html`。获取 Actions 附件可能需要登录 GitHub；下载后的工作台不需要登录、安装 MoonBit 或联网。附件保留 30 天，之后可从源码重建。

选择或拖入 `.s1p` / `.s2p` 文件，或粘贴文本；切换 S11 / S21 / S12 / S22、线性或对数频率轴，查看幅度和相位曲线，再导出全部 CSV / JSON 数据。表格分页不截断导出。内置 RC / RLC 样例全部为合成数据。

工作台是自包含单 HTML，无在线 API、外部字体或遥测。Blob Web Worker 调用实际编译的 MoonBit 核心；JavaScript 只处理文件、消息、界面和绘图。编辑输入或解析失败后清空旧图表并禁用旧结果导出，避免混用结果。未部署 GitHub Pages。

## 本轮完善

- 支持 LF、CRLF、纯 CR 及混合换行，保留诊断的物理行号。
- 接受文件开头单个 BOM；嵌入或重复 BOM 不会被静默吞掉。
- 新增 18 个回归测试，共 72 个；同一套用例在 JS / wasm-gc 各执行一次。
- 增加格式化门禁、生成 API 一致性检查、发布源包检查及全新目录重建测试。
- 增加两份来源和内容哈希锁定的公开样例对照，不将其混作自建合成数据。
- 构建器缺少当前编译入口时明确失败，不再回退到旧 `dist/core.cjs`。

历史验证及具体提交见 [verification/STATUS.md](verification/STATUS.md)；本轮结果见 [verification/HARDENING.md](verification/HARDENING.md)。测试通过只说明对应提交在记录的输入和环境下通过，不代表任意仪器或浏览器兼容。

## 从源码构建

准备官方 MoonBit 工具链、Node.js 22 和 Python 3.11+：

```bash
git clone https://github.com/zhenghao493-netizen/moonbit-sparamkit.git
cd moonbit-sparamkit
bash tools/verify.sh
moon build bridge --target js --release --deny-warn
python tools/build_web.py
```

打开 `dist/index.html`。文件 CLI 使用同一编译产物：

```bash
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format json
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format csv > result.csv
node dist/cli.cjs input.txt --ports 1 --format json
python tools/test_host.py
```

CLI 退出码：0 成功；1 解析失败（标准输出为结构化 JSON）；2 文件或参数错误（标准错误输出）。`cmd/main` 仍是内置 CSV 示例，文件 CLI 是 `dist/cli.cjs`。Windows 的 `tools/verify.ps1` 已同步格式化门禁，但未做 Windows 实机验证。

## 核心 API

- `parse_touchstone(text, ports)`：显式指定 1 / 2 端口；处理选项、注释、换行、科学计数法及跨行记录。
- Hz / kHz / MHz / GHz 统一为 Hz；RI / MA / DB 统一为复数实部、虚部。
- `Network::get_s(sample_index, output_port, input_port)`：样本索引从 0、端口从 1 开始。
- `Complex::magnitude`、`magnitude_db`、`phase_degrees`。
- `Network::to_csv`：导出全部参数长表。
- `analyze_touchstone_json`、`export_touchstone_csv_json`：浏览器与 CLI 共用的带版本号、资源限制及结构化错误的接口。

在本地工作区其他包的 `moon.pkg` 中导入 `"ttxiangshang/sparamkit" @sparam`：

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

尚未发布；不要假设 `moon add` 已可用。

## 格式范围与资源限制

完整对照见 [兼容性表](docs/COMPATIBILITY.md)，包括标准规则、主动收紧的策略和扩展行为。

- 仅 Touchstone 1.x 一端口、二端口 S 参数，单一有限正实数参考阻抗；二端口顺序为 **S11、S21、S12、S22**。
- 数据前要求一个 `#` 选项行；省略选项默认 GHz / S / MA / 50 Ω。重复选项行会报错，这是比规范更严格的策略。
- 每条逻辑记录从新行开始，可延续到后续行；频率非负、严格递增，不自动排序、去重或插值。
- 不支持噪声块、版本 2 关键字、多端口、Y/Z/H/G、仪器控制、校准或去嵌入。
- `! Port Impedance` 等厂商注释不解释；不能用于依赖这些注释表示复数或各端口不同阻抗的文件。
- 非有限数和非零十进制数下溢为零时报错。零复数的有限 dB 和相位为 `None` / JSON `null`，不是 0。
- 核心文本限制：8 Mi UTF-16 code units、默认 100000 样本、每行 16 字段、每字段 128 code units；JSON 接口限制为 2 Mi code units / 20000 样本，浏览器及 CLI 文件限制为 2 MiB UTF-8。
- 一次性文本解析，不是流式接口；初始 BOM 属于编码兼容扩展。公开结构可自行构造，解析结果约束不自动适用于任意外部构造值。
- 对数轴只在绘图时省略 0 Hz，表格和导出保留；相位主值跨越 ±180° 时不连线，不做相位展开。

## 独立测试与源包验证

```bash
python tools/check_package.py
python -m pip install scikit-rf==1.8.0 numpy==2.2.6 scipy==1.15.3 playwright==1.55.0
python -m playwright install chromium
python tools/crosscheck.py
python tools/test_measured.py
python tools/test_browser.py
```

源包检查会实际创建 ZIP、检查文件和许可证、在全新目录重建并重跑两后端测试及文件 CLI，**不会发布包**。浏览器测试需先构建 `dist/`，Linux 可能需额外安装 Playwright 系统依赖。CI 失败时保留日志，不上传声称成功的工具包。

77 份合成输入与两份上游标记为测量的公开文件分开记录。后者不是本项目重新采集的实验数据，也不是仪器准确度认证。原始文件来源、哈希与上游说明的限制见 [测试数据来源](docs/TEST_DATA.md)。评审完整复现步骤见 [验收指南](docs/ACCEPTANCE.md)。

Android / iOS 真机、Safari、更多仪器厂商扩展仍待验证。赛事方选题审核、报名和 Mooncakes 发布与上述工程测试相互独立。

## 独立性与来源

独立新编写的 MoonBit 实现，不包含或拆分 WaveKit、CalendarKit 或 PixelKit 的代码。AI 辅助实现、测试与文档，参赛者负责理解、审阅和质量。Python / scikit-rf 仅用于构建或独立测试，不作为运行时解析器；未复制其解析器源代码，也未将上游样例放进本项目发布包。参考见 [docs/REFERENCES.md](docs/REFERENCES.md)。项目代码采用 MIT 许可证。
