# 组件测试与 API 审查

## 完整复审与当前收尾状态

2026-10-05 再次按各仓库的完整文件清单读取全部自有生产实现、公开入口、平台桥、相关调用者和最终 diff，重点覆盖线程、owner、取消、迟到回执、错误分类、三端契约、资源释放与最低系统。逐文件 SHA 和回归日志保留在各库忽略的 `build/full-review/`；公开文档列出实际文件范围与验证结果。第三方 SDK 内部、生成代码和宿主业务不混入“自有源码全部审查”的承诺。

本轮的“完成”要求是：确定缺陷修复、公开契约及平台限制写清、受影响回归实际通过、产物与源代码一致、不可变发布、各实际消费渠道复验，再交给宿主接入。源码阅读或本地 staging 编译不是远程消费通过。本轮所有自有组件的确定、可修复缺陷均已修复并完成相应发布与真实远程消费；各渠道的实际范围见下表，历史阶段记录保留在后文。

| 组件 / 完整审查 | 本轮改动与版本 | 当前验证范围 |
| --- | --- | --- |
| [permission](https://github.com/gycrosskit/permission/blob/main/docs/完整源码审查.md) | Maven/HAR `0.1.5`：原生公开类型导出；只有成功启动的请求更新历史；注册/启动异常不冒充拒权 | 已发布，真实 Release HAR 新建消费通过；新建 Maven Android/iOS/OHOS 编译及 Simulator Framework 链接通过 |
| [media](https://github.com/gycrosskit/media/blob/main/docs/完整源码审查.md) | Maven/HAR `0.1.5`、Swift revision `native-0.1.3`：相机临时文件独占；启动失败清理；保存拒绝截断图片；maxCount 合同统一 | 已发布，新建 Maven Android/iOS/OHOS 编译及 Simulator Framework 链接、真实 Release HAR、远程 Swift 包 device/simulator 与 UIKit 回归通过；远程 Core Framework 与真实 Swift SDK 的完整 KmpMediaBridge typecheck 通过 |
| [scanner](https://github.com/gycrosskit/scanner/blob/main/docs/完整源码审查.md) | 没有新确定运行缺陷，保留 Maven `0.1.5`、HAR `0.1.3`、Swift `0.1.1` | 本轮逐文件复审与 Node 原生回归；不以文档变更触发二进制发布 |
| [location](https://github.com/gycrosskit/location/blob/main/docs/完整源码审查.md) | Maven/HAR `0.1.3`：iOS Restricted 正确归类；OHOS 拒绝负时间戳 | 已发布，真实 Release HAR 新建消费通过；新建 Maven Android/JVM/iOS/OHOS 编译及 Simulator Framework 链接通过 |
| [system-actions](https://github.com/gycrosskit/system-actions/blob/main/docs/完整源码审查.md) | Maven/HAR `0.2.0-rc.4`：OHOS 剪贴板、私有文件分享及 keepScreenOn 接线；失败保留租约以便重试 | 已发布，真实 Release HAR 与新建 Maven Android/iOS/OHOS 编译及 Simulator Framework 链接通过；Swift 包沿用 `0.2.0-rc.2` |
| [toast](https://github.com/gycrosskit/toast/blob/main/docs/完整源码审查.md) | 没有新确定运行缺陷，保留既有 `0.1.3` 配套 | 本轮逐文件复审与 Node 原生回归；未重跑未变化的 Kotlin/Swift/HAR 构建 |
| [sound](https://github.com/gycrosskit/sound/blob/main/docs/完整源码审查.md) | 没有新确定运行缺陷，保留 Maven `0.1.3`、HAR `0.1.0` | 本轮逐文件复审与 Node 原生回归；未重跑未变化的 Kotlin/Swift/HAR 构建 |
| [wechat](https://github.com/gycrosskit/wechat/blob/main/docs/完整源码审查.md) | Swift/Git Pod `native-0.1.4`：errCode=0 的空白 OAuth code 仍为失败，合法原文保留；Maven `0.1.5`、HAR `0.1.4` 不变 | 真实 Git Pod/UIKit App 与 SPM/device 编译通过；新建远程 Maven Core Framework + 实际 Native Framework 的完整 KmpWechatBridge typecheck 通过 |
| [jverification](https://github.com/gycrosskit/jverification/blob/main/docs/完整源码审查.md) | Maven/Git Pod `0.1.3`：6000 成功码但纯空白 token 正确失败；HAR `0.1.0` 不变 | 已发布，新建 Maven Android/JVM/iOS/OHOS 编译与 Simulator/device Framework 链接通过；真实 Git Pod/UIKit App及新远程 KMP/Swift 桥通过 |
| [customer-service](https://github.com/gycrosskit/customer-service/blob/main/verification/完整源码审查.md) | Maven/Git Pod `0.1.5`：syncProfile 资料同步回调后复核 owner、serial、实际身份与已知 AppId，拒绝 reset/外部接管后的旧成功 | 已发布，新建 Maven Android/iOS 编译与 Simulator Framework 链接通过；真实 Git Pod/UIKit App 通过 |
| [live-sdk](https://github.com/gycrosskit/live-sdk/blob/main/docs/完整源码审查.md) | Maven/Git Pod `0.2.1-rc.7`：Kuikly PiP 接线；实验 API 受理不冒充浮窗实际可见；切房清除旧 View 事件 | 已发布，新建 Kuikly/CMP APK、iOS device/simulator Framework 通过；真实 Git Pod/UIKit App、远程 KMP Framework+Render/View 最终链接通过 |
| [compose-webview](https://github.com/gycrosskit/compose-webview/blob/main/docs/完整源码审查.md) | Maven/HAR/Pod `0.2.0-rc.9`：文档/owner/可见性统一门禁、来源规范化、控制上传与资源撤销、组合导航规则；新增 Kuikly 全屏原生宿主 controls/方向参数及保留 DOM 的导航更新接线 | 已发布，82项 Android/77项 iOS 与真正 UIKit App 回归通过；新建远程 Kuikly/CMP APK、iOS Framework、OHOS .so、真实 Git Pod/UIKit App 与 Release HAR 消费全部通过。配套 system-actions HAR `0.2.0-rc.4` |
| [diagnostics](https://github.com/gycrosskit/diagnostics/blob/main/docs/完整审查.md) | Maven `0.2.0-rc.5`：OHOS Curl 通知闭环、RFC HMAC、HTTP 字节上限与严格 errcode、负快照大小拒绝 | 已发布，core/通知 Android/JVM/iOS 回归通过；新建远程消费者 Android/JVM、iOS Framework及core+通知 OHOS 最终 `.so` 通过。原生 Swift `rc.1` 不变 |
| [debug-tools](https://github.com/gycrosskit/debug-tools/blob/main/docs/完整审查.md) | Maven/HAR `0.2.0-rc.3`：初始化与命令隔离；初始恢复期间打开表单仍采集证据；原生严格 JSON 类型/键校验 | 已发布，新建 Maven Android/iOS/OHOS 编译及 Simulator Framework、真实 Release HAR 新建消费通过；Keychain 两项仍明确跳过 |

所有已发布变更的 Release 资产重新下载校验 SHA；Maven 每个 publication、实际 variant 文件、四种声明 hash、ZIP CRC、POM 身份/许可证及内部版本均逐项核验，并与冻结归档实际字节比较。公开 MD5/SHA-1 sidecar 通过；SHA-256/SHA-512 sidecar 的 HTTP404 仍是渠道缺失，不记为通过。新 HAR 的 OHPM 提交接受仅表示审核中：permission/media/location/system-actions/debug-tools/compose-webview 精确 Registry 安装本轮仍 NOTFOUND，实际安装验证使用同标签公开 Release HAR。

### 尚有外部契约限制

- **Live OHOS**：[腾讯鸿蒙直播 SDK 调研](https://github.com/gycrosskit/live-sdk/blob/main/docs/腾讯鸿蒙直播SDK调研.md)。公开 AtomicX/Room/IM 能力没有证明等价 LiveId、直播列表、直播 View 与互动协议；不能以聊天室或普通音视频 SDK 填空成功。Android/iOS 的真实音视频、账号与 PiP 仍需设备验收。
- **客服 OHOS**：[腾讯客服鸿蒙接入核查](https://github.com/gycrosskit/customer-service/blob/main/verification/腾讯客服鸿蒙接入核查.md)。腾讯 AI Desk uni-app 有鸿蒙支持，但当前原生 ArkUI/Kuikly 等价 HAR、初始化/身份/聊天/重置与企业配置契约未获取并验证；不能写成“腾讯没有鸿蒙客服”。
- **WebView 受控上传**：iOS 公开 WKUIDelegate 拦截从 18.4 才可用；普通网页仍支持 iOS15，15～18.3 的受控上传明确 Unsupported。UIKit MOV 不假装 MP4；DOM 提示不作为安全证明。OHOS fileSelector 不提供真实 frame/gesture 信息，文档中保留该平台边界。
- **图片保存**：API28+ 使用严格 ImageDecoder；API24～27、Swift 与 HAR 在真实小图解码前检查 PNG/JPEG/WebP 容器结束边界。它不是完整格式解析器，不能声称校验了所有压缩数据/CRC。
- **signal 9**：串行构建通过没有证明历史 signal9 的根因；保留“尚未明确归因”，不把本轮修复或内存压力推测写成结论。
- **Kuikly 官方 SDK 字体/语义**：[本轮上游核查](KuiklySDK上游核查.md)。不属于14个自有组件。官方 `2.28.0-2.0.21-ohos` 与核查主分支 `18252bca15c4215fb5c9a7e92013043aa3f903ba` 仍缺输入 fontFamily 连续接线；[PR #1419](https://github.com/Tencent-TDS/KuiklyUI/pull/1419) 已关闭且未合并，不能声称升级现成版本即可解决。真实官方 AAR 调用生产 `KuiklySemantisHandler.buildAccessibilityText` 输出 `English option, 已选择`；[源码](https://github.com/Tencent-TDS/KuiklyUI/blob/18252bca15c4215fb5c9a7e92013043aa3f903ba/compose/src/commonMain/kotlin/com/tencent/kuikly/compose/extension/KuiklySemantisHandler.kt) 还缺 Switch/Radio 与选中/禁用/错误的完整结构化桥接。已准备英文上游报告与最小复现，未将未编译建议或设备读屏列为修复/验收；不在业务组件重写输入控件或创建平行 SDK fork。

此轮回归曾捕获真实截断图片被 BitmapFactory/UIImage 接受，以及 WebView 旧回调、IPv6/DNS/脚本端口边界；失败日志与修复后结果均保留。完整复审应减少已知遗漏，但不承诺以后再审查必定零发现；设备、厂商服务和新的使用场景仍有独立验收范围。

## 历史阶段记录

审查日期：2026-10-05。范围为下表 14 个功能组件，依据各库本轮 `build/test-api-review/audit.md` 汇总。团队逐文件阅读自有生产源码、原生桥、现有测试和相关调用者，并补充关键契约回归；完整阅读不等于 100% 行为覆盖，也不代表所有平台已有动态测试。

**初轮源码验证：14 库定向测试与受影响平台编译完成；当前 Gradle XML 共 549 次测试执行，547 次通过、2 次 App-hosted Keychain 显式跳过、0 失败。** 同一测试在不同平台执行会重复计数，Node/Swift/Python 行为检查另行核验，不混作唯一测试数量。 下表记录已有测试行为与新增回归。Gradle XML、Node/Swift 行为检查及 Native 链接分别核验，不把测试代码存在视为通过。组件源码与测试链接指向公开仓库 `main` 的入口，具体本轮变更以合并后的源码为准。

## 关键回归与剩余边界

| 组件与源码 / 测试入口 | 已有关键行为 | 本轮关键回归 | 剩余平台边界 |
| --- | --- | --- | --- |
| [permission](https://github.com/gycrosskit/permission) · [源码](https://github.com/gycrosskit/permission/tree/main/permission-core/src) · [测试](https://github.com/gycrosskit/permission/tree/main/permission-core/src/androidUnitTest) | 权限历史与实时状态、拒绝/取消、Kuikly 销毁窗口、OHOS 系统状态 | Host 绑定与恢复、实时授权优先；取消后继与旧回执隔离；设置返回重读、未知状态拒绝与畸形桥输入 | 真实系统弹窗、ActivityResult 重放、iOS RunLoop、系统撤权与永久拒绝推断 |
| [scanner](https://github.com/gycrosskit/scanner) · [源码](https://github.com/gycrosskit/scanner/tree/main/scanner-core/src) · [测试](https://github.com/gycrosskit/scanner/tree/main/scanner-core/src/androidUnitTest) | 扫码 busy/暂停/释放、一次反馈、预览代次、临时文件清理 | 真实 QR 图片编码后经生产解码还原；空/损坏/无码图片；取消迟回执、零长度写入失败、open 挂起时销毁清理 | 真相机、声效/振动、Swift CoreImage/AVCapture、OHOS ScanKit Surface；Kuikly 预览事件仍缺独立行为 harness |
| [media](https://github.com/gycrosskit/media) · [源码](https://github.com/gycrosskit/media/tree/main/media-core/src) · [测试](https://github.com/gycrosskit/media/tree/main/verification-kuikly/src/test) | Main 与交付取消窗口、选择器替换/忙碌、原图/JPEG/32 MiB 限额、UIKit 转场与重入 | 坏 Base64 后可恢复；取消发送 requestId 并释放回调；部分读写完整性、零写入拒绝成功、拒权与相机失败分别结算 | MediaStore/Photos 真落盘、EXIF 与大图内存、FileProvider、物理拍照、多窗口；取消不能保证关闭系统 Picker 或回滚已开始写入 |
| [location](https://github.com/gycrosskit/location) · [源码](https://github.com/gycrosskit/location/tree/main/location-core/src) · [测试](https://github.com/gycrosskit/location/tree/main/verification-kuikly/src/test) | 新鲜度/精度/坐标准入、deadline、缓存、服务关闭与取消 | 超时/年龄/非有限数值端点；取消后继与旧回调隔离；迟位置不污染缓存、期限结束重读权限与服务状态 | Android GPS/NETWORK 监听解除、iOS delegate/manager 生命周期、OHOS off 后耗电与真定位 |
| [system-actions](https://github.com/gycrosskit/system-actions) · [源码](https://github.com/gycrosskit/system-actions/tree/main/system-actions-core/src) · [测试](https://github.com/gycrosskit/system-actions/tree/main/ohos/tests) | URL/phone 准入、Intent 与分享 grants、多 owner 窗口策略、观察取消 | 端口/IPv6/控制符等输入边界；非法输入不进系统；重复 ID 无第二笔动作；全屏系统栏数组快照隔离 | 真商店/拨号/设置、FileProvider 接收方、iPad 分享、系统栏与截图保护；Kotlin Kuikly 桥主要为编译检查 |
| [toast](https://github.com/gycrosskit/toast) · [源码](https://github.com/gycrosskit/toast/tree/main/toast-core/src) · [测试](https://github.com/gycrosskit/toast/tree/main/toast-core/src/androidUnitTest) | iOS 空白/时长转发、OHOS 输入与页面 owner 隔离 | Android 真实 Handler 队列只展示最新、替换 cancel、空白不淘汰当前/排队消息、LONG/SHORT；OHOS open 拒绝后恢复 | Robolectric/ShadowToast 不证明系统浮层外观、厂商限流；UIKit Scene/动画/VoiceOver；CMP CompositionLocal 缺独立 runtime 测试 |
| [sound](https://github.com/gycrosskit/sound) · [源码](https://github.com/gycrosskit/sound/tree/main/sound-core/src) · [测试](https://github.com/gycrosskit/sound/tree/main/sound-core/src/androidUnitTest) | HTTPS 准入、准备超时/失败回退、iOS 有界读取、RELEASED 终态 | 生产 Kuikly 模块的旧准备回调隔离、去重/失败重试、空址恢复与幂等释放；OHOS 本地准备失联/迟 create 释放播放器与 rawfile | 真扬声器、静音/焦点、系统播放器事件、网络与资源失败、Kuikly 调度；prepared 不保证完整缓存或离线可播 |
| [wechat](https://github.com/gycrosskit/wechat) · [源码](https://github.com/gycrosskit/wechat/tree/main/wechat-core/src) · [测试](https://github.com/gycrosskit/wechat/tree/main/wechat-core/src/commonTest) | state/transaction/kind 匹配、可信 journal、清除失败保留等待、取消确认与资源清理 | 非法恢复与超长 ID 拒绝、transaction 不复用、旧回执不消费新请求；Swift 未发送 share 候选隔离与安全取消重试 | 真微信/AppID/UniversalLink、跨进程磁盘、OAuth 换票与转账；iOS singlePending 仅为候选，确认页 success 不证明到账 |
| [jverification](https://github.com/gycrosskit/jverification) · [源码](https://github.com/gycrosskit/jverification/tree/main/jverification-core/src) · [测试](https://github.com/gycrosskit/jverification/tree/main/jverification-core/src/jvmTest) | 同意门禁、预取号不拉页、busy、超时/撤销、opened 唯一与凭据脱敏 | 协程取消释放 busy、旧 Token 不结束新尝试；close/dispose 只关闭一次；空 Token 失败、畸形 JSON/非布尔同意不进 SDK | 真 SIM/运营商网络、AppKey/品牌页、原生回调线程与关闭、隐私开关、Token 后端换票 |
| [customer-service](https://github.com/gycrosskit/customer-service) · [源码](https://github.com/gycrosskit/customer-service/tree/main/src) · [测试](https://github.com/gycrosskit/customer-service/tree/main/verification) | own/borrow/foreign 与 AppId、清理重试、展示失败和真实 dismiss 完成 | 非法/空白凭据与登录中拒绝、无效 Activity；取消仍等 SDK callback；清理失败重试；子页 disappear 不结算、重复 open/reset 不抢 completion | 腾讯真实账号/聊天、IM 与直播共用、UI 转场与 SDK 线程；OHOS 保持 unsupported |
| [live-sdk](https://github.com/gycrosskit/live-sdk) · [源码](https://github.com/gycrosskit/live-sdk/tree/main/live-core/src) · [测试](https://github.com/gycrosskit/live-sdk/tree/main/live-core/src/commonTest) | 账号清理权、join/leave 门禁、预览生命周期、关注回执代次、消息快照、IM 绑定与 Swift Account callback | 点赞首次/合并、失败批次恢复、release 后不重试、同步抛错不丢计数；Swift 空白凭据不进 SDK；Android 非法 login 输入在调用线程同步失败 | 真 AtomicX/IM、退房/声音画面、后台与互动、Native View；PiP 请求/实验回执不证明浮窗可见；无 OHOS/HAR |
| [compose-webview](https://github.com/gycrosskit/compose-webview) · [源码](https://github.com/gycrosskit/compose-webview/tree/main/webview-core/src) · [测试](https://github.com/gycrosskit/compose-webview/tree/main/webview-core/src/commonTest) | 来源/导航门禁、Bridge 文档隔离、文件/媒体控制器撤销、进度与首航预算、OHOS port/window owner | 错误 JSON 类型不能开启能力/改头；新声明独立首航恢复；OHOS 真实生成脚本来源拒绝、迟授权/URI 隔离与一次结算 | 真 WebKit/Chromium/ArkWeb、document-start 延迟兜底、ActivityResult、POST/cookies、权限与全屏；字符串断言不能代替浏览器执行 |
| [diagnostics](https://github.com/gycrosskit/diagnostics) · [源码](https://github.com/gycrosskit/diagnostics/tree/main/diagnostics-core/src) · [测试](https://github.com/gycrosskit/diagnostics/tree/main/diagnostics-core/src/commonTest) | 有界日志、批次重试/落盘/确认、真实归档与流式读取、Crash/ANR、DingTalk MockEngine | Swift 小数秒时间戳与非法范围；活动快照捕获长度、冻结原件增长拒绝确认；借用 transport 关闭隔离、非法 host 与响应形状 | 真 MetricKit/NSException、ANR、OHOS HiAppEvent、系统退出/磁盘失败；真实钉钉通知未验证 |
| [debug-tools](https://github.com/gycrosskit/debug-tools) · [源码](https://github.com/gycrosskit/debug-tools/tree/main/src) · [测试](https://github.com/gycrosskit/debug-tools/tree/main/src/commonTest) | 草稿/授权/目标隔离、UNKNOWN 防重、附件部分成功、journal/ACK、摇动与安全存储 | English 实际请求体标签；create 取消保留 UNKNOWN、附件读失败与已知 Bug 保留、远端成功后 journal 失败禁止重写；HUKS 错误/同 alias 队列隔离 | 两项真实 Keychain 测试仍显式跳过；Keystore/HUKS、传感器、Kuikly 生命周期、真实禅道创建/附件/通知由设备和业务环境验收 |

上述回归复用已有 common/platform tests、Robolectric、MockEngine、Swift callback harness 与 ArkTS harness。替身只承接 SDK、系统或传输边界，主要断言来自生产入口；纯策略测试、源码/字符串检查与真实平台行为分别说明，不按 getter、enum 或文件数量凑覆盖率。

## 公共 API 注释范围

补充自有 Kotlin、Swift、ArkTS 及 Objective-C 公开类型、方法、属性和构造参数：用途、默认值、单位/范围、输入失败、调用/回调线程、取消结果、owner 与资源释放、敏感数据边界。KDoc 可用 `@param`/`@property`；明确 override 继承可读契约，平台差异在声明或类级解释。

线程与所有权按实际平台收窄：Kuikly 页面线程不等同原生 Main；jverification 的 dispatcher 必须提供串行执行；Android/iOS 选图替换不外推为 OHOS Picker 保证。取消本地等待不承诺 SDK 请求、已打开页面或已开始写入均可撤销。

生成代码、第三方 SDK/上游源码、标准生成成员、构建/测试桩及消费示例不是自有公共 API 逐行注释对象；必要的接入与平台约束仍核对。私有赋值和简单转发不机械加注释，既有 README 图保留。

## 实际运行行为修复

| 组件 | 修复与兼容边界 | 影响的消费渠道 |
| --- | --- | --- |
| jverification | `close` 复用 `dispose`，同一次关闭只发送一笔 native close，保留代次与回调清理顺序 | Maven Kuikly 模块 |
| diagnostics | 识别 Swift 实际生成的小数秒 timestamp；保留整数秒/毫秒及 ISO，非有限/越界值回退 | Maven/KMP core 解析路径 |
| debug-tools | English 报告补 Actual result / Expected result 与长日志截断提示；保留默认中文公开签名及日志原文 | Maven/KMP 报告请求体 |
| customer-service | Swift 拒绝纯空白 userId/UserSig；只校验 trim 后非空，传给 SDK 的原文不变 | Swift Native Pod |
| live-sdk | Swift 同样拒绝空白凭据；Android 把原有 require 移到 Main 派发前，在调用线程同步拒绝非法输入 | Swift Native Pod、Maven Android |
| compose-webview | wire JSON 严格检查类型；iOS 新声明重置首航预算；独立 Native 修复 Boolean 装箱和 WebKit 规则编译，拒绝数字安全开关 | Maven core/Kuikly、CMP iOS；Git Pod0.2.0-rc.7 |

其余 8 库初轮无运行行为修复；测试依赖和 harness 增强不改变生产功能。纯注释/测试无需据此重复发布二进制；上述 6 库已发布修复 Maven 版本并通过干净远程消费。WebView HAR 保留原有配套；宿主真实日志追加暴露 iOS Kuikly 原生布尔编码问题，独立 Git Pod 补修为0.2.0-rc.7，单独完成发布与远程验收。

## 精简规则与验证结论

精简前追踪实际调用者，只删除确认未引用的常量/import、不可达分支和无价值私有转发；permission 的重复状态映射保持优先级。保留生命周期代次、取消屏障、owner 集合和平台差异，不引入单调用方 Wrapper/Manager、跨库框架或未来功能。新增注释/测试行数不作为生产优化收益。

各库详细生产审查清单、最小验证命令和遗留边界保留在其本轮 audit。根会话串行完成 Gradle 定向测试、Node/Swift 原生边界检查与受影响平台编译。media 的固定微任务等待和 system-actions 的 URI 编码断言已按实际契约修正后通过；live-sdk Kuikly iOS 首次缺失 Render C 符号，链接真实 arm64 Simulator Render 静态 Framework 后两项测试通过，最低 iOS 15 的 SDK 与运行器边界写入组件开发文档。2 项 App-hosted Keychain 测试保持显式跳过，未算为通过。6 个 Maven 修复版本已完成不可变发布与干净远程消费，WebView独立iOS Git Pod0.2.0-rc.7也已完成真实远程消费与UIKit App最终链接。源码静态检查、单元/harness 测试、Native 编译链接、不可变远程产物消费、真实设备与业务验收分别记录。真实通知、禅道写入、HUKS/Keychain 与厂商业务操作没有被 mock 结果代替。

## 初轮不可变发布

以下 6 个修复版本已发布；Git 标签、JitPack 最终 public/tag/commit 与 Release 归档重新下载 SHA 均一致。68 个 publications 的 153 个变体逐项核验了真实文件大小、四种声明哈希、POM 许可证、内部依赖及 available-at 目标。公开 MD5/SHA-1 的 136 个 sidecar 均通过；SHA-256/SHA-512 的 136 个 sidecar 返回 HTTP 404，作为渠道缺失记录，未记为通过。jverification/diagnostics 的 JitPack 顶层 component.url 被改写到 404 地址；实际变体与 available-at 正常，干净消费验证单独记录。

| 组件 Release | Maven 版本 | 标签提交 | Maven 归档 SHA-256 |
| --- | --- | --- | --- |
| [jverification](https://github.com/gycrosskit/jverification/releases/tag/0.1.2) | `0.1.2` | `7827c9f9307726fd55250e7653f665d672a60618` | `1514c9290fa7ba02bf82e1b59c8ace43d4481d0fa30ff20bb5b1169c9f66349a` |
| [diagnostics](https://github.com/gycrosskit/diagnostics/releases/tag/0.2.0-rc.4) | `0.2.0-rc.4` | `88690f9a41ac4498a184df38f058ab7849faeec0` | `d9142b53d885caad03220e216ac3d044523c14e2a761cc951d5615d2e5487ed5` |
| [debug-tools](https://github.com/gycrosskit/debug-tools/releases/tag/0.2.0-rc.2) | `0.2.0-rc.2` | `e3e5701e448a415c4ed05697f706cc05d5767a31` | `cd45b6f66ce2bb7bb955c541cd56d65a04e05dabc4d25cddd1ee100672bf87dd` |
| [customer-service](https://github.com/gycrosskit/customer-service/releases/tag/0.1.4) | `0.1.4` | `83b320fc1c7fa263a942fda0073ea9b6976420ef` | `cd4dc02bc34989816f24efcd7ed3b035eb06c816e9d66a347ace1ec6b2ce3df4` |
| [live-sdk](https://github.com/gycrosskit/live-sdk/releases/tag/0.2.1-rc.6) | `0.2.1-rc.6` | `5e641b598231139b5b39dfe8c164935c20b8a522` | `6dc24dfab7b3309a58591b14c1ed3cb97605cbaf048ca3236c0410eb69ac35bb` |
| [compose-webview](https://github.com/gycrosskit/compose-webview/releases/tag/0.2.0-rc.6) | `0.2.0-rc.6` | `1c416129648573aecd56106287dfcfb72b0ef9cd` | `0df6961df3b29518ca505433f3c1fe0f79bcfdf44e8c2831b73351762f335aba` |

customer-service Git Pod 0.1.4、live-sdk Git Pod 0.2.1-rc.6 从真实远程标签安装，lock 与标签提交核对，参与编译的 Swift 文件逐字节匹配，纯 UIKit iphoneos arm64 App 最终链接通过。没有以本地 :path Pod 代替远程消费。其余独立原生渠道保留既有配套：jverification Git Pod 标签0.1.1/HAR0.1.0；diagnostics SwiftPM/Git Pod0.2.0-rc.1；debug-tools HAR0.2.0-rc.1；WebView 新 Git Pod0.2.0-rc.7（已验收）/HAR0.2.0-rc.5及system-actions HAR0.2.0-rc.3。

干净远程消费者：jverification Android/JVM/iOS/OHOS，diagnostics core/dingtalk Android/JVM/iOS及core OHOS，debug-tools Android/iOS/OHOS，customer-service Android/iOS，以及Live/WebView各自Kuikly/CMP入口均通过。所有本组件固定远程坐标，禁止本地Maven/includeBuild/其他组件工程依赖，解析日志记录精确版本；AGP单元测试自身资源输出按实际契约放行。diagnostics首轮被守卫误判为本地组件，修正后以原完整任务重跑通过，未删测试或替换远程产物。

## 宿主日志追加的 iOS 原生回归

宿主真机日志 `0 does not represent a Boolean → WebViewWire.boolean → decodeEvent → GYWebViewEvent.onEvent` 暴露了本轮最初未捕获的 Native 生产者编码缺陷。Objective-C 的逻辑/比较表达式被装箱为NSNumber int，JSON生成0/1；事件、命令及规则字段改为显式@YES/@NO，保持严格解析。原生安全开关拒绝数字伪布尔；新 UIApplication Simulator App直接编译生产GYWebView.m，链接真实Render，检查实际JSON往返/CFBoolean、输入类型、导航和命令。真实WKContentRuleList编译还发现原有host规则使用不支持的disjunction；依照 [WebKit正则子集](https://webkit.org/blog/3476/content-blockers-first-look/) 改为可选路径及末尾锚点并验证host/port/path和相似域名边界，真实WebKit四类规则编译通过。新增Kotlin事件布尔类型Android/iOS回归通过，未用放宽解析或吞异常代替修复。14库布尔生产者另作只读专项复核，未发现同类C表达式出现在其他组件。

WebView独立Native验收：真实GitPod0.2.0-rc.7、标签提交`21453637194fb5551f375a0811e80be7f0cebed4`、重新下载源码归档SHA-256`fa0faab8db41747f9818d05405268c78188fd075093add5d9edc76e0232c2604`，安装的.h/.m/.inc与实际ObjC编译输入逐字节一致，纯UIKit iphoneos arm64 App最终链接通过。Maven0.2.0-rc.6与HAR0.2.0-rc.5配套不变；没有Maven/HAR rc7产物。宿主升级与原机异常/页面性能复验已经委派“鸿蒙生产接入”会话，本记录不把尚未回传的宿主结果写成通过。


## CMP / Kuikly 与鸿蒙追加修复

2026-10-05 追加审查仅修改远程组件，宿主问题由“鸿蒙生产接入”会话处理。sound iOS 自动 Main 入口；WebView Android/鸿蒙隐藏初始化、每文档一次、隐藏消息清理、乱序 visibility 和导航恢复握手已实现、独立复审并发布。没有引入跨库框架、恢复 reload 或放宽原生来源/生命周期权限门禁。初轮 547/2 执行统计保留为阶段结果；本次实际执行 sound iOS12/Android8、Web Android3，均无失败或跳过，OHOS production ETS/JS harness另计。

| 当前 Release / 验收记录 | Maven / 独立原生配套 | 验收结果 |
| --- | --- | --- |
| [sound 0.1.3](https://github.com/gycrosskit/sound/releases/tag/0.1.3) · [详细记录](https://github.com/gycrosskit/sound/blob/main/docs/0.1.3远程发布验收.md) | Maven `0.1.3`；未改 OHOS HAR `0.1.0` | 8 个 publication/8 个制品；干净 Android/iOS/OHOS 编译与 Simulator Framework 链接通过 |
| [WebView rc.8](https://github.com/gycrosskit/compose-webview/releases/tag/0.2.0-rc.8) · [详细记录](https://github.com/gycrosskit/compose-webview/blob/main/docs/0.2.0-rc.8远程发布验收.md) | Maven/HAR `rc.8`；未改 iOS Native Pod `rc.7`；system-actions HAR `rc.3` | 17 个 publication/17 个制品；Kuikly Android APK、iOS device/simulator Framework、OHOS .so，以及 CMP Android APK/iOS 编译与 simulator Framework 通过 |

两库不可变标签、JitPack最终public/tag/commit、Release归档重下载SHA一致。25个制品大小、四种声明hash、ZIP CRC、POM许可证、available-at及内部精确依赖通过；50个制品MD5/SHA-1 sidecar通过，50个SHA-256/SHA-512 sidecar HTTP404仅记录为渠道缺失。sound生成的顶层component.url仍指向缺失的sound根坐标（本次HTTP404），实际平台variant/available-at和干净消费正常；不建立伪坐标掩盖渠道行为。

Web rc.8 Release HAR重下载、实际HAR production harness及新目录ArkTS消费者通过；Web与宿主直接依赖仅一份system-actions rc.3 owner。Web rc.8 OHPM接受closure-rc8审核，精确查询仍NOTFOUND；配套system-actions-native rc.3本轮已published且从Registry实际安装，组织首页同步纠正其状态。Release文件消费不能代替Web Registry安装。宿主接入已交接，真实设备业务验收由用户完成；本轮缺陷不作为signal9的已证实归因。
