# ChatTTS 长音频生成工具

一个基于 [ChatTTS](https://github.com/2noise/ChatTTS) 与 [chatTTS-ui](https://github.com/jianchang512/chatTTS-ui) 改进的本地文本转语音工具，提供网页 UI 与 API，专注解决**长音频生成**、**专业术语/英文/数字/特殊符号读错**等问题。

## 演示教程

项目安装、启动与使用演示可观看 B 站教程视频：

[ChatTTS 长音频生成工具演示教程](https://www.bilibili.com/video/BV15nNQ6EEGs)

## 关于作者

本项目由 [**卷卷姐juan**](https://space.bilibili.com/229150291) 维护，欢迎关注 B 站账号，获取更多 AI 音频与视频创作相关内容。

## 致谢与上游项目

本项目在以下两个开源项目基础上进行改进：

- [2noise/ChatTTS](https://github.com/2noise/ChatTTS)：底层 TTS 模型与推理代码。
- [jianchang512/chatTTS-ui](https://github.com/jianchang512/chatTTS-ui)：提供本地 WebUI 与 API 调用方式。

## 为什么要做这个项目？

在使用原版 ChatTTS 和 chatTTS-ui 的过程中，我们发现几个影响视频生产体验的痛点：

1. **ChatTTS 没有 UI，启动麻烦**  
   需要手动跑脚本、配置环境，对不熟悉命令行的用户不友好。

2. **无法稳定生成长音频**  
   做视频解说、有声书时，文本往往很长。直接整段生成，一旦段落过长，后面就会出现杂音、口齿不清甚至无法听的情况，只能手动切分再逐段生成，非常繁琐。

3. **专业术语、英文、数字、特殊符号容易读错**  
   例如金融/科技领域的专业词、英文单词、手机号、小数、百分号、公式等，模型经常按中文方式“乱读”。

## 主要改进

### 1. 一键启动的本地 WebUI
- 继承 chatTTS-ui 的网页界面，双击脚本即可启动服务。
- 浏览器访问 `http://localhost:9966` 即可使用。

### 2. 长音频自动切分与合并
- 服务端 `app.py` 会按行/按标点自动拆分文本，逐段推理后合并成一段完整音频。
- `chattts_api_client.py` 提供命令行示例：输入长文本后自动切分为多段，调用本地 `/tts` 接口批量生成，最后合并并插入适当静音，输出一条完整长音频。
- 适合 5 分钟、10 分钟甚至更长的解说词生成。

### 3. 文本预处理：数字、英文、特殊符号归一化
- `uilib/utils.py` 中集成了中英文文本归一化逻辑：
  - 数字（整数、小数、百分数、手机号、座机号、日期时间、算式等）转换为适合朗读的形式。
  - 英文单词、数字串按英文读法处理，避免中文式乱读。
  - 过长句子自动按标点切分，降低单次推理 token 过长导致的音质异常。

### 4. 音色管理
- `speaker/` 目录预置了多组音色 CSV/PT 文件。
- 在 WebUI 或 API 中通过 `voice` 参数指定音色：可以是数字 seed（如 `2222`），也可以是 `speaker/` 目录下的音色文件名。
- 通过环境变量 `DEFAULT_VOICE` 可修改 WebUI 打开时的默认音色。仓库默认 `2222`，本地可在 `.env` 中按需设置。

## 目录说明

```text
ChatTTS/                    # ChatTTS 模型推理代码（来自上游）
docs/                       # 项目截图与示例音频
speaker/                    # 预置音色文件（CSV/PT）
static/                     # WebUI 静态资源
static/workbench.html       # 网页工作台主界面
templates/                  # Flask 模板
uilib/                      # 工具函数：文本归一化、音色加载、参数处理等
uilib/zh_normalization/     # 中文文本归一化模块
app.py                      # 主服务：WebUI + /tts API
bootstrap_run.py            # 自动创建虚拟环境、安装依赖并启动服务
chattts_api_client.py       # 长文本批量生成/合并示例脚本
双击启动.bat                  # Windows 一键启动脚本
requirements.txt            # Python 依赖
pyproject.toml              # 项目元数据与打包配置
.env.example                # 环境变量示例
Dockerfile.cpu              # CPU 版 Docker 镜像配置
Dockerfile.gpu              # GPU 版 Docker 镜像配置
docker-compose.cpu.yaml     # CPU 版 Docker Compose 配置
docker-compose.gpu.yaml     # GPU 版 Docker Compose 配置
faq.md                      # 常见问题说明
README_EN.md                # 英文说明文档
```

## 环境要求

- Windows（源码部署）
- Python 3.10–3.11
- 显卡：有 4GB 以上显存的 NVIDIA 显卡可启用 CUDA 加速；否则使用 CPU

## 界面预览

![ChatTTS WebUI 预览](docs/ScreenShot_2026-07-12_195458_326.png)

## 安装与启动

### 1. 克隆仓库

```bash
git clone <你的仓库地址>.git
cd ChatTTS-LongAudio
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
```

> 如果需要 GPU 加速，请额外安装 CUDA 11.8+ 对应的 PyTorch，例如：  
> `pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118`

### 3. 复制环境变量文件

```bash
copy .env.example .env
```

### 4. 启动服务

方式一：双击运行：

```text
双击启动.bat
```

方式二：命令行启动：

```bash
call venv\Scripts\activate.bat
python app.py
```

首次启动时会自动从 modelscope 下载 ChatTTS 模型到 `models/` 目录（约 1GB+，已配置 `.gitignore` 不进入仓库）。

启动成功后浏览器访问：

```text
http://localhost:9966
```

## API 调用示例

### 长音频批量生成

```bash
python chattts_api_client.py "你好，这是第一段。这是第二段，用于测试长音频合并功能。"
```

脚本会：
1. 按句子/长度切分文本；
2. 逐段调用 `http://127.0.0.1:9966/tts`；
3. 下载每段音频到 `output/`；
4. 合并成一条带 0.5 秒静音间隔的完整音频。

### 直接调用 /tts 接口

```python
import requests

res = requests.post('http://127.0.0.1:9966/tts', data={
    "text": "你好，这是 ChatTTS 长音频测试。",
    "prompt": "[break_3]",
    "voice": "2222",
    "temperature": 0.00001,
    "top_p": 0.6,
    "top_k": 20,
    "skip_refine": 0,
})
print(res.json())
```

## 常用参数

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `WEB_ADDRESS` | `localhost:9966` | 服务监听地址 |
| `compile` | `false` | 是否启用 torch.compile |
| `DEFAULT_VOICE` | `2222` | 默认音色，可以是数字 seed 或 `speaker/` 下的文件名 |

API 参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `text` | - | 待合成文本（必填） |
| `voice` | `2222` | 音色编号或 `speaker/` 下的音色文件名 |
| `temperature` | `0.3` | 采样温度 |
| `top_p` | `0.7` | top_p |
| `top_k` | `20` | top_k |
| `skip_refine` | `0` | 是否跳过文本 refine |
| `infer_max_new_token` | `2048` | 推理最大 token |
| `refine_max_new_token` | `384` | refine 最大 token |

## 注意事项

1. **模型文件**：`models/` 目录会在首次运行时自动下载，体积较大（约 1GB+），已加入 `.gitignore`，不需要也不应提交到 GitHub。
2. **生成文件**：`output/`、`static/wavs/`、`logs/` 为运行时输出，已加入 `.gitignore`。
3. **音色文件**：`speaker/` 中的 `.csv`/`.pt` 为音色嵌入，体积很小，可随仓库一起提交。
4. **二进制发布**：如需提供免安装 exe，请通过 GitHub Releases 发布，不要直接提交到仓库。

## 许可证

本项目继承上游项目许可证，详见 [LICENSE](LICENSE)。

## 致谢

感谢 [2noise/ChatTTS](https://github.com/2noise/ChatTTS) 与 [jianchang512/chatTTS-ui](https://github.com/jianchang512/chatTTS-ui) 的开源贡献。
