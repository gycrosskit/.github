# GY CrossKit 共用配置

本仓库保存组织主页、跨仓库发布规则和共用脚本模板。

- [`AGENTS.md`](AGENTS.md)：AI 工作入口，按任务指向[组件开发](docs/组件开发.md)、[Git Flow 与提交规范](docs/GitFlow与提交规范.md)和[发布流程](docs/发布流程.md)。
- [组件文档索引](docs/组件文档索引.md)：17 个组件库的功能入口、文档分工和 core / CMP / Kuikly / 平台差异维护规则。
- [组件文档规范](docs/组件文档规范.md)：第三方 README 内容、安装渠道区分、详细文档与 Wiki 的维护边界。
- [组件评审技能](skills/gycrosskit-component-review/SKILL.md)：公开能力清单、CMP/Kuikly 平台调用链、行为与精简两轮检查及反向复审；[测试与 API 审查](docs/组件测试与API审查.md)保留方法入口和历史记录。
- [组件抽离路线图](docs/组件抽离路线图.md)：权限、扫码、媒体、定位等三端组件的边界、实施顺序与首版交付状态。
- [Issues 与迭代流程](docs/Issues与迭代流程.md)：接入项目提交问题后，如何修复、验证、发布并关闭 Issue。
- [组织默认 Issue 模板](.github/ISSUE_TEMPLATE/integration-problem.md)：收集版本、平台和复现信息；组件仓库可自行覆盖。
- [`templates/jitpack-metadata.py`](templates/jitpack-metadata.py)：compose-webview、live-sdk、toast、debug-tools、customer-service 共用的 KMP 元数据修正脚本模板。
- [`templates/check-maven.py`](templates/check-maven.py)：校验完整 publication、POM 许可证、Native 变体、实际文件及四种哈希和 sidecar。
- [`scripts/test-check-maven.py`](scripts/test-check-maven.py)：发布校验的正向与失败场景回归。
- [持续集成门禁](docs/持续集成门禁.md)：14 个功能组件的源码、冻结产物和独立远程消费者回归边界。
- [CI 优化与评审计划](docs/CI优化与评审计划.md)：事件分工、下载与缓存、失败证据、版本检查和上线测量。
- [`templates/check-public-maven.py`](templates/check-public-maven.py)：实际 JitPack 标签、POM/GMM、variant 字节摘要及公开 sidecar 校验；[最小自检](scripts/test-check-public-maven.py)。
- [`scripts/protect-main.sh`](scripts/protect-main.sh)：为新建的公开仓库配置 `main` 分支保护；规则定义在 [`templates/main-protection.json`](templates/main-protection.json)。
- [`profile/README.md`](profile/README.md)：GitHub 组织主页内容。

本机工作区的 `/Users/guoyang/gycrosskit/AGENTS.md` 链接到这里的规则文件。JitPack 只检出正在构建的仓库，所以各依赖库保留脚本副本和自身的 `jitpack.yml`；修改共用脚本时先改模板，再同步并核对副本。Koin、Stately、MMKV 的预构建归档流程各有依赖和校验值，仍由各仓库维护。GitHub Free 不提供覆盖未来仓库的组织级 ruleset；新建仓库后须执行保护脚本并核验结果。
