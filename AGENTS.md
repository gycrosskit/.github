# GY CrossKit 共用工作规则

本仓库是跨项目规则和脚本的版本源；本地 `/Users/guoyang/gycrosskit/AGENTS.md` 链接到此文件。进入具体仓库后，先读其源码、构建配置和更具体的 `AGENTS.md`，再按任务读取对应文档：

- [组件开发](docs/组件开发.md)：平台边界、公共 API、验证与中文 README。
- [组件评审技能](skills/gycrosskit-component-review/SKILL.md)：专项全库审查、定向变更评审和修复复审；按公开能力与实际调用链分两轮检查行为及精简。
- [Git Flow 与提交规范](docs/GitFlow与提交规范.md)：分支、提交、PR 和主分支保护。
- [发布流程](docs/发布流程.md)：JitPack、Release 归档、ohpm 与远程消费验证。
- [组件抽离路线图](docs/组件抽离路线图.md)：拟建组件、边界和实施顺序。
- [Issues 与迭代流程](docs/Issues与迭代流程.md)：接入反馈、修复 PR、发布和关闭 Issue。

跨仓库共用脚本放在本仓库的 `templates/` 或 `scripts/`；JitPack 需要在各项目检出中执行的脚本，应从模板同步副本并检查一致性。项目特有的构建参数、密钥和产物配置留在项目或受控环境中。不要提交或输出凭据。

新建仓库后，先确认默认分支为 `main`，运行 `scripts/protect-main.sh gycrosskit/<仓库名>` 并核验结果。GitHub Free 不能为整个组织配置自动覆盖未来仓库的 ruleset；脚本失败时要明确报告该仓库尚未受保护。
同时确认仓库启用了 Issues，让真实接入项目在组件仓库反馈问题；维护任务开始时先检查对应仓库的未关闭 Issue。
