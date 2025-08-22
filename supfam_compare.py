import os
import subprocess
import shutil
import argparse

# ========== 配置 ==========
SUPERFAMILY_IDS = [
    "3F2B", "6T0V", "8DCD", "2XAN", "6CI7", "7TGK",
    "4FF3", "3AMT", "6IG2", "7Y7P", "3WDL", "3GQK"
]
SUPERFAMILY_DIR = "superfamily_pdbs"
DAT_DIR = "DAT"
OUT_DIR = "OUT"
QUERY_PDBID = "qry1"  # 必须合法（4字符）


# ========== 工具函数 ==========
def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"❌ 命令执行失败: {' '.join(cmd)}\n{result.stderr}")
    return result


def import_structure(pdb_path, pdb_id, dat_dir):
    run_cmd(["import.pl", "--pdbfile", pdb_path, "--pdbid", pdb_id, "--dat", dat_dir])


def list_dat_chains(pdb_id, dat_dir):
    prefix = pdb_id.lower()
    return sorted([
        f[:-4] for f in os.listdir(dat_dir)
        if f.startswith(prefix) and f.endswith(".dat")
    ])


def get_query_chain(dat_dir):
    candidates = [
        f[:-4] for f in os.listdir(dat_dir)
        if f.lower().startswith(QUERY_PDBID) and f.endswith(".dat")
    ]
    if not candidates:
        raise RuntimeError("❌ 未找到 query 的 .dat 文件。")
    if len(candidates) > 1:
        print(f"⚠️ 发现多个 query 链：{candidates}，默认使用第一个")
    return candidates[0]


def run_dali(cd1, cd2, dat1, dat2, outdir):
    os.makedirs(outdir, exist_ok=True)
    cmd = [
        "dali.pl",
        "--cd1", cd1,
        "--cd2", cd2,
        "--dat1", os.path.abspath(dat1),
        "--dat2", os.path.abspath(dat2),
        "--outfmt", "summary,alignments",
        "--clean"
    ]
    run_cmd(cmd, cwd=outdir)

    for fname in os.listdir(outdir):
        if cd1 in fname and cd2 in fname and (fname.endswith(".summary") or fname.endswith(".txt")):
            path = os.path.join(outdir, fname)
            with open(path) as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        parts = line.strip().split()
                        try:
                            return float(parts[2]) if parts[0].endswith(":") else float(parts[1])
                        except:
                            continue
    raise RuntimeError("⚠️ 找不到有效输出 Z-score")


def clean_dirs():
    for folder in [DAT_DIR, OUT_DIR]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder)


# ========== 主流程 ==========
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="query 的 PDB 文件名")
    args = parser.parse_args()

    if not os.path.exists(args.query):
        raise FileNotFoundError(f"❌ query 文件不存在: {args.query}")

    clean_dirs()

    print(f"📥 导入 query: {args.query}")
    import_structure(args.query, QUERY_PDBID, DAT_DIR)
    query_chain = get_query_chain(DAT_DIR)
    print(f"✅ 发现 query 链：{query_chain}\n")

    print(f"📥 导入 superfamily pdb 文件:")
    for sfid in SUPERFAMILY_IDS:
        path = os.path.join(SUPERFAMILY_DIR, f"{sfid}.pdb")
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌ 缺失 superfamily 文件: {path}")
        import_structure(path, sfid.lower(), DAT_DIR)

    print(f"\n🔬 开始比对：{query_chain} vs 所有 superfamily 链")
    results = []

    for sfid in SUPERFAMILY_IDS:
        chains = list_dat_chains(sfid, DAT_DIR)
        for chain in chains:
            try:
                z = run_dali(query_chain, chain, DAT_DIR, DAT_DIR, OUT_DIR)
                results.append((chain.upper(), z))
                print(f"✅ {query_chain} vs {chain} => Z = {z:.2f}")
            except Exception as e:
                print(f"⚠️ 比对失败：{query_chain} vs {chain} ：{e}")

    if not results:
        print("❌ 所有比对失败")
        return

    results.sort(key=lambda x: x[1], reverse=True)
    best = results[0]
    print("\n📊 排名前 5:")
    for name, z in results[:5]:
        print(f"  {query_chain} vs {name} => Z = {z:.2f}")

    print(f"\n🎯 最接近的 superfamily 是：{best[0]}，Z-score = {best[1]:.2f}")


if __name__ == "__main__":
    main()
