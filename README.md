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

## 命令

- `pixel-counter parse-images`
- `pixel-counter build-index`
- `pixel-counter serve`

也可以直接运行：

- `python -m pixel_counter parse-images`
- `python -m pixel_counter build-index`
- `python -m pixel_counter serve`
