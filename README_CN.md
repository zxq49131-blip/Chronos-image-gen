# zhexueqi-image-gen

通过 [zhexueqi.xyz](https://zhexueqi.xyz) API 生成图片 — 无需 OpenAI Key。

## 快速开始

```bash
# 1. 设置 token
export ZHEXUEQI_TOKEN="zxq_..."

# 2. 安装依赖
pip install requests

# 3. 生成图片
python zhexueqi_gen.py "一颗放在白色桌子上的红苹果"
```

## 用法

```
python zhexueqi_gen.py "提示词" [选项]

选项:
  -n N          生成数量 (1-10, 默认 1)
  -q QUALITY    质量: low | medium | high (默认 low)
  -s SIZE       尺寸: 如 1024x1024, 2048x2048, 2880x2880, auto
  -f FORMAT     格式: png | webp (默认 png)
  -r PATH       参考图路径 (可重复)
  -o DIR        输出目录 (默认 output)
  -m MODEL      模型: gpt-5.5 (默认) | gpt-5.4 | gpt-5.4-mini
```

### 示例

```bash
# 基础用法
python zhexueqi_gen.py "日落山景"

# 高质量 2K
python zhexueqi_gen.py "未来城市" -q high -s 2048x2048

# 4 张并行生成 (配合多个 token)
python zhexueqi_gen.py "一只可爱的猫" -n 4

# 带参考图
python zhexueqi_gen.py "给这只猫画一顶帽子" -r cat.png -r style_ref.png
```

## 多 Token 并行

当 `-n > 1` 时，如果有多个 token，请求会自动分配到不同 token 并行执行：

```
export ZHEXUEQI_TOKEN="zxq_xxx"
export ZHEXUEQI_TOKEN_2="zxq_yyy"
```

例如 n=4 时，两个 token 各承担 2 次调用，同时发出。

## Claude Code 技能

```bash
npx skills add https://github.com/zxq49131-blip/zhexueqi-image-gen
```

安装后直接让 Claude Code 帮你生图即可。

## 技术细节

使用 OpenAI Responses API 格式：

- 端点：`POST https://zhexueqi.xyz/respones`
- 模型：`gpt-5.5` 调用 `image_generation` 工具
- 流式：SSE（`stream: true`，绕过 60s 网关超时）
- 鉴权：`Authorization: Bearer` 头

关键参数：
- `tools[].action: "generate"` — 必须显式指定，否则模型返回文字而非图片
- `tool_choice: "required"` — 强制调生图工具
- `stream: true` — 非流式请求会被 60s 网关超时掐断

参考图通过 `input_image` content block 传入，支持 `data:` URL 格式的 base64。

## 模型

| 模型 | 速度 | 说明 |
|-------|------|------|
| gpt-5.5 | ~30-70s | 综合最佳 |
| gpt-5.4 | ~30-120s | 流式下全部尺寸可用 |
| gpt-5.4-mini | ~20-120s | 小图/低质量最快 |

全部模型在 `stream: true` 下支持参考图和所有尺寸。

## 尺寸约束

| 约束 | 值 |
|------|-----|
| 最大边长 | 3840px |
| 边长倍数 | 16px |
| 最大像素 | 8,294,400 |
| 最大正方形 | 2880×2880 |
| 最大宽屏 | 3840×2160 (16:9) |

## 常见问题

| 症状 | 原因 | 解决 |
|------|------|------|
| 504 Gateway Timeout | 非流式超 60s | 加 `"stream": true` |
| 返回文字而非图片 | 没设 `action: "generate"` | 加 `"action": "generate"` + `"tool_choice": "required"` |
| 401 Token 验证失败 | Token 过期或无效 | 换新 token |
| 参考图无效 | input 格式不对 | 用数组格式 + `input_image` block |

## 协议

MIT
