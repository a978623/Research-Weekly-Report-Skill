# Research Weekly Report Skill

**用真实阅读和研究记录，写出有个人思考的中文科研周报。**

这是一个可安装的 Codex skill。把论文笔记、工作记录和既有周报交给助手，它会保留你的篇幅与表达习惯，写清论文的方法、自己的理解和对课题的价值，并区分已完成工作、阅读计划和待验证设想。

项目包含通用写作流程，以及一个可选的乳腺多模态动态 MRI 领域参考。换课题时可以替换领域参考，无须重写核心技能。

## 它解决什么问题

- 要求完整周报时，同时交付本周总结和下周安排。
- 使用完整论文题名，解释真正相关的机制，而非堆叠模型缩写。
- 保留使用者主动提出的研究问题，不把周报压成文献摘要。
- 不把下载、讨论、计划阅读、代码浏览写成读完或实验验证。
- 按既有样稿控制篇幅。默认约 1900—2400 个字符，**含英文题名**，不是 2000 多字中文。
- 局部润色直接给替换段落，减少空泛过渡，不把个人偏好变成机械禁词表。
- 尊重指定阅读名单。发现事实问题时准确说明论文用途，不悄悄替换论文。

它不自动读取你的笔记软件、不运行模型实验，也不代替论文全文精读。检索、读文件和文档导出使用宿主助手实际提供的工具；技能本身不需要 API key 或额外连接器。

## 安装

下载或克隆本仓库，进入项目根目录。运行安装、统计及项目检查脚本需要 **Python 3.10+**，仅使用标准库。

```console
python scripts/install_skill.py
```

安装脚本把 `skills/research-weekly-report/` 复制到 `CODEX_HOME/skills/`；没有设置 `CODEX_HOME` 时，使用用户目录下的 `.codex/skills/`。若同名技能已存在，脚本会停止并保留已有内容。

也可以指定技能父目录：

```console
python scripts/install_skill.py --skills-dir ./my-skills
```

或者手动把 `skills/research-weekly-report/` 整个文件夹复制到宿主支持的技能目录。只需手动复制时不要求 Python；请同时保留其中的参考文件和模板。

## 使用

在支持该技能的会话中输入：

```text
使用 $research-weekly-report，根据以下笔记和之前确认的样稿写完整周报。
沿用“一、本周工作总结；二、下周工作安排”。
保留我的研究思考，使用完整论文名称，不补造阅读或实验。

本周实际完成：……
只读了一部分／延期：……
我自己的理解和疑问：……
下周指定阅读：……
```

只改一段时可以直接说：

```text
使用 $research-weekly-report，只改下面这一段。
开头用“对于本课题”，写得自然一些，保留尚未验证的语气。
```

不必每周重新填长表。已有笔记和简短进度说明足够时，直接给材料；需要提纲可参考 [材料收集模板](skills/research-weekly-report/assets/material-intake.md)。

## 表达习惯

写作细节见 [表达与取舍](skills/research-weekly-report/references/style-guide.md)。涉及乳腺 MRI 时可按需使用 [领域参考](skills/research-weekly-report/references/breast-mri.md)，其中明确区分：

- 多序列 MRI、DCE 多时相与多预测任务。
- 专家融合、灵活编码框架与联合多任务训练。
- 历史病例检索辅助预测与单纯图文匹配。
- 空间掩码、跨序列掩码、时相掩码和欠采样成像重建。

领域参考中的论文是可核实的示例，不代表安装者已经阅读，也不是每周必须安排的名单。

## 调整为自己的周报

优先直接提供你的旧样稿，并说明本次要保留的标题和篇幅。当前用户要求高于技能默认值，例如“上周总结／本周安排”、只写两篇、按项目条目组织、缩短篇幅，都可以直接覆盖默认设置。

需要长期复用新领域时：

1. 在技能的 `references/` 下新增该领域真正容易混淆的概念和核实入口。
2. 在 `SKILL.md` 的工具与核实部分添加按需读取说明。
3. 补充不含私人资料的行为评估场景。

不建议把每次纠正都变成所有领域通用的硬规则，也不要把私人的已读状态写进公开技能。

## 篇幅统计

```console
python skills/research-weekly-report/scripts/report_metrics.py report.md --json
```

将 `report.md` 替换为你自己的周报文件路径。统计以脚本定义的 Markdown 可见正文为口径。它会给出字符数和中文汉字数，用于和样稿比较；英文题名计入字符数，链接地址不重复计入。具体排除项和空白处理可用脚本的 `--help` 查看。

统计结果不是 Word 字数或页数，不检查事实真伪，也不会因为低于参考篇幅就强制扩写。

## 项目检查与打包

```console
python scripts/validate_project.py
python -m unittest discover -s tests -v
python scripts/package_skill.py
```

生成：

- `dist/research-weekly-report-v0.1.0.zip`：单独的可安装技能包。
- `dist/research-weekly-report-project-v0.1.0.zip`：完整项目源码包。

结构检查和自动测试用于验证文件完整性、链接及工具行为。写作质量还需做 [行为场景评估](evals/scenarios.md)；不能把结构检查通过写成模型输出已经可靠。当前版本实际执行的检查与两种独立试写结果见 [本地验证记录](evals/validation-notes.md)。

GitHub Actions 配置同时在 Windows 和 Linux 上运行检查、测试与打包。

## 发布到 GitHub

本项目不绑定任何账号，也不默认推送代码。检查公开内容后，可以在 GitHub 创建名为 `research-weekly-report-skill` 的空仓库，再上传项目源码，或从本地 Git 仓库推送。

若使用 GitHub CLI，在已经安装并登录 `gh`、本地已有首个提交且尚未绑定目标远程仓库的条件下，可在项目根目录运行：

```console
gh repo create research-weekly-report-skill --public --source . --remote origin --push
```

创建 release 时可使用标签 `v0.1.0`，将 `dist/` 中两个 ZIP 作为附件。`dist/` 已被 Git 忽略，源码仓库只维护项目文件。

真实周报、患者资料、本地笔记和导出文件请保存在仓库外。`private/`、`local-notes/` 及常见文档文件已加入忽略规则，但忽略规则不能替代发布前检查。

## 文件结构

```text
skills/research-weekly-report/
  SKILL.md                  技能入口与事实边界
  agents/openai.yaml        显示信息与默认调用提示
  references/               风格和可选领域参考
  assets/                   输入提纲和周报骨架
  scripts/report_metrics.py 篇幅统计
evals/scenarios.md          人工或独立助手行为评估
scripts/                    安装、检查和打包工具
tests/                      工具行为测试
.github/workflows/          跨平台自动检查
```

## 许可证

本项目自行编写的代码、技能指令和文档以 [MIT License](LICENSE) 发布。论文只提供公开来源链接，未打包论文原文、图表或私人笔记；第三方内容权利属于相应权利人。
