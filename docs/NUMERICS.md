# 数值计算说明

SParamKit 使用 MoonBit `Double` 存储频率、参考阻抗和复数参数。输入先解析为二进制双精度值，再转换单位和数值表示。CSV 保留归一化后的实部与虚部；JSON 在此基础上增加幅度、分贝和相位。

## 幅度与分贝

对于复数 `z = re + j·im`，幅度为 `hypot(re, im)`，分贝值为 `20·log10(|z|)`。

分贝计算不先构造线性幅度，而使用等价的缩放形式：

```text
high = max(abs(re), abs(im))
low  = min(abs(re), abs(im))
r = low / high

dB = 20·log10(high) + 10·ln(1 + r²) / ln(10)
```

其中 `ln(1 + r²)` 使用 `ln_1p`。这样既避免大分量的中间幅度溢出，也避免极小分量的幅度在舍入后丢失信息。

例如，实部与虚部均为 `1.7e308` 时，线性幅度超过 `Double` 范围，但分贝仍可表示，约为 `6167.619278384205`。JSON 中此时 `magnitude` 为 `null`，`db` 保留有限值。两分量均为最小正双精度值时，分贝约为 `-6463.114006905676`；对先舍入的幅度取对数会丢失约 `3.0103 dB`。

这些输入用于检查计算边界，不是随工具附带的射频测量样例。

## 零值与相位

实部和虚部都为零时，幅度为 `0`，有限分贝和相位无定义。MoonBit 可选接口返回 `None`，JSON 写入 `null`，界面显示空缺。

相位按 `atan2(im, re)` 转为度。工作台显示相位主值，跨越 ±180° 时断开曲线，不做相位展开。库调用者自行构造的非有限复数，其分贝和相位接口也返回 `None`。

## 数值回归

```bash
moon build bridge --target js --release --deny-warn
python tools/build_web.py
python tools/test_numeric.py
```

测试包含 1,024 组固定边界与带固定种子的随机有限复数组合，将同一批值分别放入一端口和二端口文件。独立 MoonBit 模块在 JS 和 wasm-gc 上输出 JSON / CSV，命令行输出再与当前源码结果核对。

参考结果使用 Python [Decimal](https://docs.python.org/3/library/decimal.html)，以 100 位有效数字计算 `10·log10(re² + im²)`。`Decimal.from_float` 按解析后的确切双精度值建立参考，避免把十进制输入到双精度的正常舍入混入分贝误差。

检查包括分贝、幅度、相位、参数次序以及实部和虚部的 JSON / CSV 往返。分贝绝对容差为 `1e-10 dB`，线性幅度容差为两个双精度间隔。报告写入 `verification/numeric-tests.json`，源码包独立重建时也运行此检查。

常规频率单位和 RI / MA / DB 转换另由 `tools/crosscheck.py` 与 scikit-rf 对照。数值回归不改变文件格式支持范围。
