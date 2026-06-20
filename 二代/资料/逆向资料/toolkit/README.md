# uw2-toolkit

这是从 `sea2_demo` 进一步提炼出来的**最小工具包骨架**，目标是把《大航海时代 II》复刻最核心的生成链，从“作者本机研究脚本集合”推进成“你可以继续维护的工具链”。

## 当前范围

当前工具包骨架已包含这些模块：

- `uw2toolkit.config` — 路径与环境变量配置
- `uw2toolkit.ls11` — LS10 / LS11 / Ls12 容器解压
- `uw2toolkit.text` — 基础文本解码
- `uw2toolkit.dat_extract` — Phase 1 DAT 提取
- `uw2toolkit.render.portchip` — Portchip atlas 渲染
- `uw2toolkit.render.portmap` — Portmap 港口图渲染
- `uw2toolkit.render.worldmap` — Worldmap v1 / v2 解码与渲染
- `uw2toolkit.cli` — CLI 入口
- `uw2toolkit.doctor` — 环境 / 依赖 / 原始资源就绪检查
- `tests/` — 基础单元测试

## 输入目录约定

默认读取：

```text
toolkit/raw/Koukai2/
```

建议把这些原始文件放进去：

- `*.lzw`
- `Main.exe`
- `Chip_no.dat`
- `KoeiCht.txt`
- `1.pat`
- `2.pat`
- `Message.dat`
- 以及其他 `.dat`

也可以通过环境变量覆盖：

```bash
export UW2_RAW_DIR=/path/to/Koukai2
export UW2_OUT_DIR=/path/to/output
```

## 输出目录约定

默认输出到：

```text
toolkit/output/
```

## 安装依赖

最小依赖：

```bash
pip install numpy pillow
```

如需研究层脚本（当前工具包骨架未强依赖）：

```bash
pip install unicorn capstone pyte
```

## 典型用法

在 `toolkit/` 目录下：

```bash
python -m uw2toolkit.cli ls11-decode raw/Koukai2/Kao.lzw output/lzw_parts/Kao
python -m uw2toolkit.cli inventory-lzw
python -m uw2toolkit.cli render-portchip
python -m uw2toolkit.cli render-portmap
python -m uw2toolkit.cli render-worldmap --mode v2
python -m uw2toolkit.cli extract-phase1
python -m uw2toolkit.cli decode-text raw/Koukai2/Message.dat
python -m uw2toolkit.cli doctor
python -m unittest discover -s tests -v
```

## 当前定位

这还不是完整成品工具包，而是：

- 一条稳定主链的开始
- 一套不依赖作者本机路径的代码骨架
- 未来继续迁移更多脚本的落脚点

## 下一步建议

1. 先运行 `python -m uw2toolkit.cli doctor`，确认原始资源目录和依赖是否就绪
2. 再用你自己的原始资源目录跑通：
   - `inventory-lzw`
   - `render-portchip`
   - `render-portmap`
   - `render-worldmap --mode v2`
   - `extract-phase1`
3. 再继续补文本链和研究链
4. 最后把复刻工程直接消费的规范化 JSON 接到这里
