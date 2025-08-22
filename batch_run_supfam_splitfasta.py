import os
import subprocess
import shutil

# 配置路径
input_root = "/mnt/data2/supfam/jiajun/run/split_fasta"
output_root = "/mnt/data2/supfam/jiajun/run/split_results"
supfam_script = "/mnt/data2/supfam/supfam/superfamily.pl"
supfam_resource_dir = "/mnt/data2/supfam/supfam"  # 含 model.tab / .dat / .hmm / self_hits.tab 等资源文件

# 所需依赖文件名（按需补充）
required_files = [
    "model.tab",
    "model.dat",
    "model.hmm",
    "self_hits.tab"
]

# 创建输出主目录
os.makedirs(output_root, exist_ok=True)

# 遍历所有子目录
for subdir in os.listdir(input_root):
    sub_input_dir = os.path.join(input_root, subdir)
    if not os.path.isdir(sub_input_dir):
        continue

    # 创建对应输出目录
    sub_output_dir = os.path.join(output_root, subdir)
    os.makedirs(sub_output_dir, exist_ok=True)

    # 检查并建立软链接到每个子目录（避免复制多份）
    for filename in required_files:
        src_path = os.path.join(supfam_resource_dir, filename)
        dst_path = os.path.join(sub_input_dir, filename)
        if not os.path.exists(dst_path):
            try:
                os.symlink(src_path, dst_path)
            except FileExistsError:
                pass  # 如果已经有同名文件或链接就跳过
            except Exception as e:
                print(f"⚠️ 无法链接 {filename} 到 {sub_input_dir}：{e}")

    # 遍历 .fa 文件
    for filename in os.listdir(sub_input_dir):
        if not filename.endswith(".fa"):
            continue

        basename = os.path.splitext(filename)[0]
        html_output = os.path.join(sub_output_dir, f"{basename}.html")
        fa_path = os.path.join(sub_input_dir, filename)

        if os.path.exists(html_output):
            print(f"✅ 已存在，跳过: {basename}")
            continue

        print(f"▶ 正在比对: {filename} in {subdir}")

        try:
            subprocess.run(
                [supfam_script, filename],
                cwd="/mnt/data2/supfam/supfam",
                check=True,
                env={**os.environ, "HMMDB": "hmmlib"}
            )

            tmp_html = os.path.join(sub_input_dir, f"{basename}.html")
            if os.path.exists(tmp_html):
                shutil.move(tmp_html, html_output)
                print(f"✅ 输出已保存: {html_output}")
            else:
                print(f"⚠️ 未生成HTML: {basename}")
        except subprocess.CalledProcessError:
            print(f"❌ superfamily.pl 执行失败: {filename}")
