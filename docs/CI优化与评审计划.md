# CI 优化与组件评审计划

下文保留 2026-10-08/18 的 Actions 改造与测量，不作为当前 dispatch/预热指令。2026-10-25 的 18 库源码验收与 Jenkins 入口准备见[统一远程验证](统一远程验证.md)，发布进度见[发布流程](发布流程.md)；源码已验收不等于包/公开消费/事件保护全切换，不再调用旧 warm_native_cache dispatch。

## 2026-10-26 Jenkins 复盘与待优化项

本轮按实际 Run 区分锁等待、队列、工具准备、候选复制、SDK 编译、发布以及公开消费；并行阶段不能相加为总耗时。28 项 SDK 逻辑生产对应 29 个实际 Run，含一次失败，整体约 2 小时 47 分；19 项 Native 源码渠道生产约 7 分 28 秒。Maven/HAR 的含排队中位数分别约 18 分 05 秒、12 分 38 秒，不是纯编译或依赖下载时间，也不能据此估算单项优化的收益。

| 观察到的问题 | 后续最小优化 | 验证方式 |
| --- | --- | --- |
| `mac-tools` 单 executor 串行准备和收尾，大候选复制占据时间 | 先量出 executor 等待和复制耗时，再评估移出大文件传输或复用已验证只读候选 | 同大小候选的前后计时、字节及摘要一致性；不绕过生产者身份 |
| 工具准备复制约 2.14 GB Harmony、901 MB Native 内容；不全是公网下载 | 按平台及工具链摘要复用受控只读工具包，分别统计本地复制与网络下载 | 记录冷暖命中、复制/下载字节；实际编译与测试仍执行 |
| 本轮原共享 Gradle 缓存包含依赖 artifact，metadata、POM 等仍有重复下载；后续已补固定 Gradle 8.11.1 的独立 metadata 供应 | 按实际 Gradle 布局和摘要限定复用；Robolectric、Pod、OHPM 等缺口分别确认 | 供应成功与真实命中、请求减少、提速分别验收；保持同工具链和公开字节校验 |
| 四槽准入仍只有两项 Mac 重编译能力，准备与收尾共用 executor | 按现有资源预算改善阶段重叠；不直接扩成四个 Mac worker | 用实际 slot/backend/executor 时间线确认收益及资源归还 |
| CI SHA 已更新，但 release 内嵌 guard 没同步，四次任务在加载前失败 | 完整 canonical 渲染、部署后回读及实际 CPS 检查一并执行 | 固定 CI、runtime、guard 和精确审批一致；不把失败重标成功 |
| 加载前失败没有 journal；artifact 保留窗口可能回收历史证据 | 仅识别可证明的已知无写入失败；在回收前保留确有恢复/验收依赖的准确 Run | 未知历史继续阻断，保留原失败和 journal；不扩大清理权限 |
| 公开复验入口 mock 未执行私有输出目录前置条件，Run105 两平台在编译前因缺父目录失败 | 入口新建 0700 父目录，沿用原有目录安全校验；模拟入口执行真实 shell 和目录函数 | 旧入口先红、新入口转绿，覆盖遗留目录、权限和归档失败，再做真实流水线验收 |

本轮已按维护者最新要求调整顺序：先完成职责、状态/产物说明、重复编译与下载、计时及恢复去重的优化，经 Review、CI、部署与代表组件验收后，才恢复剩余发布。当前源码变更和定向回归不代算部署通过；依赖 metadata 供应成功也不代算冷暖消费收益。SSH UTC/PID 日志与专用用户的有界失联回收已在全局 drain 后应用并独立回读，七个指定 agent 在线；首次 exit255 原因仍未知。大型工具包中转尚未消除，若改为封存镜像只读供应，须重新资格验收并保留旧镜像及证据，不挂载宿主缓存。

