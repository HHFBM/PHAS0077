import os
import subprocess
import tempfile
from Bio import SeqIO

# ========== 配置项 ==========
FASTA_FILE = "sequence.fasta"
QUERY_PDB = "query.pdb"
SUPERFAMILY_DIR = "superfamily_pdbs"  # 包含12个superfamily结构的目录


# ========== 自动创建 fasta 文件 ==========
def create_fasta(sequence: str, fasta_path: str):
    with open(fasta_path, "w") as f:
        f.write(">query_sequence\n")
        f.write(sequence + "\n")
    print(f"✅ FASTA 文件写入完成：{fasta_path}")


# ========== 从 fasta 文件读取序列 ==========
def load_sequence(fasta_file):
    record = next(SeqIO.parse(fasta_file, "fasta"))
    return str(record.seq)


# ========== 使用命令行 Protenix 预测结构 ==========
def predict_structure(sequence, out_pdb_path):
    try:
        result = subprocess.run(
            ["protenix", "predict", "--input", sequence, "--out_dir", out_pdb_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Protenix 出错：")
        print(e.stderr)
        raise RuntimeError("结构预测失败")

    if not os.path.exists(out_pdb_path):
        raise FileNotFoundError(f"结构文件未生成：{out_pdb_path}")

    print(f"✅ 结构预测完成，保存为：{out_pdb_path}")
    return out_pdb_path


# ========== 使用 DALI 本地比对 ==========
def run_dali(query_pdb, target_pdb, dali_output_dir):
    os.makedirs(dali_output_dir, exist_ok=True)
    dali_cmd = [
        "dali.pl",
        "--query", query_pdb,
        "--target", target_pdb,
        "--outdir", dali_output_dir,
        "--quiet"
    ]
    subprocess.run(dali_cmd, check=True)

    summary_file = os.path.join(dali_output_dir, "summary.txt")
    if not os.path.exists(summary_file):
        raise FileNotFoundError("未找到 DALI summary 文件")

    with open(summary_file, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split()
                z_score = float(parts[1])  # Z-score 通常为第2列
                return z_score
    return 0.0


# ========== 比对所有 superfamily PDB ==========
def identify_superfamily(query_pdb, pdb_dir):
    best_score = -1
    best_family = None

    for fname in os.listdir(pdb_dir):
        if not fname.endswith(".pdb"):
            continue
        name = fname.replace(".pdb", "")
        target_pdb = os.path.join(pdb_dir, fname)

        with tempfile.TemporaryDirectory() as tempdir:
            try:
                z = run_dali(query_pdb, target_pdb, tempdir)
                print(f"[{name}] Z-score = {z:.2f}")
                if z > best_score:
                    best_score = z
                    best_family = name
            except Exception as e:
                print(f"❌ 比对 {name} 出错：{e}")

    return best_family, best_score


# ========== 主程序 ==========
def main():
    # Step 1: 输入蛋白质序列
    user_sequence = input("请输入蛋白质序列（单行）：").strip().upper()
    if not user_sequence.isalpha():
        raise ValueError("❌ 非法序列，仅应包含字母")

    # Step 2: 写入 FASTA 文件
    create_fasta(user_sequence, FASTA_FILE)

    # Step 3: 读取并确认序列
    sequence = load_sequence(FASTA_FILE)

    # Step 4: 调用命令行 Protenix
    predict_structure(sequence, QUERY_PDB)

    # Step 5: 与 superfamily 比对
    print("🔍 正在与12个 superfamily 比对...")
    superfamily, score = identify_superfamily(QUERY_PDB, SUPERFAMILY_DIR)

    # Step 6: 输出结果
    if superfamily:
        print(f"\n✅ 最可能归属 superfamily：{superfamily}（Z-score = {score:.2f}）")
    else:
        print("❌ 没有匹配任何 superfamily")


if __name__ == "__main__":
    main()
