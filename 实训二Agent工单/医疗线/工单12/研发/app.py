# -*- coding: utf-8 -*-
"""
work_order_12 健康咨询 - 交互入口
提供 CLI 和 HTTP API 两种交互方式
工单编号：人工智能NLP-Agent数字人项目-12-健康咨询
"""
import sys
from kg_builder import build_knowledge_base
from kg_agent import MedicalKGAgent, demo_test


def cli_interactive():
    """CLI 交互模式"""
    print("\n" + "="*60)
    print("🏥 工单 12 - 医疗健康咨询 Agent")
    print("="*60)
    print("功能: 基于知识图谱的疾病咨询")
    print("输入 'quit' 退出, 'test' 运行测试案例, 'build' 重建图谱")
    print("-"*60)
    
    agent = None
    
    while True:
        try:
            query = input("\n👤 患者: ").strip()
            
            if not query:
                continue
            elif query.lower() in ("quit", "exit", "退出"):
                print("👋 再见!")
                if agent:
                    agent.close()
                break
            elif query.lower() == "test":
                if agent:
                    agent.close()
                demo_test()
                agent = MedicalKGAgent()
            elif query.lower() == "build":
                build_knowledge_base()
                if agent:
                    agent.close()
                agent = MedicalKGAgent()
            else:
                if not agent:
                    agent = MedicalKGAgent()
                answer = agent.ask(query)
                print(f"\n🤖 Agent:\n{answer}")
                
        except KeyboardInterrupt:
            print("\n👋 再见!")
            if agent:
                agent.close()
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")


def main():
    """主入口"""
    # 确保知识图谱已构建
    import os
    from config import DB_PATH
    
    if not os.path.exists(DB_PATH):
        print("📦 首次运行，正在构建知识图谱...")
        build_knowledge_base()
    
    # 根据参数选择模式
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        demo_test()
    else:
        cli_interactive()


if __name__ == "__main__":
    main()
