# 乳腺多模态动态 MRI：按需使用的领域提示

本文件帮助写作者保持概念边界，不是一份用户阅读记录，也不代表以下论文均已阅读。写周报时，只采用本轮材料支持的内容；具体网络配置、数值和实验结论应回到原文核对。不要把这里列出的研究设想写成已完成的工作。

## 多序列融合与专家模型

《A large model for non-invasive and personalized management of breast cancer from multiparametric MRI》中的 MOME 联合 DCE-MRI、T2WI 与 DWI。理解其专家结构时，需要区分两种作用：

- **模态专属的稀疏专家**主要适配不同 MRI 序列的特征；
- **软融合专家**通过加权汇总 token、专家处理和结果组合，学习跨序列融合。

不要将两者合并成一句笼统的“使用多专家进行融合”。论文中的融合比较也不能推出“模型越复杂越好”或“辅助序列必然改善预测”。适合本课题的研究顺序是建立各单序列及简单融合基线，再检验注意力、专家等模块是否有额外贡献。

DCE 的多个时相不等于多个 MRI 序列；使用多时相输入，也不等于已经专门研究了时间交互。可分别比较少量与完整可用时相、通道堆叠与显式时间表示，再分析 T2WI、DWI 的增量价值。不同序列可以采用不同处理方式，但更大的编码器或不对称容量是否有益仍需验证。

原始来源：[Nature Communications](https://www.nature.com/articles/s41467-025-58798-z)。

## 灵活图文框架与检索辅助预测

《VLMo: Unified Vision-Language Pre-Training with Mixture-of-Modality-Experts》的关键启发不只是“多专家”，还包括同一骨干按任务切换计算方式：共享自注意力，使用视觉、语言或图文对应的前馈专家；独立编码适合高效检索，联合编码适合图文交互与理解。迁移到医学任务时，应说明哪些表示共享、何处交互，以及不同任务实际需要哪些输入。

原始来源：[NeurIPS 2022](https://papers.neurips.cc/paper_files/paper/2022/hash/d46662aa53e78a62afd980a29e0c37ed-Abstract-Conference.html)。

“以当前乳腺 MRI 检索 Top-K 相似病例的 MRI 与放射报告，再用检索上下文辅助良恶性或 BI-RADS 预测”是一种待验证构想。可关注病例相似度、图像与报告的对应、检索证据融合以及错误检索的影响。研究设计必须保证按患者划分数据，检索库不混入测试患者，且模型使用的报告内容在预定预测时点能够获得。不要把报告中的目标诊断直接当作可用的独立证据。

《ClinRAG-GRAPH: Clinical-prior Retrieval-Augmented Graph Model with Domain Adversarial Learning for Breast pCR Prediction》可用于了解病例检索、患者图与预测的结合，但其目标是病理完全缓解（pCR），使用 DCE-MRI 及结构化临床、活检病理等信息。不能将其直接描述为“MRI 与放射报告库辅助良恶性或 BI-RADS 诊断”的已完成实现。

原始来源：[MICCAI 2026 论文](https://papers.miccai.org/miccai-2026/paper/1181_paper.pdf)。

## 图文监督与生成、筛选

《BLIP: Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation》中的 CapFilt 通过生成描述、筛选图文配对改善训练监督。其在医学课题中的价值依赖真实图文数据、配对质量、弱标注和可用数据规模等条件。不能仅凭“单中心”“小样本”或“全人工分割标注”，就断定它没有价值；也不能在尚无实验时预判收益。

原始来源：[BLIP 原论文](https://arxiv.org/abs/2201.12086)。

《ITCNET: a visual and language pretraining model based on multimodal fusion in predicting the breast cancer subtypes on DCE-MRI》可用于区分 MRI 序列融合与影像、报告、临床资料融合。讨论其课题价值时，关注报告可用条件，以及三维或时间信息能否提供超出已有文字概括的贡献。引用具体结构前应核对原文，不根据题名推断实现。

如需比较对比学习与生成目标，可按用户指定范围补充《CoCa: Contrastive Captioners are Image-Text Foundation Models》。不要因本文件提到该论文，就擅自加入用户已经确定的下周阅读名单。

原始来源：[CoCa 原论文](https://arxiv.org/abs/2205.01917)。

## 空间、序列和时相掩码

三者有联系，但不是同一任务：

| 掩码维度 | 可研究的问题 | 不应直接声称 |
| --- | --- | --- |
| 空间 patch | 重建局部结构是否有助于形态表征 | 重建好就一定识别出病灶边缘或非肿块样强化 |
| MRI 序列 | 可见序列能否补充被遮蔽序列的信息 | 跨序列重建已经证明时间动力学建模有效 |
| DCE 时相 | 保留时相能否恢复缺失时相及病灶强化变化 | 恢复像素就一定保留诊断所需动力学 |

时间强度曲线（TIC）是重要的强化动力学线索，不宜称为乳腺 DCE 诊断的“金标准”。需要验证掩码任务是否保留病灶相关信息，以及是否改善最终预测，不能由训练目标本身代替结果。

图文对比（ITC）目标不直接要求恢复局部形态或缺失时相，但这不等于它“绝对学不到”这些特征。可以把掩码训练写为待检验的补充约束，并通过空间掩码、时相掩码及二者结合的对照，区分收益来源。

《Enhanced MRI Representation via Cross-series Masking》讨论跨序列和空间遮蔽，并在乳腺病灶分类等任务中评估表征；它不能直接充当 DCE 时相遮蔽或 TIC 学习的验证。

原始来源：[原论文](https://arxiv.org/abs/2412.07387)。

《3D Masked Autoencoders with Application to Anomaly Detection in Non-Contrast Enhanced Breast MRI》涉及非增强乳腺 MRI 的三维掩码自编码与异常检测。可借鉴其空间遮蔽和重建思路，但不能写成已经验证乳腺 DCE 时间建模，或直接等同于良恶性分类证据。

原始来源：[原论文](https://arxiv.org/abs/2303.05861)。

《SiamMAE-MRI for Dynamic MR Imaging》研究心脏动态 MRI 的欠采样重建，涉及 k-space 重建目标。它可提供时间交互与掩码结构的参考，不能直接称为乳腺 DCE 时相补全或诊断表征学习的证据。阅读时应先确认掩码所在数据域和重建对象，再判断可迁移的模块。

原始来源：[SPIE 论文 DOI](https://doi.org/10.1117/12.3097696)。
