# Museum Bot

面向博物馆场景的**智能导览机器人**应用。访客通过 Web 控制面板选择目的地、提问互动；后台机器人线程负责路径规划、导航模拟、AI 问答与语音播报。项目可在 PC 上开发调试，也可部署到 **Raspberry Pi** 接入真实硬件。

## 功能特性

- **交互式导览导航** — 基于 A* 算法的路径规划，支持转弯惩罚与动态障碍
- **双语支持** — 英文（EN）与中文（ZH），含语言选择页与界面文案切换
- **AI 智能问答** — 接入 OpenAI 兼容 API，结合当前展点与 POI 知识库回答访客问题
- **语音播报（TTS）** — 使用 gTTS 合成语音，pygame 播放，本地缓存加速重复播报
- **实时地图可视化** — Canvas 渲染网格地图、机器人位置、路径与 POI
- **WebSocket 实时通信** — Flask-SocketIO 推送位置、路径、对话状态
- **语音输入** — 浏览器录音上传，支持语音提问
- **硬件抽象层** — `driver.py` 提供电机、超声波、音频接口，默认桩实现便于仿真开发

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web 浏览器（访客界面）                  │
│         语言选择 / 目的地 / 提问 / 地图可视化              │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP + WebSocket
┌────────────────────────▼────────────────────────────────┐
│  web.py — Flask + SocketIO                               │
│  路由、命令队列、状态轮询、地图 API                        │
└────────────────────────┬────────────────────────────────┘
                         │ command_queue
┌────────────────────────▼────────────────────────────────┐
│  app.py — Robot 状态机（IDLE / NAVIGATING / SPEAKING）    │
│  导航调度 · 问答处理 · TTS 触发 · 位置广播                 │
└───┬──────────────┬──────────────┬───────────────────────┘
    │              │              │
navigation.py   ai.py          tts.py
(A* 路径规划)  (OpenAI 问答)  (gTTS + pygame)
    │
driver.py（硬件驱动，可替换为树莓派真实实现）
```

## 项目结构

```
rasberrypi1/
├── app.py                      # 主入口：Robot 状态机与后台逻辑线程
├── web.py                      # Flask Web 服务与 SocketIO
├── navigation.py               # A* 路径规划
├── ai.py                       # OpenAI 问答与回复解析
├── tts.py                      # gTTS 语音合成与播放（适配树莓派）
├── driver.py                   # 硬件驱动接口（默认桩实现）
├── cli.py                      # 命令行工具（地图转换、TTS 预生成）
├── generate_tts_prompts.py     # 从 POI 数据生成 TTS 提示词
├── requirements.txt            # Python 依赖
├── data/
│   ├── raw_poi_data.sample.json        # POI 与地图示例数据
│   └── generated_tts_prompts.sample.json
├── templates/
│   ├── index.html              # 主控制面板
│   └── language_select.html    # 语言选择页
├── static/js/
│   └── visualization.js        # 地图与机器人可视化
└── tts_cache/                  # TTS 音频缓存（运行时自动生成）
```

## 环境要求

- Python 3.8+
- pip
- 网络连接（gTTS 合成、OpenAI API 调用）
- 可选：ffmpeg（若需 pydub 做音频格式转换）
- 部署到树莓派时建议安装 SDL / 音频相关系统库以支持 pygame

## 安装

### 1. 克隆仓库

```bash
git clone <your-repo-url>
cd rasberrypi1
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS / 树莓派
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 准备数据文件

仓库中实际使用的数据文件被 `.gitignore` 忽略，需从示例复制：

```bash
# Windows PowerShell
Copy-Item data\raw_poi_data.sample.json data\raw_poi_data.json
```

```bash
# Linux / macOS
cp data/raw_poi_data.sample.json data/raw_poi_data.json
```

### 5. 生成 TTS 提示词（推荐）

```bash
python generate_tts_prompts.py
```

该脚本会读取 `data/raw_poi_data.json`，生成 `data/generated_tts_prompts.json`，并在 `tts` 模块可用时预合成音频到 `tts_cache/`。

