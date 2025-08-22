import os
import subprocess
import pandas as pd
import re
import shutil
from Bio.PDB import MMCIFParser, PDBIO
import argparse

# === 参数解析 ===
parser = argparse.ArgumentParser(description="从 JSON 预测结构，并用 DALI 归类")
parser.add_argument("json_file", type=str, help="ProteinX 输入 JSON 文件路径")
args = parser.parse_args()

# === 配置 ===
BASE_DIR = "/mnt/data2/supfam/jiajun"
DALI_BIN = "/home/wenhao/6tx0/software/dali/DaliLite.v5/bin/dali.pl"
IMPORT_BIN = "/home/wenhao/6tx0/software/dali/DaliLite.v5/bin/import.pl"
PROTENIX_BIN = "protenix"

QUERY_DAT_DIR = os.path.join(BASE_DIR, "query_structures_DAT")
TARGET_DAT_DIR = os.path.join(BASE_DIR, "DAT")
TARGET_PDB_DIR = os.path.join(BASE_DIR, "superfamily_pdbs")
RESULT_DIR = os.path.join(BASE_DIR, "dali_results")
os.makedirs(RESULT_DIR, exist_ok=True)

# === Step 1: ProteinX 结构预测 ===
json_path = args.json_file
query_id = os.path.splitext(os.path.basename(json_path))[0]
output_dir = os.path.join(BASE_DIR, f"{query_id}_output")
os.makedirs(output_dir, exist_ok=True)

print(f"🚀 开始 ProteinX 结构预测: {query_id}")
cmd = [
    PROTENIX_BIN, "predict",
    "--input", json_path,
    "--out_dir", output_dir,
    "--seeds", "101",
    "--use_msa_server"
]
subprocess.run(cmd, check=True)

# === Step 2: 获取预测的 .cif 文件路径 ===
pred_cif = os.path.join(output_dir, "seed_101", "predictions", f"{query_id}_seed_101_sample_0.cif")
if not os.path.exists(pred_cif):
    raise FileNotFoundError(f"未找到预测结构: {pred_cif}")

# === Step 3: .cif → .pdb（Biopython）===
pdb_path = os.path.join(BASE_DIR, f"{query_id}.pdb")
print(f"📁 Biopython 转换 CIF → PDB: {pred_cif}")
parser = MMCIFParser(QUIET=True)
structure = parser.get_structure(query_id, pred_cif)
io = PDBIO()
io.set_structure(structure)
io.save(pdb_path)

# === Step 4: import.pl 转换为 .dat ===
print("📦 使用 import.pl 生成 .dat 文件")
import_cmd = [
    IMPORT_BIN,
    "--pdbfile", pdb_path,
    "--pdbid", query_id,
    "--dat", QUERY_DAT_DIR
]
subprocess.run(import_cmd, check=True)

# === Step 5: DALI 比对 ===
zscore_list = []
for fname in os.listdir(TARGET_PDB_DIR):
    if not fname.endswith(".pdb"):
        continue
    ref_id = fname.replace(".pdb", "")
    print(f"🔗 DALI: {query_id} vs {ref_id}")
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
        print(f"⚠️ 失败: {result.stderr}")
        continue

    out_file = f"{query_id}.txt"
    renamed = os.path.join(RESULT_DIR, f"{query_id}_vs_{ref_id}.txt")
    if os.path.exists(out_file):
        shutil.move(out_file, renamed)
    else:
        print(f"⚠️ 未生成输出: {out_file}")
        continue

    # 提取 Z-score
    zscore = 0.0
    with open(renamed, "r") as f:
        for line in f:
            if re.match(r"^\\s*\\d+\\s+", line):
                tokens = line.strip().split()
                zscore = float(tokens[-1])
                break
    zscore_list.append({
        "Superfamily": ref_id,
        "Z-score": zscore,
        "ResultFile": os.path.basename(renamed)
    })

# === Step 6: 保存 Z-score CSV（当前目录）===
df = pd.DataFrame(zscore_list)
df = df.sort_values(by="Z-score", ascending=False).reset_index(drop=True)
csv_path = f"./{query_id}_zscore_results.csv"
df.to_csv(csv_path, index=False)
print(f"\n✅ Z-score 表格保存为: {csv_path}")
if not df.empty:
    print(f"🎯 最佳匹配 superfamily: {df.iloc[0]['Superfamily']} (Z = {df.iloc[0]['Z-score']})")
