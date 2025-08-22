import os
import subprocess
import sys

def run_hmmscan(fasta_file, output_file, db_path="hmmlib"):
    """
    使用hmmscan对输入FASTA进行Supfam结构域注释。
    """
    if not os.path.exists(fasta_file):
        print(f"❌ FASTA文件未找到: {fasta_file}")
        sys.exit(1)

    if not os.path.exists(db_path):
        print(f"❌ Supfam HMM库未找到: {db_path}")
        sys.exit(1)

    # 生成 domtblout 格式的结构域注释文件
    cmd = [
        "hmmscan",
        "--cpu", "4",
        "--domtblout", output_file,
        db_path,
        fasta_file
    ]

    print("🚀 正在运行 hmmscan 注释 Supfam 结构域...")
    subprocess.run(cmd, check=True)
    print(f"✅ 注释完成，结果保存在: {output_file}")


def parse_domtblout(domtblout_file):
    """
    解析hmmscan domtblout输出，提取结构域注释结果。
    """
    annotations = []

    with open(domtblout_file, 'r') as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            fields = line.strip().split()
            target_name = fields[0]
            query_id = fields[3]
            i_evalue = float(fields[12])
            domain_score = float(fields[13])
            ali_start = int(fields[17])
            ali_end = int(fields[18])
            annotations.append((query_id, target_name, ali_start, ali_end, i_evalue, domain_score))

    return annotations


def write_summary(annotations, out_file="supfam_annotations_summary.txt"):
    """
    将注释结果写入到summary文件
    """
    with open(out_file, "w") as f:
        f.write("Query\tDomain\tStart\tEnd\tE-value\tScore\n")
        for ann in annotations:
            f.write("\t".join(map(str, ann)) + "\n")
    print(f"📄 结果摘要保存至: {out_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="使用 Supfam HMMs 注释 FASTA 文件中的蛋白质结构域")
    parser.add_argument("fasta", help="输入的FASTA序列文件")
    parser.add_argument("--db", default="hmmlib", help="Supfam HMM库路径")
    args = parser.parse_args()

    # 获取基础名（不带路径和扩展名）
    base_name = os.path.splitext(os.path.basename(args.fasta))[0]

    # 构造输出路径
    output_dir = "supfam_results"
    os.makedirs(output_dir, exist_ok=True)

    # 设置 domtblout 和 summary 路径
    domtbl_path = os.path.join(output_dir, f"{base_name}.domtbl")
    summary_path = os.path.join(output_dir, f"{base_name}_supfam_result.txt")

    run_hmmscan(args.fasta, domtbl_path, args.db)
    result = parse_domtblout(domtbl_path)
    write_summary(result, summary_path)
