# 命令行指南

运行包附带 `cli.cjs`，需要 Node.js 22。以下命令在运行包解压目录执行；从源码构建后，将路径改为 `dist/cli.cjs`。

## 读取文件

```bash
node cli.cjs samples/synthetic_notch.s2p --format json
node cli.cjs samples/synthetic_notch.s2p --format csv -o result.csv
node cli.cjs input.txt --ports 1 -o result.json
node cli.cjs --version
node cli.cjs --help
```

默认输出 JSON。`.s1p`、`.s2p` 后缀用于识别端口数，`--ports` 可显式指定。遇到以短横线开头的文件名，使用 `--` 结束选项解析：

```bash
node cli.cjs --format json -- --antenna.s1p
```

## 管道输入

使用 `-` 从标准输入读取，并提供端口数。下面的命令适用于 Bash：

```bash
cat antenna.s1p | node cli.cjs - --ports 1 --format csv -o antenna.csv
```

管道中的字节应为 UTF-8。不同终端对管道文本的编码处理不同；在 PowerShell 中，直接传入文件路径更方便：

```powershell
node cli.cjs '测量数据.s1p' --format csv -o '分析结果.csv'
```

文件和标准输入均限制为 2 MiB，最多 20,000 个频点。读取按块计数，超限即返回错误；数据解析仍使用 MoonBit 核心。

## 输出文件

`-o` 或 `--output` 将结果直接写成 UTF-8，无需依赖终端重定向的文本编码设置。输出路径的父目录必须已存在。

已有文件不会被覆盖，包括输入文件本身。需要重新导出时，请换一个文件名，或先自行处理旧结果。数据检查失败时不会创建输出文件。

不使用 `-o`，或指定 `-o -`，会写入标准输出。完整运行包的文件清单会检测额外文件；执行完整性检查前，请将分析结果保存在运行包目录之外。

## 退出码与诊断

| 退出码 | 含义 | 输出 |
| --- | --- | --- |
| `0` | 成功 | CSV / JSON 写入标准输出或指定文件 |
| `1` | 数据检查失败 | 带错误码、行列位置和原因的 JSON |
| `2` | 参数、读取或写入错误 | 标准错误输出中的文字说明 |

默认模式保留 JSON 诊断到标准输出，便于脚本读取。使用 `-o 文件名` 时，JSON 诊断改写到标准错误输出，输出文件保持不变。CSV 模式遇到数据错误也返回 JSON 诊断，因此调用脚本应检查退出码，不要只判断是否收到文本。

`--ports`、`--format` 和 `--output` 各只能出现一次，避免相互覆盖设置。输出管道提前关闭时返回退出码 `2`，不打印未捕获异常堆栈。
