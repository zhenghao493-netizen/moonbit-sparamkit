# SParamKit 命令行指南

文件 CLI 和浏览器工作台使用相同的 MoonBit 核心。以下命令在解压后的运行包目录执行，需要 Node.js 22。

## 常用命令

```bash
# 输出 JSON 到终端
node cli.cjs samples/synthetic_notch.s2p

# 保存 CSV，直接写入 UTF-8 文件
node cli.cjs samples/synthetic_notch.s2p --format csv --output result.csv

# 保存 JSON，-o 是 --output 的简写
node cli.cjs samples/synthetic_notch.s2p -o result.json

# 手动指定端口数
node cli.cjs input.txt --ports 2 --format csv -o result.csv

# 文件名以短横线开头时，用 -- 分隔选项与文件名
node cli.cjs --format json -- --antenna.s1p

# 查看帮助
node cli.cjs --help
```

在源码仓库中构建后，把命令中的 `cli.cjs` 改为 `dist/cli.cjs`，示例路径改为 `dist/samples/...`。

## 参数

| 参数 | 用途 |
| --- | --- |
| 输入文件 | 一个 `.s1p` 或 `.s2p` 文件；其他后缀需要指定端口数 |
| `--ports 1\|2` | 指定端口数，优先于文件后缀 |
| `--format json\|csv` | 输出格式，默认为 JSON |
| `--output FILE` / `-o FILE` | 保存到一个新文件；省略时使用标准输出 |
| `--` | 后面的内容按输入文件名处理 |

每项选项只能指定一次。路径包含空格时请加引号；输出文件名以短横线开头时，在路径前加 `./`，例如 `-o ./--result.csv`。

## 输出文件

`--output` 在解析成功后创建文件，统一使用 UTF-8、无 BOM。它不会覆盖已有文件，也不会自动创建父目录。输出到输入文件本身同样会被拒绝，原文件保持不变。文件写入失败时会尝试删除本次产生的不完整文件。

使用 `--output` 成功时不往终端打印数据。省略此参数仍可使用标准输出和管道，例如：

```bash
node cli.cjs samples/synthetic_notch.s2p --format json > result.json
```

需要跨终端保持相同输出编码时，使用 `--output`。

## 错误处理

| 退出码 | 含义 | 输出位置 |
| --- | --- | --- |
| `0` | 成功，或显示帮助 | 指定文件或标准输出 |
| `1` | 文件内容未通过解析或数据检查 | 标准输出中的诊断 JSON；不创建目标文件 |
| `2` | 命令参数、文件读取或写入错误 | 标准错误中的错误说明 |

例如，不完整记录或参考阻抗冲突会产生带错误码、行号、列号的 JSON。即使指定 `--format csv`，失败时也返回诊断 JSON，而不是把错误说明写进 CSV。

## 输入范围

文件须为 UTF-8，最多 2 MiB、20,000 个频点，支持一个开头 BOM 和 LF / CRLF / CR 换行。读取过程中出现文件增长时仍执行大小限制。具体 Touchstone 支持范围见 [兼容性说明](COMPATIBILITY.md)。
