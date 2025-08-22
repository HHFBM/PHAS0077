import os
import shutil
import subprocess

# 配置路径
input_dir = "/mnt/data2/supfam/expasy"
supfam_script = "/mnt/data2/supfam/supfam/superfamily.pl"
output_dir = "/mnt/data2/supfam/jiajun/run/html_outputs"
cleaned_dir = "/mnt/data2/supfam/jiajun/run/cleaned_fasta"
tmp_root = "/mnt/data2/supfam/jiajun/run/tmp_fasta"

# 创建目录
os.makedirs(output_dir, exist_ok=True)
os.makedirs(cleaned_dir, exist_ok=True)
os.makedirs(tmp_root, exist_ok=True)

def clean_fasta(input_path, output_path):
    """清理FASTA格式：去除空行、非法字符、非标准格式"""
    with open(input_path, "r") as f_in, open(output_path, "w") as f_out:
        lines = f_in.readlines()
        current_seq = []
        wrote_header = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_seq:
                    f_out.write("".join(current_seq) + "\n")
                    current_seq = []
                f_out.write(line + "\n")
                wrote_header = True
            else:
                if all(c.isalpha() and c.isupper() for c in line):
                    current_seq.append(line)
                else:
                    print(f"⚠️ 跳过包含非法字符的行: {line}")
        if current_seq and wrote_header:
            f_out.write("".join(current_seq) + "\n")

# 遍历所有 .fa 文件
for filename in os.listdir(input_dir):
    if not filename.endswith(".fa"):
        continue

    basename = os.path.splitext(filename)[0]
    html_output = os.path.join(output_dir, f"{basename}.html")

    if os.path.exists(html_output):
        print(f"✅ 已存在，跳过: {basename}")
        continue

    print(f"▶ 正在处理: {filename}")

    # 路径准备
    src_fa = os.path.join(input_dir, filename)
    cleaned_fa = os.path.join(cleaned_dir, filename)
    tmp_dir = os.path.join(tmp_root, basename)
    os.makedirs(tmp_dir, exist_ok=True)

    # Step 1: 清洗FASTA并保存副本
    clean_fasta(src_fa, cleaned_fa)

    # Step 2: 拷贝干净的 .fa 到 tmp_dir（用于 superfamily 执行）
    dst_fa = os.path.join(tmp_dir, filename)
    shutil.copy(cleaned_fa, dst_fa)

    try:
        subprocess.run(
            ["perl", supfam_script, filename],
            cwd=tmp_dir,
            check=True
        )

        tmp_html = os.path.join(tmp_dir, f"{basename}.html")
        if os.path.exists(tmp_html):
            shutil.move(tmp_html, html_output)
            print(f"✅ 输出已保存: {html_output}")
        else:
            print(f"⚠️ 未生成HTML: {basename}")
    except subprocess.CalledProcessError:
        print(f"❌ superfamily.pl 执行失败: {filename}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
