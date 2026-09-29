# Git Flow 与提交规范

## 分支与 PR

- `main` 是默认主分支。日常修改从实际目标分支创建短期分支，经 PR 合并；不直接推送、强推或删除主分支。
- AI 分支使用 `codex/<任务>`；人工开发可使用 `feature/<任务>`、`fix/<问题>`、`hotfix/<问题>`。发布准备需要独立维护时再使用 `release/<版本>`；目前不额外引入没有实际用途的 `develop` 分支。
- 先确认目标分支。Koin、Stately 的 OpenHarmony 适配位于各自的 `codex/ohos-*` 分支，默认 `main` 是上游基线；适配修改应向适配分支发 PR，不把默认分支的构建结果当作适配结果。
- PR 写明修改原因、验证命令与结果、未验证范围。合并前确认目标分支、差异范围和必要检查的最终结果；发布标签只从确认的发布提交创建，不覆盖已有标签。

## 提交

一次提交只解决一个可说明的问题。沿用 `type(scope): summary`，常用类型为 `feat`、`fix`、`docs`、`test`、`build`、`refactor`、`chore`，例如 `fix(toast): preserve KMP variants on JitPack`。提交前检查 `git diff --check` 和暂存内容，不夹带生成产物、凭据或无关文件。删除旧发布产物时，先按[发布流程](发布流程.md)验证新坐标。

## 主分支保护

现有公开仓库的 `main` 应要求 PR、对管理员生效，并禁止强推和删除。规则不预设审核人数或 CI 检查；仓库有稳定的审核人和 CI 后再增加对应要求。使用 [`scripts/protect-main.sh`](../scripts/protect-main.sh) 为新仓库设置同样规则，并用 GitHub API 回查。

GY CrossKit 当前为 GitHub Free，组织级 ruleset 不能自动覆盖未来仓库；因此创建新仓库后必须立即运行脚本。私有仓库的分支保护目前受套餐限制，脚本失败时不得称其已受保护。若将来升级到支持组织级 ruleset 的套餐，可改为覆盖所有仓库默认分支的组织规则，并核验新建仓库确实继承。
