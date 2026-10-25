# AI 评审与中文状态

共用仓库维护评审规则，组件仓库维护自身能力、平台差异和验证合同。Codex 负责评审，CI 由 Jenkins 执行。

## 自动评审

在 Codex 的 Code Review 设置中连接并启用组件仓库的 Automatic review。组织目标是待审查 PR 创建时和草稿转为 ready for review 时自动评审；逐库核验实际 Review trigger 设置及真实事件，不把 Actions wrapper 存在当成自动评审已启用。设置入口与权限条件见 [OpenAI 官方文档](https://learn.chatgpt.com/docs/third-party/github)。

把 [Code Review Rules 模板](../templates/code-review-rules.md) 合入各库适用的 `AGENTS.md`，已有规则按最小差异合并。评审意见用中文，保留 API/类名；按各库公开入口、`docs/功能与平台差异.md` 和测试追查受影响调用链。专项全库检查仍用[组件评审技能](../skills/gycrosskit-component-review/SKILL.md)，自动 PR 评审不等于全库或全平台验收。

只评审，不自动修复、不自动合并。修复需要独立任务授权，合并仍遵守[Git Flow 与提交规范](GitFlow与提交规范.md)及原 CI/分支保护。Codex 的无问题提示仅代表该次审查结果。

## 中文状态

GitHub Actions 已停用，旧中文副评论 workflow、wrapper 和专用测试已删除。评审意见直接遵守组件 `AGENTS.md` 的中文规则；自动评审是否启用仍须核验实际服务设置，不能由 Jenkins 成功推断。
