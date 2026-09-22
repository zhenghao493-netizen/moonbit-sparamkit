# 参考来源

核对日期：2026-09-22。以下资料用于格式语义、API 签名和工具链用法核对，未复制第三方 Touchstone 解析器源码。

- Keysight SnP File Format：https://helpfiles.keysight.com/csg/N1930xB/FilePrint/SnP_File_Format.htm
- MoonBit 官方构建系统教程：https://docs.moonbitlang.com/en/latest/toolchain/moon/tutorial.html
- 官方安装入口：https://www.moonbitlang.com/download/
- string API：https://github.com/moonbitlang/core/blob/main/string/pkg.generated.mbti
- math API：https://github.com/moonbitlang/core/blob/main/math/pkg.generated.mbti
- builtin API：https://github.com/moonbitlang/core/blob/main/builtin/pkg.generated.mbti

尚待完成：逐条对照 IBIS Touchstone 规范形成兼容性表，以及与 scikit-rf 在共同支持子集上的独立交叉验证。两者不能以测试定义数量替代。
