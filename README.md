# GY CrossKit 共用配置

本仓库保存组织主页、跨仓库发布规则和共用脚本模板。

- [`AGENTS.md`](AGENTS.md)：AI 工作入口，按任务指向[组件开发](docs/组件开发.md)、[Git Flow 与提交规范](docs/GitFlow与提交规范.md)和[发布流程](docs/发布流程.md)。
- [`templates/jitpack-metadata.py`](templates/jitpack-metadata.py)：compose-webview、live-sdk、toast 三个仓库共用的 KMP 元数据修正脚本模板。
- [`scripts/protect-main.sh`](scripts/protect-main.sh)：为新建的公开仓库配置 `main` 分支保护；规则定义在 [`templates/main-protection.json`](templates/main-protection.json)。
- [`profile/README.md`](profile/README.md)：GitHub 组织主页内容。

本机工作区的 `/Users/guoyang/gycrosskit/AGENTS.md` 链接到这里的规则文件。JitPack 只检出正在构建的仓库，所以各依赖库保留脚本副本和自身的 `jitpack.yml`；修改共用脚本时先改模板，再同步并核对副本。Koin、Stately、MMKV 的预构建归档流程各有依赖和校验值，仍由各仓库维护。GitHub Free 不提供覆盖未来仓库的组织级 ruleset；新建仓库后须执行保护脚本并核验结果。
