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
3. 复制模板预设文件：把 `config\template_presets.example.json` 复制一份，重命名为 `config\template_presets.json`
4. 把图片放进 `image/`
5. 运行解析：`pixel-counter parse-images`
6. 启动网页：`pixel-counter serve --host 0.0.0.0 --port 8000`

## 第 3 步怎么做

这一步的意思是：先保留一份示例配置，再生成一份你自己的正式配置。

你可以把它理解成“模板说明书”复制成“正式使用版”。程序会优先读取 `config\template_presets.json`，所以你需要先把这个文件准备出来。

### Windows 手把手做法

1. 打开项目目录里的 `config` 文件夹。
2. 找到 `template_presets.example.json`。
3. 右键复制这个文件。
4. 在同一个文件夹里粘贴一份副本。
5. 把副本的文件名改成 `template_presets.json`。
6. 用记事本或 VS Code 打开 `template_presets.json`。
7. 根据你的图片尺寸和模板情况，调整里面的预设参数。

### 如果你用 PowerShell

可以直接执行：

```powershell
Copy-Item config\template_presets.example.json config\template_presets.json
```

### 这两个文件分别是什么

- `template_presets.example.json`：示例文件，留着参考
- `template_presets.json`：正式文件，程序真正读取它

### 你什么时候需要改它

如果你的图片模板和示例配置一致，通常只要复制过去就能先跑。
如果图片尺寸、网格数量、汇总条位置不同，就需要改 `template_presets.json` 里的参数。

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