也可通过 CLI 调用：

```bash
python cli.py generate-tts
```

## 配置

### 环境变量

| 变量 | 说明 | 是否必需 |
|------|------|----------|
| `OPENAI_API_KEY` | OpenAI 或兼容服务的 API Key | AI 问答必需 |
| `OPENAI_BASE_URL` | API 基础地址，默认 `https://free.v36.cm/v1/` | 可选 |
| `OPENAI_CHAT_MODEL` | 对话模型，默认 `gpt-4o-mini` | 可选 |

**Windows PowerShell 示例：**

```powershell
$env:OPENAI_API_KEY = "your-api-key-here"
```

**Linux / 树莓派示例：**

```bash
export OPENAI_API_KEY="your-api-key-here"
```

> TTS 使用 gTTS（Google Text-to-Speech），无需额外 API Key，但需要网络访问 Google 服务。

### 数据文件说明

`data/raw_poi_data.json` 包含博物馆地图与展点信息：

- **map.grid** — 二维网格，`0` 为可通行，`1` 为墙体
- **map.metadata** — 起始坐标、朝向、网格单位（厘米）
- **pois** — 展点 ID、中英文名称、描述、坐标

可根据实际博物馆布局修改 POI 描述，AI 问答会将其作为知识库上下文。

## 运行

```bash
python app.py
```

默认在 `http://0.0.0.0:5001` 启动 Web 服务。浏览器访问：

```
http://localhost:5001
```

### 使用流程

1. 选择语言（English / 中文）
2. 在控制面板点击目的地，机器人开始导航
3. 到达展点后，可点击预设问题或自由提问
4. 地图区域实时显示机器人位置与规划路径
5. 支持浏览器语音输入提问

## 命令行工具

### 将 PNG 地图转为网格 JSON

用图像编辑器绘制地图：黑色为墙、白色为通道、青色 `#00f9ff` 标记 POI 位置。

```bash
python cli.py png-to-grid input.png output.json
```

### 预生成 TTS

```bash
python cli.py generate-tts
```

## 硬件集成（Raspberry Pi）

`driver.py` 当前为**桩实现**（仅打印日志），便于在无硬件环境下开发。接入真实机器人时需实现：

| 函数 | 作用 |
|------|------|
| `setup_hardware()` | 初始化电机控制器、传感器等 |
| `move_forward()` | 前进一个网格单位 |
| `turn(direction)` | 左转或右转 |
| `supersonic_sensor_check()` | 超声波避障，返回是否检测到障碍 |
| `play_wav(filename, language)` | 播放 WAV 音频文件 |

常见硬件组合：I2C 电机驱动板、GPIO 超声波模块、3.5mm 或 USB 音频输出。

## 主要 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 主控制面板 |
| `/language_select` | GET | 语言选择页 |
| `/goto` | POST | 导航至指定 POI |
| `/ask` | POST | 提交文字问题 |
| `/voice_input` | POST | 提交语音识别文本 |
| `/status` | GET | 轮询机器人与对话状态 |
| `/api/map_data` | GET | 静态地图与 POI 数据 |
| `/api/robot_position` | GET | 机器人当前位置与朝向 |

WebSocket 事件包括 `update_position`、`update_path`、`update_response` 等，用于前端实时刷新。

## 开发说明

| 模块 | 职责 |
|------|------|
| `app.py` | 应用编排：启动后台线程与 Web 服务 |
| `web.py` | HTTP 路由、命令队列、SocketIO 广播 |
| `navigation.py` | A* 寻路，含转弯惩罚 |
| `ai.py` | OpenAI 对话、追问解析、TTS 联动 |
| `tts.py` | gTTS 合成、mp3 缓存、pygame 播放 |
| `driver.py` | 硬件抽象，仿真/真机切换点 |

修改展点或地图后，请重新运行 `generate_tts_prompts.py` 以更新语音提示词。

## 许可证

本项目采用 [WTFPL](LICENSE) 许可证。
