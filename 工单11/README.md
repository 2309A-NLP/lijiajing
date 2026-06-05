# 工单11：Embeddings模型微调

对 BGE-small-zh-v1.5 进行领域自适应微调，提升金融文本的检索效果。

## 目录结构

| 文件夹 | 内容 |
|--------|------|
| 设计/ | 微调方案设计图 |
| 研发/ | 微调代码（embedding_finetune.py） |
| 测试/ | 微调前后检索效果对比截图 |
| 优化/ | 微调策略优化总结 |
| 部署/ | 微调模型部署脚本 |

## 技术栈

- 基座模型：BGE-small-zh-v1.5（512维）
- 训练框架：sentence-transformers
- 损失函数：MultipleNegativesRankingLoss
- 训练数据：金融领域问答对
