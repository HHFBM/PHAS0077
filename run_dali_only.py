import os
import subprocess
import pandas as pd
import re
import shutil
import argparse

# === 命令行参数 ===
parser = argparse.ArgumentParser(description="使用 DALI 对预测结构进行分类")
parser.add_argument("query_id", type=str, help="预测结构的 ID（如 1UBQ）")
args = parser.parse_args()
query_id = args.query_id

# === 目录设置（改为你有权限的路径）===
BASE_DIR = "/mnt/data2/supfam/jiajun"
DALI_BIN = "/home/wenhao/6tx0/software/dali/DaliLite.v5/bin/dali.pl"

QUERY_DAT_DIR = os.path.join(BASE_DIR, "query_structures_DAT")
TARGET_DAT_DIR = os.path.join(BASE_DIR, "DAT")
TARGET_PDB_DIR = os.path.join(BASE_DIR, "superfamily_pdbs")
RESULT_DIR = os.path.join(BASE_DIR, "dali_results")
os.makedirs(RESULT_DIR, exist_ok=True)

# === DALI比对 ===
zscore_list = []
for fname in os.listdir(TARGET_PDB_DIR):
    if not fname.endswith(".pdb"):
        continue
    ref_id = fname.replace(".pdb", "")
    print(f"🔗 Comparing {query_id} vs {ref_id}")

    cmd = [
        DALI_BIN,
        "--cd1", query_id,
        "--cd2", ref_id,
        "--dat1", QUERY_DAT_DIR,
        "--dat2", TARGET_DAT_DIR,
        "--outfmt", "summary",
        "--clean"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️ Failed: {result.stderr}")
        continue

    # 移动输出文件
    out_file = f"{query_id}.txt"
    renamed = os.path.join(RESULT_DIR, f"{query_id}_vs_{ref_id}.txt")
    if os.path.exists(out_file):
        shutil.move(out_file, renamed)
    else:
        print(f"⚠️ 输出文件未生成：{out_file}")
        continue

    # 提取 Z-score
    zscore = 0.0
    with open(renamed, "r") as f:
        for line in f:
            if re.match(r"^\s*\d+\s+", line):
                tokens = line.strip().split()
                zscore = float(tokens[-1])
                break

    zscore_list.append({
        "Superfamily": ref_id,
        "Z-score": zscore,
        "ResultFile": os.path.basename(renamed)
    })

# === 输出结果表格 ===
df = pd.DataFrame(zscore_list)
df = df.sort_values(by="Z-score", ascending=False).reset_index(drop=True)
csv_path = f"./{query_id}_zscore_results.csv"
df.to_csv(csv_path, index=False)

# === 输出总结 ===
print(f"\n✅ Z-score 表格保存为: {csv_path}")
if not df.empty:
    best = df.iloc[0]
    print(f"🎯 最佳匹配 superfamily: {best['Superfamily']} (Z-score = {best['Z-score']})")
