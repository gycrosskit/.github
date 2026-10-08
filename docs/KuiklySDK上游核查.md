# Kuikly SDK 字体与无障碍核查

2026-10-05。本报告属于第三方 SDK 接入限制，不计入14个 GYCrossKit 自有组件的已完成修复。没有修改宿主或 Kuikly SDK，没有创建私有 fork 或更换全局依赖坐标。

## 核查版本与范围

官方 Maven `com.tencent.kuikly-open:{compose,compose-android,core,core-android,core-render-android}:2.28.0-2.0.21-ohos` 的 source JAR，以及官方 [2.28.0 tag](https://github.com/Tencent-TDS/KuiklyUI/tree/2.28.0) 提交 `c9c1c743c85734422a74b7c0be44d37402fe2d08`、[本次核查 main](https://github.com/Tencent-TDS/KuiklyUI/tree/18252bca15c4215fb5c9a7e92013043aa3f903ba)。追踪31个相关生产文件及公开调用者；缓存来源/SHA、官方重复 Issue/PR 查询、英文报告和最小复现保留在本轮忽略目录 `build/full-review/kuikly-upstream/`。

## 输入字体

所有 BasicTextField overload 和 Material TextField 收敛到 CoreTextField/AutoHeightTextAreaView；[TextAreaAttr.setTextStyle](https://github.com/Tencent-TDS/KuiklyUI/blob/18252bca15c4215fb5c9a7e92013043aa3f903ba/compose/src/commonMain/kotlin/com/tencent/kuikly/compose/foundation/text/BasicTextField.kt#L48) 不传 fontFamily，TextAreaAttr 无对应 API，Android KRTextFieldView/KRTextAreaView 不接收该属性。普通 Text 的字体有效不代表输入 value 字体有效；注册 IKRFontAdapter 或宿主发送原始 prop 都不能补上缺失的接线。

精确已有 [PR #1419：pass font family to text fields](https://github.com/Tencent-TDS/KuiklyUI/pull/1419) 已关闭、未合并，官方2.28与本次 main 均未包含。该 PR 的作者截图属于历史证据，本次没有新设备字体截图。应跟进此 PR，复用官方已有 family 序列化、TypeFaceLoader 和 adapter，不能仅改宿主或将整份未合并 PR 冒充兼容发行。

修复还需保留 fontWeight/style、keyboardType 切换和 Default 清除；现有字体加载器不返回完整字体样式，简单赋值可能覆盖 Bold。PR 审查要求 iOS/OHOS 输入 renderer 与 TextShadow 测量一致，换行、行高和 AutoHeight 不能只改测量。已准备最小复现与英文报告；未验证的可直接应用补丁已移除。

## 选中状态与原生语义

实际加载上述官方 release AAR 的 classes.jar 与 Kotlin stdlib，Java reflection 调用生产 `KuiklySemantisHandler.buildAccessibilityText`，没有替身实现。结果：

```text
Selected=true, ContentDescription=["English option"]
→ English option, 已选择

Disabled + Error("Invalid value"), ContentDescription=["English option"]
→ English option
```

[生产 handler](https://github.com/Tencent-TDS/KuiklyUI/blob/18252bca15c4215fb5c9a7e92013043aa3f903ba/compose/src/commonMain/kotlin/com/tencent/kuikly/compose/extension/KuiklySemantisHandler.kt#L159) 固定追加中文选中后缀；Switch 映射 TEXT、RadioButton 映射 CHECKBOX，ToggleableState 接线被注释。Disabled/Error 以及 selected/checked 等结构化字段未由这条桥完整传给原生 delegate。role 应用还受非空 label 限制。这些是文本执行/源码证据，不等于最终 View.isEnabled、真实点击和 TalkBack 设备行为都已复现。

应沿已有 attr/delegate 补原生角色和状态，交由系统读屏本地化；不要改成硬编码英文，也不要求每个业务 label 拼接状态。验收需要包含选中、开关、混合、禁用、错误添加/清除、StateDescription 优先级、无 label 角色、语义合并和节点重用后的重置，并对齐 iOS/OHOS。

本次官方重复查询未发现精确的本地化/角色状态报告。[PR #539](https://github.com/Tencent-TDS/KuiklyUI/pull/539) 是最初语义支持，[PR #1391](https://github.com/Tencent-TDS/KuiklyUI/pull/1391) 是 testTag/自动化改进，均不能证明这些缺口已解决。英文上游报告已准备，尚未提交；demo fixture 尚未编译或在设备运行。

## 接入结论

没有可直接升级的已验证官方修复版本。现有14个组件修复与 SDK 上游问题分开验收；SDK 修复发行后再验证真实远程消费、输入法/布局和设备读屏。宿主自行拼接英文标签、忽略缺字段或增加另一套输入控件，都不作为 SDK 已修复的证据。
