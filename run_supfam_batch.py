import os
import shutil
import subprocess

# 配置路径
input_dir = "/mnt/data2/supfam/expasy"
supfam_script = "/mnt/data2/supfam/supfam/superfamily.pl"
supfam_dir = "/mnt/data2/supfam/supfam"  # 包含 model.tab 的目录
output_dir = "/mnt/data2/supfam/jiajun/run/html_outputs"
tmp_dir = "/mnt/data2/supfam/jiajun/run/tmp_fasta"

# 确保输出和临时目录存在
os.makedirs(output_dir, exist_ok=True)
os.makedirs(tmp_dir, exist_ok=True)

# 遍历 .fa 文件
for filename in os.listdir(input_dir):
    if filename.endswith(".fa"):
        basename = os.path.splitext(filename)[0]
        html_output = os.path.join(output_dir, f"{basename}.html")

        if os.path.exists(html_output):
            print(f"✅ 已存在，跳过: {basename}")
            continue

        # 拷贝到临时目录
        src_fa = os.path.join(input_dir, filename)
        tmp_fa = os.path.join(tmp_dir, filename)
        shutil.copy(src_fa, tmp_fa)

        print(f"▶ 正在比对: {filename}")
        try:
            # 在 supfam_dir 中运行，确保能访问 model.tab，避免在 expasy 中写入
            subprocess.run(
                [supfam_script, tmp_fa],
                check=True,
                cwd=supfam_dir  # 修改点：使用包含 model.tab 的路径作为工作目录
            )

            # supfam 输出仍在 supfam_dir 中，形如：basename.html
            tmp_html = os.path.join(supfam_dir, f"{basename}.html")
            if os.path.exists(tmp_html):
                shutil.move(tmp_html, html_output)
                print(f"✅ 输出已保存: {html_output}")
            else:
                print(f"⚠️ 未生成HTML: {basename}")
        except subprocess.CalledProcessError:
            print(f"❌ superfamily.pl 执行失败: {filename}")
        finally:
            if os.path.exists(tmp_fa):
                os.remove(tmp_fa)  # 清理临时 .fa 文件
