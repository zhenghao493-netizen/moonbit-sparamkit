# MoonBit SParamKit

[![Verify SParamKit](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml/badge.svg)](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/workflows/ci.yml)

MoonBit 原生的一端口、二端口 Touchstone S 参数解析与数值归一化工具库。

**状态：开发中。初次导入的源码尚待 GitHub Actions 编译验证，不是验收版或已发布的 Mooncakes 包。以具体提交的 Actions 日志为准。**

## 当前功能范围

- `parse_touchstone(text, ports)`：调用方明确给出 1 或 2 个端口。
- 选项行、注释、CRLF、科学计数法及跨行记录。
- Hz/kHz/MHz/GHz 归一化到 Hz；RI/MA/DB 归一化到实部/虚部。
- 参考阻抗、`get_s(sample_index, output_port, input_port)` 查询。
- 二端口顺序为 **S11、S21、S12、S22**，不是行优先顺序。
- 带行列位置的错误诊断，以及输入、样本和 token 限制。
- 幅度、有限 dB、相位计算及长表 CSV 输出。

`core_wbtest.mbt` 中有 40 个测试定义，`hardening_wbtest.mbt` 中有 6 个，总计 46 个。测试定义数不等于通过数。

## 复现

安装官方工具链：https://www.moonbitlang.com/download/

```bash
bash tools/verify.sh
```

或分别执行：

```bash
moon check --target wasm-gc
moon build --target wasm-gc
moon test --target wasm-gc
moon check --target js
moon build --target js
moon test --target js
moon run cmd/main --target js
```

Windows 可执行 `powershell -ExecutionPolicy Bypass -File tools/verify.ps1`。

`cmd/main` 目前只运行内置合成二端口样例并输出 CSV，**还不是文件输入 CLI**。
每次 push 的 CI 分别运行 JS 与 wasm-gc 检查，并保留日志附件。工作流只读代码，不发布包，不需要配置密钥。

## API 示例

在其他包的 `moon.pkg` 中导入 `"ttxiangshang/sparamkit" @sparam` 后：

```moonbit nocheck
let text = "# GHz S RI R 50\n1 0.1 0 0.8 -0.1 0.7 -0.2 0.2 0\n"
match @sparam.parse_touchstone(text, 2) {
  Ok(network) => {
    let s21 = network.get_s(0, 2, 1).unwrap()
    println(s21.magnitude())
    println(network.to_csv())
  }
  Err(error) => println(error)
}
```

尚未发布到 Mooncakes；请先从仓库本地运行，不要假设 `moon add` 已可用。

## 明确的支持边界

这是严格子集，不是完整 Touchstone 标准实现：

- 数据前要求一个 `#` 选项行；缺省选项为 GHz / S / MA / 50 Ω。
- 仅一端口、二端口 S 参数及单一正实数参考阻抗。
- 每条逻辑记录从新行开始，可延伸至后续行。
- 频率非负且严格递增，不自动排序或去重。
- 不支持噪声参数块、版本 2 关键字、多端口、Y/Z/H/G 参数。
- 非有限数值和非零十进制数下溢为零时返回错误。
- 零复数的相位和有限 dB 返回 `None`。
- 输入最多 8 Mi UTF-16 code units，每行最多 16 个 token，每个 token 最多 128 code units；默认最多 100000 样本。
- 一次性文本解析，不是流式接口；不自动处理 BOM。
- 公开结构可由调用方构造，解析成功的约束不自动适用于任意调用方构造的数据。

`samples/` 全部为合成样例，不是真实仪器测量。

## 后续工作

首先完成编译和测试修正；然后进行 scikit-rf 独立交叉核验、文件输入 CLI 和调用同一 MoonBit 核心的浏览器曲线页。
完整规范兼容性表、真实测量文件兼容性、赛事方选题审核及报名仍未完成。

## 独立性与来源

本项目是独立新编写源码，不包含或拆分 WaveKit 音频、CalendarKit 日历或 PixelKit 寻路代码。AI 辅助用于实现、测试和文档，参赛者仍需理解并审阅成果。
参考资料见 [docs/REFERENCES.md](docs/REFERENCES.md)。MIT 许可证。
