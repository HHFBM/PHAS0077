import argparse
import os
import time

def generate_output_filename(model1_path, model2_path):
    """生成唯一的输出图片名：model1_vs_model2_时间.png"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    name1 = os.path.splitext(os.path.basename(model1_path))[0]
    name2 = os.path.splitext(os.path.basename(model2_path))[0]
    return f"{name1}_vs_{name2}_{timestamp}.png"

def generate_pml(model1, model2, output_img, script_path="visualize.pml"):
    """生成 PyMOL 脚本"""
    pml_script = f"""
load {model1}, model1
load {model2}, model2
align model1, model2

select atp, resn ATP
show sticks, atp
color yellow, atp

select near_atp, (byres (all within 4 of atp)) and polymer
show sticks, near_atp
color cyan, near_atp
util.cbag near_atp

ray 1200,900
png {output_img}
quit
"""
    with open(script_path, "w") as f:
        f.write(pml_script)
    return script_path

def main():
    parser = argparse.ArgumentParser(description="Align two PDB files and highlight ATP + surrounding residues.")
    parser.add_argument('--model1', required=True, help="Path to predicted model PDB file (with ATP)")
    parser.add_argument('--model2', required=True, help="Path to reference structure PDB file")
    parser.add_argument('--output', help="Output PNG file (optional, auto-generated if omitted)")
    args = parser.parse_args()

    # 自动生成输出图像文件名
    output_img = args.output if args.output else generate_output_filename(args.model1, args.model2)

    # 生成 PyMOL 脚本
    script_file = generate_pml(args.model1, args.model2, output_img)

    print(f"✅ 生成 PyMOL 脚本: {script_file}")
    print(f"📸 输出图像将保存在: {output_img}")
    print(f"🚀 正在运行 pymol 脚本...")

    # 调用 PyMOL
    ret = os.system(f"pymol -cq {script_file}")
    if ret != 0:
        print("❌ pymol 执行失败，请确认已安装并配置好 pymol 命令")

if __name__ == "__main__":
    main()
