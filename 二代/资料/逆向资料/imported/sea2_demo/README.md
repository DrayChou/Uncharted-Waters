# imported/sea2_demo

这里保存的是从 `sea2_demo` **原样或近原样导入**的参考文件，方便后续做复刻、写脚本、校对数据来源。

## 来源

- 仓库：<https://github.com/dongzhang84/sea2_demo>
- 导入参考 commit：`82543a3`
- 导入时间：2026-06-20

## 目录说明

- `sea2_demo-CLAUDE.md`：原项目对格式、算法、已完成 / 未完成内容的总说明
- `scripts/`：原项目脚本树，包含解压、提取、渲染、反汇编、拓扑分析与 experiments
- `docs/`：原项目中的 Markdown / 反汇编说明文档副本
- `game_data/`：原项目导出的结构化 JSON 数据副本
- `ROADMAP.md`：原项目的阶段路线图

## 使用边界

这些文件保留了原项目的字段名、组织方式与置信度差异：

- 有些文件可直接消费，例如 `guide_ports_reference.json`、`ports_projected.json`、`windcur_dat.json`
- 有些文件仍属于研究中间态，例如 `za_dat.json`、`monster_dat.json`、`ships.json`、`characters.json`

面向本仓库读者的二次整理，请优先看上级目录中的：

- `README.md`
- `复刻可用数据清单.md`
- `逆向算法与提取脚本总览.md`
- `manifest.json`
- `generated/`
