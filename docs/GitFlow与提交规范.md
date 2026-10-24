# Git Flow 与提交规范

## 分支与 PR

- `main` 是默认主分支。日常修改从实际目标分支创建短期分支，经 PR 合并；不直接推送、强推或删除主分支。
- AI 分支使用 `codex/<任务>`；人工开发可使用 `feature/<任务>`、`fix/<问题>`、`hotfix/<问题>`。已启用仓库的任务 PR 指向下节登记的开发线，其余仓库保留当前 PR 入口；独立验证及保护规则按实际验收分阶段切换。
- 先确认目标分支。Koin、Stately 的 OpenHarmony 适配位于各自的 `codex/ohos-*` 分支，默认 `main` 是上游基线；适配修改应向适配分支发 PR，不把默认分支的构建结果当作适配结果。
- 组件先完成相关本地轻量检查及统一 Jenkins 编译、回归和消费验证，通过后再创建 MR/PR；真机问题另行设备复验，不以源码门禁替代。本地受阻先说明，不默认先提评审或发版；例外需用户明确决定。
- PR 写明修改原因、验证命令与结果、未验证范围。合并前确认目标分支、差异范围和必要检查的最终结果；发布标签只从确认的发布提交创建，不覆盖已有标签。

## 提交

一次提交只解决一个可说明的问题。沿用 `type(scope): summary`，常用类型为 `feat`、`fix`、`docs`、`test`、`build`、`refactor`、`chore`，例如 `fix(toast): preserve KMP variants on JitPack`。提交前检查 `git diff --check` 和暂存内容，不夹带生成产物、凭据或无关文件。删除旧发布产物时，先按[发布流程](发布流程.md)验证新坐标。

## 主分支保护

现有公开仓库的 `main` 应要求 PR、对管理员生效，并禁止强推和删除。规则不预设审核人数或 CI 检查；仓库有稳定的审核人和 CI 后再增加对应要求。使用 [`scripts/protect-main.sh`](../scripts/protect-main.sh) 为新仓库设置同样规则，并用 GitHub API 回查。

GY CrossKit 当前为 GitHub Free，组织级 ruleset 不能自动覆盖未来仓库；因此创建新仓库后必须立即运行脚本。私有仓库的分支保护目前受套餐限制，脚本失败时不得称其已受保护。若将来升级到支持组织级 ruleset 的套餐，可改为覆盖所有仓库默认分支的组织规则，并核验新建仓库确实继承。

## GitFlow 分阶段启用

切换按仓库执行，不以共用文档合并或本地测试宣称全部生效。开发线启用与 Jenkins 门禁迁移分别验收。现有 Actions 与必需检查保留；18 项冻结源码验收、release/hotfix 的真实 PR 事件/回填、稳定线晋级、正式发布和公开消费分别验收。全部替代证据齐全后再逐库调整必需 context 并通过 Actions API 停止执行，保留 YAML 合同文件，不能先停掉唯一有效门禁。当前发布、诊断窗口由各主责会话交接。

| 仓库 | 稳定维护线 | 开发线及当前状态 |
| --- | --- | --- |
| live-sdk、wechat、jverification、media、permission、location、sound、toast、system-actions | `main` | `dev` 已启用，任务 PR 指向 `dev` |
| compose-webview、customer-service、debug-tools、diagnostics、dynamic-page、scanner | `main` | `dev` 待逐库启用；冻结候选尚不能说已合入稳定线 |
| koin-ohos | `codex/ohos-4.1.1`，`main` 保留上游基线 | `dev/ohos-4.1.1` 已启用 |
| stately-ohos | `codex/ohos-2.1.0`，`main` 保留上游基线 | `dev/ohos-2.1.0` 待启用；本次未查到该 ref，按实际维护线评审 |
| mmkv-ohos | `main` | `dev/ohos` 待启用，保留已有上游 `dev`，不误用为 OHOS 开发线 |

2026-10-24 启用上述九库 `dev` 时，从各自当时 `main` 创建，沿用原有分支保护：要求 PR、对管理员生效、禁止强推和删除，保留 `contracts`、`android`、`native`、`release-android`、`release-native` 五个 Actions 必需检查；默认分支仍为 `main`。不得在尚未取得对应仓库 Jenkins 准入和真实回填证据前，把新 Jenkins context 设为必需检查，也不得移除旧 Actions。截至 2026-10-25，18 库已分别完成冻结源码的 Jenkins 验收，原 CI/helper、真实报告、声明跳过与未覆盖边界逐项保留；不把这些源码收据转记为任意新 merge SHA 已重跑，也不据此宣称 package、正式发布、公开消费或事件/分支保护全部验收。九库开发 PR 的合并不等于候选已晋级 main，另外六库的 dev 仍未启用。公共规则仓库 `.github` 的文档 PR 仍指向 `main`。

开发任务 PR 到绑定的开发线并运行 CI；release 从已冻结的开发线创建，hotfix 从对应生产 Tag 创建。
release/hotfix 对完整 SHA 独立验证后 PR 到稳定维护线，核对当前源、基线、结果树和本次必需检查的准确回填；同 tree 复用保留原证据身份，变化或证据缺失时实际重新验证；
发布修复回流开发线，热修复回流活动 release 或开发线，回流冲突解决后重新验证。不得把上游维护分支重命名或覆盖以凑齐命名。

提交校验只针对新增普通提交，保留 Git 自动 merge/revert 和历史基线；本地 Hook 不能代替远端强制检查。
目标保护禁止直接推送、强推和删除稳定/开发线，对管理员也生效；保留已有更严格的检查，不使用默认模板覆盖现有规则。
