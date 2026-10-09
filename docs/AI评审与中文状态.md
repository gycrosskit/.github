# AI 评审与中文状态

共用仓库维护评审规则和状态同步实现，组件仓库维护自身能力、平台差异和验证合同。Codex 负责评审；GitHub Actions 只同步已有的固定状态说明。

## 自动评审

在 Codex 的 Code Review 设置中连接并启用组件仓库的 Automatic review。组织目标是待审查 PR 创建时和草稿转为 ready for review 时自动评审；逐库核验实际 Review trigger 设置及真实事件，不把 Actions wrapper 存在当成自动评审已启用。设置入口与权限条件见 [OpenAI 官方文档](https://learn.chatgpt.com/docs/third-party/github)。

把 [Code Review Rules 模板](../templates/code-review-rules.md) 合入各库适用的 `AGENTS.md`，已有规则按最小差异合并。评审意见用中文，保留 API/类名；按各库公开入口、`docs/功能与平台差异.md` 和测试追查受影响调用链。专项全库检查仍用[组件评审技能](../skills/gycrosskit-component-review/SKILL.md)，自动 PR 评审不等于全库或全平台验收。

只评审，不自动修复、不自动合并。修复需要独立任务授权，合并仍遵守[Git Flow 与提交规范](GitFlow与提交规范.md)及原 CI/分支保护。Codex 的无问题提示仅代表该次审查结果。

## 接入中文状态

1. 先发布本仓库 [reusable workflow](../.github/workflows/review-status-zh.yml)，记录实际包含该文件的完整 40 位 commit SHA。
2. 将 [wrapper 模板](../templates/review-status-zh.yml) 放入组件库 `.github/workflows/review-status-zh.yml`，把 40 个 `0` 的占位值换成该 SHA。固定 `gycrosskit/.github/.github/workflows/review-status-zh.yml@<完整SHA>`，不引用浮动分支或 tag；无需复制 Python、checkout 消费者源码或传递额外 secret。
3. 通过 PR 合入组件库默认分支。`issue_comment` 工作流需存在于默认分支才响应评论事件；确认 Actions 策略允许调用该公共共用 workflow，并保留 `pull-requests: write`。调用方无法给共用任务提升权限。
4. 在真实组件 PR 检查 Codex 固定英文 summary/no-findings 的 `created` 和 `edited`：中文副评论应复用同一 marker，源评论折叠且正文不被覆盖，真实问题评论保持原位置。分别验证自动评审与中文同步，记录 PR、源评论、中文评论和 Actions run。

reusable workflow 的 GitHub 上下文和 token 来自调用方，`GITHUB_REPOSITORY`、`GITHUB_EVENT_PATH` 与 `GH_TOKEN` 因而定位组件仓库。[GitHub reusable workflow 文档](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)说明调用方上下文与 token 的权限边界。共用 workflow 同时监听本仓库 `issue_comment` 的 `created` / `edited`，沿用相同的 bot 身份和 PR 校验，使自身原生评审评论也能同步中文；同样须先合入默认分支并验证真实事件。消费者模板只有 `issue_comment` 监听，不发送评审请求，不修改组件源码。

## 同步边界与验证

只处理身份三重匹配的 Codex bot：user id `199175422`、login `chatgpt-codex-connector[bot]`、type `Bot`；任务内再次检查 API 返回的作者。只翻译固定 summary/no-findings 文案、状态和北京时间，保留提交 SHA、链接和非固定内容；输出含触发 bot 的文本时失败，不发布该副评论。

中文副评论使用源评论 ID marker，分页查找并更新已有副评论。按源评论 ID 串行执行，同步后折叠原文；不 PATCH Codex 原始正文，避免与 bot 的异步状态更新互相覆盖。源原文是权威来源，中文副评论可能在下一次 `edited` 事件到来前短暂滞后。未知模板保持原文，翻译失败在 Actions 中可见，不宣称成功。

共用 PR 的 [template-regression](../.github/workflows/template-regression.yml) 执行 `python3 scripts/test-review-status.py`，共 11 项离线回归：固定文案、真实问题保留、作者校验、分页去重、并发源更新和消费者调用合同，以及[真实自动 no-findings 全文夹具](../scripts/fixtures/review-status-auto-no-findings.txt)的安全发布与 `Draft marked ready` / `PR opened` / 既有 `Pull request opened` 字段翻译。夹具取自[已观测的 bot 评论](https://github.com/can1357/oh-my-pi/pull/8017#issuecomment-5278231782)，仅规范行尾空白；未知触发文本仍拒绝发布。不访问 GitHub，离线通过不证明 Actions 权限、GraphQL 折叠或真实事件已上线；每库真实事件验收另行记录。
