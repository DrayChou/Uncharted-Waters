# imported/sea2_demo

这里保存的是从 `sea2_demo` **原样或近原样导入**的参考文件，方便后续做复刻、写脚本、校对数据来源。

## 来源

- 仓库：<https://github.com/dongzhang84/sea2_demo>
- 导入参考 commit：`82543a3`
- 导入时间：2026-06-20

## 目录说明

- `docs/`：原项目中的 Markdown 说明文档副本
- `game_data/`：原项目导出的结构化 JSON 数据副本

## 使用边界

这些文件保留了原项目的字段名、组织方式与置信度差异：

- 有些文件可直接消费，例如 `guide_ports_reference.json`、`ports_projected.json`、`windcur_dat.json`
- 有些文件仍属于研究中间态，例如 `za_dat.json`、`monster_dat.json`、`ships.json`、`characters.json`

面向本仓库读者的二次整理，请优先看上级目录中的：

- `README.md`
- `复刻可用数据清单.md`
- `manifest.json`
- `generated/`
