# zhexueqi-image-gen

通过 zhexueqi.xyz API 生成图片。

这个修复版更新了当前可用的接口、默认模型和 SSE 图片解析逻辑。

## 快速开始

```powershell
$env:ZHEXUEQI_TOKEN="zxq_..."
python .\zhexueqi_gen.py "清晰的木材资源图标，透明背景，游戏UI风格"
```

## 默认配置

- 接口：`https://hk-api.zhexueqi.xyz/responses`
- 模型：`gpt-image-2`
- 质量：`low`
- 尺寸：`1024x1024`
- 格式：`png`
- 流式：开启

需要时可以覆盖接口：

```powershell
$env:ZHEXUEQI_URL="https://hk-api.zhexueqi.xyz/responses"
```

## 用法

```text
python zhexueqi_gen.py "提示词" [选项]

选项:
  -n N          生成数量，默认 1
  -q QUALITY    low | medium | high，默认 low
  -s SIZE       例如 1024x1024、2048x2048、2880x2880、auto
  -f FORMAT     png | webp，默认 png
  -r PATH       参考图路径，可重复传入
  -o DIR        输出目录，默认 output
  -m MODEL      gpt-image-2 默认 | grok-imagine-image
```

## 示例

```powershell
python .\zhexueqi_gen.py "温暖清晨的殖民地生存游戏主菜单背景，手绘风格" -q high -s 2048x2048 -o output/main_menu
python .\zhexueqi_gen.py "清晰的石头资源图标，透明背景，游戏背包图标" -n 4 -q medium -s 1024x1024 -o output/icons
python .\zhexueqi_gen.py "把参考图重绘成干净的游戏UI图标" -r reference.png -q medium -s 1024x1024
```

## 修复内容

- 默认接口从 `https://zhexueqi.xyz/respones` 改为 `https://hk-api.zhexueqi.xyz/responses`。
- 默认模型从 `gpt-5.5` 改为 `gpt-image-2`。
- 增加 `ZHEXUEQI_URL` 环境变量覆盖。
- 修复 SSE 解析，支持顶层 `partial_image_b64` 以及嵌套 `item` 图片字段。
- 保留多 token 并发生成能力。

## Token 说明

`ZHEXUEQI_TOKEN` 必须是生图分组 key。普通聊天/API key 可能无法鉴权。

不要提交真实 token。
