# 在 MoonBit 项目中使用 SParamKit

SParamKit 的公开接口可在独立 MoonBit 模块中使用。当前可以用本地工作区接入源码，无需先发布到 Mooncakes。

## 工作区结构

准备两个并列目录：

```text
workspace/
├── moon.work
├── moonbit-sparamkit/    # 本项目源码
└── client/
    ├── moon.mod
    ├── moon.pkg
    └── main.mbt
```

`moon.work`：

```moonbit
members = ["moonbit-sparamkit", "client"]
```

`client/moon.mod`：

```moonbit
name = "example/sparamkit-client"

import {
  "ttxiangshang/sparamkit@0.1.0-dev.8",
}
```

`client/moon.pkg`：

```moonbit
import {
  "ttxiangshang/sparamkit" @sparam,
}

pkgtype(kind: "executable")
```

MoonBit 工作区将模块依赖解析到本地成员。版本号随项目更新调整，工作区接入方式见 [MoonBit 模块配置](https://docs.moonbitlang.com/en/latest/toolchain/moon/module.html#dependency-management)。

## 查询与导出

`client/main.mbt`：

```moonbit
fn main {
  let text = "# Hz S RI R 50\n1 .3 -.4\n2 0 0\n"
  match @sparam.parse_touchstone(text, 1) {
    Ok(network) => {
      let value = network.get_s(0, 1, 1).unwrap()
      println(value.magnitude())
      println(network.to_csv())
    }
    Err(error) =>
      println("line \{error.line}:\{error.column}: \{error.message}")
  }
}
```

在 `client/` 中执行：

```bash
moon check . --target js --deny-warn
moon run . --target js --deny-warn
moon run . --target wasm-gc --deny-warn
```

样例先输出幅度 `0.5`，随后输出两个频点的 CSV。样本索引从 0 开始，端口号从 1 开始；对于双端口文件，`get_s(0, 2, 1)` 取得第一个频点的 S21。

`magnitude_db()` 和 `phase_degrees()` 返回可选值；零幅度时为 `None`。需要 JSON 时可调用 `analyze_touchstone_json(text, ports)`，失败结果也包含结构化诊断。完整接口见 [pkg.generated.mbti](../pkg.generated.mbti)。

## 接入测试

仓库中的测试脚本会创建全新的工作区，将核心库作为独立模块依赖接入，并在 JS 和 wasm-gc 上检查、编译、测试和运行：

```bash
python tools/test_consumer.py
```

该脚本包含五个公开 API 用例，覆盖解析与幅度、非对称双端口查询、诊断与样本限制、CSV / JSON 导出和零值处理。源码包重建测试也会执行同一流程。
