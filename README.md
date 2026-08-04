# pixel bead counter

本项目用于把固定模板的拼豆图自动解析为 JSON，再在网页里勾选和汇总。

## 目录约定

- `image/`：输入图片
- `output/`：自动生成的条目 JSON、索引 JSON、差异报告
- `config/template_presets.json`：模板预设

## 运行顺序

1. 在目标设备上批量安装 `requirements.txt`
2. 在目标设备上执行可编辑安装，或者将 `src/` 加入 `PYTHONPATH`
3. 补充 `config/template_presets.json`
4. 运行解析命令生成 `output/index.json`
5. 启动网页查看和汇总

## 可编辑安装

如果要直接用命令入口，建议在目标设备上执行：

```bash
pip install -r requirements.txt
pip install -e .
```

## 目标设备安装与运行

在另一台设备上，按下面顺序执行即可：

1. 进入项目目录。
2. 创建并激活 Python 环境，建议使用 Python 3.12 或更高版本。
3. 安装依赖：`pip install -r requirements.txt`
4. 安装项目本身：`pip install -e .`
5. 复制 `config/template_presets.example.json` 为 `config/template_presets.json`
6. 根据你的实际图片模板，调整 `template_presets.json`
7. 把待识别图片放到 `image/` 文件夹
8. 运行解析：`pixel-counter parse-images`
9. 启动网页：`pixel-counter serve --host 0.0.0.0 --port 8000`

如果你只想先验证解析链路，也可以只执行第 8 步，然后检查 `output/` 下是否生成了每张图的 JSON 和 `index.json`。

## Windows 参考命令

如果目标设备也是 Windows，可以参考下面的命令：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
copy config\template_presets.example.json config\template_presets.json
pixel-counter parse-images
pixel-counter serve --host 0.0.0.0 --port 8000
```

## 运行结果

- 解析成功后，`output/` 目录会出现每张图对应的 JSON 文件。
- `output/index.json` 是图鉴页读取的总索引。
- `output/reviews/` 会保存需要人工介入的条目差异报告。

## 命令

- `pixel-counter parse-images`
- `pixel-counter build-index`
- `pixel-counter serve`

也可以直接运行：

- `python -m pixel_counter parse-images`
- `python -m pixel_counter build-index`
- `python -m pixel_counter serve`
