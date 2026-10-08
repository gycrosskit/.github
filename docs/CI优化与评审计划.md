# CI 优化与组件评审计划

2026-10-08。本轮覆盖 14 个有组件 CI 的仓库：media、scanner、permission、location、sound、system-actions、wechat、compose-webview、live-sdk、debug-tools、customer-service、toast、jverification、diagnostics。MMKV / Koin / Stately 三个上游 fork 没有同样的 GitHub CI，另列本地构建与远程消费，不虚报已经套用流水线。共用 `.github` 是模板和规则源。

## 执行与验收

| 项目 | 实施内容 | 本地验收 | 上线后验收 |
| --- | --- | --- | --- |
| 分离阶段 | PR 按变更范围验源码；main 只做脚本/配置语法核对；Release 或显式版本 dispatch 验公开制品 | 14 库事件、步骤和原 required job 名检查；未知路径/范围失败保守运行源码 | 纯文档 PR、源码 PR、main 和指定版本 dispatch 各验证一次实际事件路径 |
| 严格校验去重 | 单一 verify-public 校验冻结归档、标签与全部 publication，再启动 Android / Native 独立消费者 | 每库每个发布事件的全量严格校验调用由两次减为一次；原平台命令保留 | 实际验证相同精确版本，消费者不用源码/staging 替换 |
| 缓存与等待边界 | 按 OS、CPU 和工具链配置缓存 Native 下载；只在成功后保存，排除未完成下载；Gradle 步骤与外部下载有上限 | 成功缓存条件/键检查；真实子进程验证退出码、静默编译、字节停滞及后代清理 | 同版本工具链的冷、暖缓存对照，记录 cache hit、下载字节、执行时间；排队单列 |
| 网络与就绪 | 每请求最多三次，仅瞬时网络错误重试；明确未就绪状态最多等待 300 秒，必要时请求精确 POM 一次触发构建 | 503、404、截断、TLS EOF/证书错误、未就绪后成功、超时与真实构建失败分别回归 | 新 tag 首次公开验收，检查首响应、最终状态及真实消费者；不重建或覆盖旧 tag |
| 失败证据与传播 | 校验前保存编号原响应；日志与逐次 JSONL 收据始终上传；范围/公开校验失败显式传回原 required job | 实际 shell 验证 success/failure/cancelled/skipped；只传小型诊断，不上传重复二进制 | 失败时能区分下载、就绪、源码、消费编译和排队；没有 proof 不算公开验收通过 |
| 版本与夹具 | Release 只接收明确版本，删除不再使用的历史 baseline 默认值；新 API 探针按真实版本合同启用 | system-actions rc.5/rc.6 file-actions 探针及旧版、未知版本、当前源码版本边界检查 | 下次版本更新时先通过 PR 的版本合同检查，再冻结和发布 |
| 固定评审方法 | 适配鸣岐的能力调用链、行为与精简两轮检查、反向复审 | [组件评审技能](../skills/gycrosskit-component-review/SKILL.md)结构/链接及独立检查 | 每次专项审查交付完整能力范围清单、排除项、测试映射和证据层级，定向审查不宣称全库通过 |

本轮代码与本地检查完成后再按已有 Git Flow 提交和合入；未提交的候选不代表 GitHub 已生效。线上实际时间与命中率必须在合入后测量，不把少跑 job 的数量换算成未经测量的提速百分比。文档流程的目标是执行时间不超过 5 分钟，排队另算；平台编译不承诺固定分钟数。

## 原有验收保留什么

- 原 contracts、android、native、release-android、release-native 名称保留。纯文档或不适用事件会明确跳过/轻量完成，不宣称编译执行；范围判断失败必须使原 required contracts 失败。公开证明失败也必须使消费者门禁失败。
- PR 不再反复编译历史远程 baseline。它验证的是源码候选；新版本公开后的精确消费者仍独立执行。修复消费者本身时保留其最小本地回归，并可显式 dispatch 已发布版本验证，不把旧制品当成新源码证明。
- 原平台行为测试、Swift typecheck、Native 最终链接、真实 Kuikly Render 与已有 HAR 检查按原适用范围保留。缓存与去重不改变编译目标、关闭测试或放宽 hash/commit/public/inventory 校验。
- 不自动重跑失败的 Gradle 构建或行为测试；可重试的是公开只读网络请求。下载停滞依据明确的 Native 字节进度，不能因编译静默就终止编译。队列没有 runner 时不能靠仓库脚本消除等待。
- 已发布源码、tag、Maven 归档与 HAR 不因 CI 修改而覆盖；本轮不升级 Kotlin/Gradle/SDK、不改组件生产逻辑、不移除 CMP。

## 评审如何避免反复漏项

评审的事实源仍是各组件 docs/功能与平台差异.md、测试与公开入口。专项全库审查先列出全部范围内能力，逐项追入口、状态 owner、平台调用、回调、取消与释放，分别检查 CMP Android/iOS 和 Kuikly Android/iOS/OpenHarmony。再独立检查精简，最后反向检查和对齐完整范围清单。

已发现问题先按共同根因修复，并保留能复现的最小回归；不能靠增加保护层或把编译通过写成跨品牌/设备业务一致来结案。阶段性结论明确分源码、替身/行为测试、SDK/模拟器/设备、远程渠道和宿主接线；没有发现也说明未覆盖范围，不保证零缺陷。鸿蒙直播/客服仍按用户范围排除。

## 来源

- 评审执行方法适配自鸣岐 skills/sxmqlive-platform-code-review/SKILL.md，不复制宿主业务、品牌、Jenkins 或目录规则；源码快照与适配验证见本轮交付收据。
- Native 缓存与按需要构建：[Kotlin 官方说明](https://kotlinlang.org/docs/native-improving-compilation-time.html)。
- 事件、条件、依赖、并发与超时：[GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)。
- 精确构建状态：[JitPack API](https://docs.jitpack.io/api/)。
