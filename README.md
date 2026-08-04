# pixel bead counter

自动把固定模板的拼豆图解析为 JSON，并在网页里做勾选汇总。

## 项目结构

- `image/`：输入图片
- `output/`：自动生成的条目 JSON、索引 JSON、差异报告
- `config/template_presets.json`：模板预设
- `src/pixel_counter/`：解析器、校验器、网页查看器

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 安装项目：`pip install -e .`
3. 复制模板预设：`copy config\template_presets.example.json config\template_presets.json`
4. 把图片放进 `image/`
5. 运行解析：`pixel-counter parse-images`
6. 启动网页：`pixel-counter serve --host 0.0.0.0 --port 8000`

## 命令

- `pixel-counter parse-images`：批量把图片转成 JSON
- `pixel-counter build-index`：查看当前索引文件
- `pixel-counter serve`：启动图鉴网页

## 运行结果

- `output/` 中会生成每张图对应的条目 JSON
- `output/index.json` 是网页读取的总索引
- `output/reviews/` 保存需要人工介入的差异报告

## 目标设备

在另一台设备上运行时，建议先使用 Python 3.12 或更高版本创建虚拟环境，再执行上述命令。Windows 下可直接使用 `PowerShell` 运行。
