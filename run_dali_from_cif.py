import os
import subprocess
import re
import shutil
import pandas as pd
from Bio.PDB import MMCIFParser, PDBIO

# ========== 配置 ==========
BASE_DIR = "/mnt/data2/supfam/jiajun"
QUERY_DAT_DIR = os.path.join(BASE_DIR, "query_structures_DAT")
TARGET_DAT_DIR = os.path.join(BASE_DIR, "DAT")
TARGET_PDB_DIR = os.path.join(BASE_DIR, "superfamily_pdbs")
RESULT_DIR = os.path.join(BASE_DIR, "dali_results")
DALI_BIN = "/home/wenhao/6tx0/software/dali/DaliLite.v5/bin/dali.pl"
IMPORT_BIN = "/home/wenhao/6tx0/software/dali/DaliLite.v5/bin/import.pl"

os.makedirs(QUERY_DAT_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# ========== 输入 .cif 文件路径 ==========
predictions_folder = os.path.join(BASE_DIR, "seqpart_output", "sequence_1", "seed_101", "predictions")

# 遍历 predictions 中所有 .cif 文件
for filename in os.listdir(predictions_folder):
    if not filename.endswith(".cif"):
        continue

    cif_path = os.path.join(predictions_folder, filename)
    query_id = os.path.splitext(filename)[0]
    print(f"\n🚀 正在处理: {query_id}")

    # === Step 1: Biopython 解析 .cif → .pdb ===
    pdb_path = f"./{query_id}.pdb"
    parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure(query_id, cif_path)
    io = PDBIO()
    io.set_structure(structure)
    io.save(pdb_path)

    # === Step 2: 使用 import.pl 生成 .dat 文件 ===
    print("📦 生成 .dat 文件中...")
    query_id = (query_id[24:].lower())[:4]
    import_cmd = [
        IMPORT_BIN,
        "--pdbfile", pdb_path,
        "--pdbid", query_id,
        "--dat", QUERY_DAT_DIR,
        "--clean"
    ]
    subprocess.run(import_cmd, check=True)

    # === Step 3: 用 DALI 比对 query vs 所有 superfamily ===
    zscore_list = []
    for ref_pdb in os.listdir(TARGET_PDB_DIR):
        if not ref_pdb.endswith(".pdb"):
            continue
        ref_id = os.path.splitext(ref_pdb)[0]
        print(f"🔗 比对 {query_id} vs {ref_id}")

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
            print(f"❌ 比对失败: {result.stderr}")
            continue

        output_file = f"{query_id}.txt"
        target_output = f"dali_results/{query_id}_vs_{ref_id}.txt"
        if os.path.exists(output_file):
            shutil.move(output_file, target_output)
        else:
            continue

        # === Step 4: 解析 Z-score ===
        zscore = 0.0
        with open(target_output, "r") as f:
            for line in f:
                if line.strip().startswith("#") or line.strip() == "":
                    continue
                tokens = line.strip().split()
                if len(tokens) >= 7:
                    try:
                        zscore = float(tokens[6])  # 第7列是Z-score
                        break
                    except ValueError:
                        continue

        zscore_list.append({
            "filename": os.path.basename(target_output),
            "Z-score": zscore
        })

    # === Step 5: 保存 CSV ===
    df = pd.DataFrame(zscore_list)
    df = df.sort_values(by="Z-score", ascending=False)
    csv_path = f"./{query_id}_result.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ 保存 Z-score 结果表: {csv_path}")