实际只读网络超时与 SSH 退出仍按原日志保留，未证实根因的不归为 OOM 或缓存故障。以上项目尚未做完整冷暖对照，不承诺提速百分比。HAR 归档与 OHPM 提交、上架、安装和 ArkTS 消费分别统计，不能将归档成功计为 Registry 发布完成。三个 Job 的状态与产物解释见[发布流程](发布流程.md#任务说明状态与产物)，发布前的 Review 检查见[发布前](发布流程.md#发布前)。

2026-10-08。本轮覆盖 14 个有组件 CI 的仓库：media、scanner、permission、location、sound、system-actions、wechat、compose-webview、live-sdk、debug-tools、customer-service、toast、jverification、diagnostics。MMKV / Koin / Stately 三个上游 fork 没有同样的 GitHub CI，另列本地构建与远程消费，不虚报已经套用流水线。共用 `.github` 是模板和规则源。

2026-10-18 后续源码候选已转为 core、原生与 Kuikly 维护入口，保留 Kuikly Compose，退出独立 CMP UI；当前能力见[组件文档索引](组件文档索引.md)。下文“不移除 CMP”描述的是 10 月 8 日 CI 改造范围，保留当时发布与验证事实。

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

## 发布提速的执行入口

14 库已合入的实现复用各库 Source regression 的 `native` job，增加 `warm_native_cache` 布尔输入；不新增自动全量构建或发布 job。只有在 `main` 手动打开该输入、且版本输入留空时，才运行工具链预热。正常 main push 仍轻量；未指定预热的空版本 dispatch 仍执行源码回归。源码门禁和 main 轻量检查已实际通过，缓存命中与公开消费者另行验收。

- 各库 `gradle/native-toolchain.properties` 固定实际编译器、目标与缓存修订；与源码/consumer 的 Kotlin 版本不一致时直接失败。客服使用官方 `2.2.21` 和 iOS，其他库使用鸿蒙 fork `2.2.21-1.0.0` 和实际 Native 目标，不混用。
- `scripts/ci-native-cache.py --key` 由编译器清单、预热实现、OS/CPU、实际 Xcode 版本生成身份。业务版本、README 和无关 consumer 配置不再改变工具链 key；编译器/目标/Xcode/预热实现变化会改变 key。
- 首次在可信 main 填充完整工具链缓存后，PR 与 Release 优先恢复该缓存；miss 后的成功构建仍可保存自身 ref 的缓存。PR 缓存不能供 tag 恢复，不能靠相同 restore-key 绕过 ref 范围；每库独立预热，不假设跨仓库共享。
- 预热 miss 才编译临时目录中的最小 iOS Framework/OHOS shared library 探针，填充编译器与 LLVM；hit 时跳过探针。不编译组件业务源码，不发布制品；所有源码测试、远程 public 与 consumer 门禁保留。
- Release workflow 不再运行无输出消费者的第二次 scope 分类；`release-android`/`release-native` 保留原 required 名称，依赖 public 成功。包内模块根 README/CHANGELOG 只有同目录存在 `oh-package.json5` 时视为维护文档，manifest/ETS/未知目录及混合源码改动仍运行源码门禁。

Media 试点已完成：[首次 main 预热](https://github.com/gycrosskit/media/actions/runs/37787758499)的 Native job 运行 10 分 56 秒，保存约 802 MB 的 main 工具链缓存；[第二次预热](https://github.com/gycrosskit/media/actions/runs/37790413889)命中相同精确 key，运行 1 分 10 秒并跳过探针与重复保存；[0.1.8 精确公开消费者](https://github.com/gycrosskit/media/actions/runs/37790427457)的 public、Android、Native 均成功，Native 恢复同一 main key。首次运行仍有既存 Gradle 缓存，上述对照仅代表这两次预热 job，排队另计，不能外推为整体发版提速比例。其余库按同样入口填充各自 main 缓存；工具链未变且缓存仍在时不重复预热，清理或输入变化时再执行。

发布按渠道生产变化选择集合，不要求 14 库每次齐发。版本、源码、文档和 checksum 一次冻结后开 PR；同一冻结归档只生产一次，同一版本 public 严格验一次，失败只重跑失败项。公开只读核验可限量并行，本机重构建保留内存/工具链锁；现有证据不足以把十几秒本地锁等待当成主要瓶颈，暂不加新调度框架或取消构建锁。

14 库修复均已通过原源码门禁并正常合入，未绕过主分支保护。本轮生产变化只发布 [Sound HAR 0.1.2](https://github.com/gycrosskit/sound/releases/tag/har-0.1.2)，专用 Release 校验运行 19 秒并成功，Maven/iOS 任务按渠道跳过；固定 HAR 的独立远程消费通过。OHPM 接受提交但仍审核中，未将其写成 Registry 已可用。线上时间按实际运行记录，不把少跑 job 的数量换算成未经测量的提速百分比。文档流程的目标是执行时间不超过 5 分钟，排队另算；平台编译不承诺固定分钟数。

## 原有验收保留什么

- 原 contracts、android、native、release-android、release-native 名称保留。纯文档或不适用事件会明确跳过/轻量完成，不宣称编译执行；范围判断失败必须使原 required contracts 失败。公开证明失败也必须使消费者门禁失败。
- PR 不再反复编译历史远程 baseline。它验证的是源码候选；新版本公开后的精确消费者仍独立执行。修复消费者本身时保留其最小本地回归，并可显式 dispatch 已发布版本验证，不把旧制品当成新源码证明。
- 原平台行为测试、Swift typecheck、Native 最终链接、真实 Kuikly Render 与已有 HAR 检查按原适用范围保留。缓存与去重不改变编译目标、关闭测试或放宽 hash/commit/public/inventory 校验。
- 不自动重跑失败的 Gradle 构建或行为测试；可重试的是公开只读网络请求。下载停滞依据明确的 Native 字节进度，不能因编译静默就终止编译。队列没有 runner 时不能靠仓库脚本消除等待。
- 已发布源码、tag、Maven 归档与 HAR 不因 CI 修改而覆盖；本轮不升级 Kotlin/Gradle/SDK、不移除 CMP。功能源码仅清理 Sound 重复就绪状态，保留原行为并运行既有回归。

## 评审如何避免反复漏项

评审的事实源仍是各组件 docs/功能与平台差异.md、测试与公开入口。专项全库审查先列出全部范围内能力，逐项追入口、状态 owner、平台调用、回调、取消与释放，分别检查 Android/iOS/OpenHarmony 的 core、原生与 Kuikly 实际接线。旧 CMP 入口按历史 tag 处理。再独立检查精简，最后反向检查和对齐完整范围清单。

已发现问题先按共同根因修复，并保留能复现的最小回归；不能靠增加保护层或把编译通过写成跨品牌/设备业务一致来结案。阶段性结论明确分源码、替身/行为测试、SDK/模拟器/设备、远程渠道和宿主接线；没有发现也说明未覆盖范围，不保证零缺陷。当时鸿蒙直播/客服按该轮用户范围排除。

## 来源

- 评审执行方法适配自鸣岐 skills/sxmqlive-platform-code-review/SKILL.md，不复制宿主业务、品牌、Jenkins 或目录规则；源码快照与适配验证见本轮交付收据。
- Native 缓存与按需要构建：[Kotlin 官方说明](https://kotlinlang.org/docs/native-improving-compilation-time.html)。
- 事件、条件、依赖、并发与超时：[GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)。
- 精确构建状态：[JitPack API](https://docs.jitpack.io/api/)。
