# Chronos Image Gen

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

通过 [aichronos.xyz](https://aichronos.xyz) Images API 生图的 Agent Skill 与命令行工具，无需 OpenAI API Key。

- **仓库地址：** [https://github.com/zxq49131-blip/Chronos-image-gen](https://github.com/zxq49131-blip/Chronos-image-gen)
- **English:** [README.md](README.md)
- **API / Agent Skill：** [SKILL.md](SKILL.md)

## 功能

- 文本生图：`POST /v1/images/generations`
- 默认模型 `gpt-image-2.5-sunburst`，可选 `grok-imagine-image`
- 可调质量、尺寸、输出格式
- 多 Token 并行生成（`-n` + 额外 token）
- 可作为 Claude Code / Codex / Cursor Skill 使用
- 本地支持 `.env` 读取 token

## 环境要求

- Python 3.8+
- `requests`
- Token 必须来自 **生图（image-generation）** 订阅分组。普通对话/聊天 Key 可能能通过鉴权，但生图仍会失败。

```bash
pip install requests
# 可选：自动读取 .env
pip install python-dotenv
```

## 快速开始

1. 复制 `.env.example` 为 `.env` 并填入 token，或在终端里导出环境变量。
2. 运行 CLI。

### 环境变量

**bash / zsh**

```bash
export ZHEXUEQI_TOKEN="zxq_..."
python zhexueqi_gen.py "一颗放在白色桌子上的红苹果"
```

**PowerShell**

```powershell
$env:ZHEXUEQI_TOKEN = "zxq_..."
python zhexueqi_gen.py "一颗放在白色桌子上的红苹果"
```

### `.env` 文件

```env
ZHEXUEQI_TOKEN=zxq_xxxxxxxx
```

不要把真实 token 提交进仓库。`.env` 已被 gitignore。

## 克隆仓库

```bash
git clone https://github.com/zxq49131-blip/Chronos-image-gen.git
cd Chronos-image-gen
pip install requests
```

## 命令行用法

```text
python zhexueqi_gen.py "提示词" [选项]

选项:
  -n N          生成数量（默认 1，建议 1-10）
  -q QUALITY    质量：low | medium | high（默认 low）
  -s SIZE       尺寸：如 1024x1024、2048x2048、2880x2880、auto
  -f FORMAT     格式：png | webp（默认 png）
  -r PATH       参考图路径（可重复）
  -o DIR        输出目录（默认 output）
  -m MODEL      gpt-image-2.5-sunburst（默认）| grok-imagine-image
```

生成结果保存为 `output/generated_1.png`（或 `.webp`）。

### 示例

```bash
# 基础用法
python zhexueqi_gen.py "日落山景"

# 高质量 2K
python zhexueqi_gen.py "未来城市" -q high -s 2048x2048

# 输出 WebP
python zhexueqi_gen.py "玻璃瓶产品棚拍" -f webp

# 使用 Grok 模型
python zhexueqi_gen.py "书店里的可爱机器人" -m grok-imagine-image

# 4 张并行生成（需先配置多个 token）
python zhexueqi_gen.py "一只可爱的猫" -n 4

# 自定义输出目录
python zhexueqi_gen.py "时尚杂志人像" -o images/generations
```

`/v1/images/generations` 是文本生图接口。参考图编辑请使用 `/v1/images/edits`，详见 [SKILL.md](SKILL.md)。CLI 仍保留 `-r`，方便本地试验。

## 多 Token 并行

当 `-n > 1` 时，额外 token 会用来并行发请求：

```bash
export ZHEXUEQI_TOKEN="zxq_xxx"
export ZHEXUEQI_TOKEN_2="zxq_yyy"
export ZHEXUEQI_TOKEN_3="zxq_zzz"
```

脚本会读取 `ZHEXUEQI_TOKEN` 到 `ZHEXUEQI_TOKEN_5`。任务会均分到已配置的 token。例如两个 token 且 `-n 4` 时，每个 token 同时承担 2 次调用。

## 模型

| 模型 | 说明 |
|------|------|
| `gpt-image-2.5-sunburst` | 默认模型。除非明确要求其他模型，否则使用它。 |
| `grok-imagine-image` | Grok 生图模型。仅在明确要求 Grok 时使用。 |

建议：`2048x2048`（或更小）配合 `high` 质量，稳定性和细节比较均衡。只有特别需要细节时再上 4K。

## 尺寸约束

| 约束 | 值 |
|------|-----|
| 最大边长 | 3840px |
| 边长倍数 | 16px |
| 最大像素 | 8,294,400 |
| 最大正方形 | 2880x2880 |
| 最大宽屏 | 3840x2160（16:9） |

## Agent Skill

`SKILL.md` 中的 skill id 仍为 `zhexueqi-image-gen`。

### Claude Code

```bash
npx skills add zxq49131-blip/Chronos-image-gen
```

安装后直接让 Agent 生图即可。

### Codex / 本地 skills 目录

把本仓库克隆或复制到 skills 目录，例如：

```bash
git clone https://github.com/zxq49131-blip/Chronos-image-gen.git ~/.codex/skills/chronos-image-gen
```

Windows 上通常是 `%USERPROFILE%\.codex\skills\chronos-image-gen`。

让 Agent 生图前先设置 `ZHEXUEQI_TOKEN`。如果没有 token，skill 应停止并提醒用户配置。

Token 必须属于生图订阅分组。

## API

规范请求格式见 [SKILL.md](SKILL.md)（含解析与重试说明）：

```http
POST https://aichronos.xyz/v1/images/generations
Authorization: Bearer $ZHEXUEQI_TOKEN
Content-Type: application/json
```

```json
{
  "model": "gpt-image-2.5-sunburst",
  "prompt": "Generate a photorealistic image of a red apple on a white table",
  "n": 1,
  "response_format": "b64_json",
  "quality": "high",
  "size": "2048x2048",
  "output_format": "png"
}
```

图片以 Base64 返回在 `data[].b64_json`。

**不要**向该端点发送 `input`、`tools`、`tool_choice` 或 `stream`。

```bash
curl -s https://aichronos.xyz/v1/images/generations \
  -H "Authorization: Bearer $ZHEXUEQI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2.5-sunburst","prompt":"white table red apple","n":1,"response_format":"b64_json","quality":"high","size":"2048x2048","output_format":"png"}'
```

## 常见问题

| 症状 | 原因 | 解决 |
|------|------|------|
| 504 Gateway Timeout | 上游生成超时 | 降低质量或缩小尺寸后重试 |
| 返回结果没有图片 | 请求体不是 Images API 格式 | 发送 `prompt`，解析 `data[].b64_json` |
| 401 / 403 | Token 过期、无效，或不属于生图分组 | 换成生图分组的新 token |
| 需要参考图 | generations 只支持文本生图 | 使用 `/v1/images/edits` |
| 生成很慢 | 高质量 + 大尺寸 | 改用 medium、1K/2K，或增加 token 并行 |

## 协议

MIT，见 [LICENSE](LICENSE)。

仓库：[github.com/zxq49131-blip/Chronos-image-gen](https://github.com/zxq49131-blip/Chronos-image-gen)。