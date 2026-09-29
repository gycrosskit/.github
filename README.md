# GY CrossKit 共用配置

本仓库保存组织主页、跨仓库发布规则和共用脚本模板。

- [`AGENTS.md`](AGENTS.md)：AI 处理 GY CrossKit 仓库时共用的发布规则，以及本次 JitPack、ohpm 迁移验证得到的检查项。
- [`templates/jitpack-metadata.py`](templates/jitpack-metadata.py)：compose-webview、live-sdk、toast 三个仓库共用的 KMP 元数据修正脚本模板。
- [`profile/README.md`](profile/README.md)：GitHub 组织主页内容。

本机工作区的 `/Users/guoyang/gycrosskit/AGENTS.md` 链接到这里的规则文件。JitPack 只检出正在构建的仓库，所以各依赖库保留脚本副本和自身的 `jitpack.yml`；修改共用脚本时先改模板，再同步并核对副本。Koin、Stately、MMKV 的预构建归档流程各有依赖和校验值，仍由各仓库维护。
