"""
DistillAI CLI - 命令行接口
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from distill import Distiller, PRESET_PERSONAS
import argparse


def cmd_distill(args):
    """蒸馏人物"""
    d = Distiller()
    if args.name == "金" and Path(r"C:\Users\Administrator\.openclaw\workspace\USER.md").exists():
        persona = d.distill_from_workspace("金")
    else:
        persona = d.distill_from_files(args.name, args.files, args.description or "")
    print(f"\n[OK] {persona.name} 人格蒸馏完成")
    print(f"     文件: distill/personas/{persona.name}.json")


def cmd_chat(args):
    """与人格聊天"""
    d = Distiller()
    if not args.persona:
        print("错误: 请指定 --persona")
        return
    reply = d.chat(args.persona, args.message)
    print(f"\n[{args.persona}]\n{reply}")


def cmd_list(args):
    """列出所有人格"""
    personas_dir = Path(__file__).parent.parent / "distill" / "personas"
    files = list(personas_dir.glob("*.json"))
    if not files:
        print("还没有蒸馏过任何人格")
        return
    print("可用人格:")
    for f in files:
        import json
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        print(f"  {f.stem}: {data.get('core_identity', {}).get('description', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(description="DistillAI - 人格蒸馏工具")
    sub = parser.add_subcommands(dest="cmd")
    
    p = sub.add("distill", help="蒸馏新人物")
    p.add_argument("--name", "-n", required=True, help="人物名称")
    p.add_argument("--files", "-f", nargs="+", help="输入文件列表")
    p.add_argument("--description", "-d", help="人物描述")
    
    p = sub.add("chat", help="与人格聊天")
    p.add_argument("--persona", required=True, help="人格名称")
    p.add_argument("--message", "-m", required=True, help="消息内容")
    
    p = sub.add("list", help="列出所有人格")
    
    args = parser.parse_args()
    
    if args.cmd == "distill":
        cmd_distill(args)
    elif args.cmd == "chat":
        cmd_chat(args)
    elif args.cmd == "list":
        cmd_list(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()