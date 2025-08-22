import os
import subprocess

# ==== 配置路径 ====
DAT1 = "./DAT"
DAT2 = "./DAT"
OUTDIR = "./OUT"
os.makedirs(DAT1, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)



PDBS = {
    "1UBQ": {"file": "1UBQ.pdb", "pdbid": "1ubq"},
    "2HPR": {"file": "2HPR.pdb", "pdbid": "2hpr"},
}

# ==== 导入结构 ====
def import_structure(pdb_path, pdb_id, dat_dir):
    print(f"📥 导入结构 {pdb_id} 到 {dat_dir}...")
    cmd = [
        "import.pl",
        "--pdbfile", pdb_path,
        "--pdbid", pdb_id,
        "--dat", dat_dir
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("❌ import.pl 执行失败")
        print("STDERR:\n", result.stderr)
        raise RuntimeError("导入失败")
    print(f"✅ 导入完成：{pdb_id}")


# ==== 比对结构链 ====
def run_dali(cd1, cd2, dat1, dat2, outdir, title="DALI output"):
    print(f"🔬 正在比对：{cd1} vs {cd2}")

    # 🛠 确保 OUT 目录存在
    os.makedirs(outdir, exist_ok=True)

    # 🔄 保存当前目录，并切换到 OUT 目录
    prev_cwd = os.getcwd()
    os.chdir(outdir)

    try:
        # 🧠 组装 DALI 命令
        cmd = [
            "dali.pl",
            "--cd1", cd1,
            "--cd2", cd2,
            "--dat1", os.path.abspath(dat1),
            "--dat2", os.path.abspath(dat2),
            "--title", title,
            "--outfmt", "summary,alignments,equivalences,transrot",
            "--clean"
        ]

        # ✅ 执行命令
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # ❗ 捕捉失败信息
        if result.returncode != 0:
            print("❌ dali.pl 执行失败")
            print("STDERR:\n", result.stderr)
            raise RuntimeError("比对失败")

        # 🔍 查找 summary 文件
        summary_file = f"{cd1}.txt"
        if not os.path.exists(summary_file):
            print("❗ 没有生成 .summary 文件，可能比对失败")
            print("DALI 输出（部分）：\n", result.stdout[:500])
            raise FileNotFoundError(f"❌ 缺失 summary 文件：{summary_file}")

        # ✅ 解析 Z-score
        with open(summary_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    parts = line.strip().split()
                    z_score = float(parts[1])
                    print(f"✅ 比对成功：Z-score = {z_score:.2f}")
                    return z_score

        raise RuntimeError("⚠️ 找到 summary 文件但无法解析 Z-score")

    finally:
        os.chdir(prev_cwd)
def list_dat_chains(dat_dir):
    return sorted([f[:-4] for f in os.listdir(dat_dir) if f.endswith(".dat")])

def run_all_pairwise(dat_dir, outdir):
    chains = list_dat_chains(dat_dir)
    print(f"🔍 发现结构链：{chains}")
    results = []

    for i in range(len(chains)):
        for j in range(i+1, len(chains)):
            cd1, cd2 = chains[i], chains[j]
            try:
                z = run_dali(cd1, cd2, dat_dir, dat_dir, outdir, title=f"{cd1} vs {cd2}")
                results.append((cd1, cd2, z))
            except Exception as e:
                print(f"⚠️ 比对失败：{cd1} vs {cd2} ：{e}")

    print("\n📊 所有比对结果（Z-score）：")
    for cd1, cd2, z in results:
        print(f"{cd1} vs {cd2} => Z-score = {z:.2f}")


# ==== 主程序 ====

os.makedirs(OUTDIR, exist_ok=True)
def main():
    for pdb_id, info in PDBS.items():
        if not os.path.exists(info["file"]):
            raise FileNotFoundError(f"❌ 找不到 PDB 文件：{info['file']}")
        import_structure(info["file"], info["pdbid"], DAT1)

    z = run_dali("1ubqA", "2hprA", DAT1, DAT2, OUTDIR, title="ubq vs hpr")
    # z = run_all_pairwise(DAT1, OUTDIR)
    print(f"🎯 比对完成，Z-score = {z:.2f}")


if __name__ == "__main__":
    main()
