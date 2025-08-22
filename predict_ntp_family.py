import os
import subprocess
import sys
import json


def run_supfam(fasta_file, domtbl_file, db_path="hmmlib"):
    if not os.path.exists(fasta_file):
        print(f"❌ FASTA文件未找到: {fasta_file}")
        sys.exit(1)
    if not os.path.exists(db_path):
        print(f"❌ Supfam HMM库未找到: {db_path}")
        sys.exit(1)

    cmd = ["hmmscan", "--cpu", "4", "--domtblout", domtbl_file, db_path, fasta_file]
    subprocess.run(cmd, check=True)

def parse_supfam(domtbl_file):
    """
    如果能找到匹配的 SCOP 超家族，返回其名称（如 SSF52540）
    """
    with open(domtbl_file) as f:
        for line in f:
            if line.startswith("#"): continue
            parts = line.strip().split()
            domain = parts[0]  # e.g., SSF52540
            return domain
    return None

def run_proteinx(fasta_file, output_pdb_path):
    """
    使用 ProteinX 对输入的 fasta 文件进行结构预测，并输出标准 PDB 文件
    - fasta_file: 输入的 .fasta 文件路径
    - output_pdb_path: 希望最终保存的结构路径（如 predicted_structures/xxx.pdb）
    """

    # 1. 读取 fasta 序列
    with open(fasta_file) as f:
        lines = f.readlines()
        raw_id = lines[0].strip().replace(">", "")
        sequence = "".join([line.strip() for line in lines[1:]])

    # 2. 清理 id（用于生成合法文件名）
    clean_id = "".join(c for c in raw_id if c.isalnum() or c in ["_", "-"])[:30]
    print(f"🔧 清洗后的序列 ID：{clean_id}")

    # 3. 构造 JSON 输入文件路径
    output_dir = os.path.dirname(output_pdb_path)
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, f"{clean_id}.json")

    # 4. 写入 JSON 文件
    json_data = {
        "name": clean_id,
        "sequence": sequence,
        "use_msa_server": True
    }
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(json_data, jf, indent=2)
    except Exception as e:
        print(f"❌ JSON 写入失败: {e}")
        return
    # 5. 调用 ProteinX
    print(f"🚀 正在运行 ProteinX...")
    cmd = [
        "protenix", "predict",
        "--input", json_path,
        "--out_dir", output_dir,
        "--seeds", "101"
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ ProteinX 运行失败：{e}")
        return

    # 6. 检查是否生成了结果文件
    raw_pdb_path = os.path.join(output_dir, f"{clean_id}_seed101_model1.pdb")
    if not os.path.exists(raw_pdb_path):
        print(f"❌ ProteinX 未生成结构文件：{raw_pdb_path}")
        return

    # 7. 重命名为标准输出名
    os.rename(raw_pdb_path, output_pdb_path)
    print(f"✅ ProteinX 结构预测完成：{output_pdb_path}")


def run_dali_lite(query_id, ref_id, dali_output, query_dat_dir="query_structures_DAT", ref_dat_dir="DAT"):
    cmd = [
        "/home/wenhao/6tx0/software/dali/DaliLite.v5/bin/dali.pl",

        "--cd1", query_id,
        "--cd2", ref_id,
        "--dat1", query_dat_dir,
        "--dat2", ref_dat_dir,
        "--outfmt", "summary",
        "--clean"
    ]
    try:
        subprocess.run(cmd, check=True)
        # 结果默认输出在当前目录，保存为 summary
        os.rename("summary", dali_output)
        print(f"✅ DALI比对完成：{query_id} vs {ref_id} → {dali_output}")
    except subprocess.CalledProcessError as e:
        print(f"❌ DALI比对失败：{query_id} vs {ref_id}")
        print(e)


def parse_dali_result(dali_output):
    """
    如果Z-score>2且与NTP family结构有命中，则返回True
    """
    with open(dali_output) as f:
        for line in f:
            if line.startswith("#") or len(line.strip()) == 0:
                continue
            parts = line.strip().split()
            z_score = float(parts[1]) if len(parts) > 1 else 0
            if z_score > 2:
                return True
    return False

def classify_protein(fasta_file):
    basename = os.path.splitext(os.path.basename(fasta_file))[0]
    os.makedirs("supfam_results", exist_ok=True)
    os.makedirs("predicted_structures", exist_ok=True)
    os.makedirs("query_structures_DAT", exist_ok=True)
    os.makedirs("dali_results", exist_ok=True)

    # Step 1: Supfam 注释
    domtbl_file = f"supfam_results/{basename}.domtbl"
    run_supfam(fasta_file, domtbl_file)
    domain = parse_supfam(domtbl_file)

    # Step 2: 获取结构（优先 Supfam → PDB → fallback ProteinX）
    if domain:
        domain_pdb = f"superfamily_pdbs/{domain}.pdb"
        if os.path.exists(domain_pdb):
            query_structure = domain_pdb
            print(f"✅ 使用 Supfam 对应结构：{query_structure}")
        else:
            print(f"⚠️ Supfam识别为 {domain}，但结构未找到，使用 ProteinX")
            query_structure = f"predicted_structures/{basename}.pdb"
            run_proteinx(fasta_file, query_structure)
    else:
        print("⚠️ Supfam未识别结构域，使用 ProteinX")
        query_structure = f"predicted_structures/{basename}.pdb"
        run_proteinx(fasta_file, query_structure)

    # Step 3: 将结构转换为 .dat（供 DALI 使用）
    query_dat_dir = "query_structures_DAT"
    query_dat_id = f"{basename[:3]}A"  # DALI要求 pdbid为4字符
    dat_path = os.path.join(query_dat_dir, f"{query_dat_id}.dat")
    if not os.path.exists(dat_path):
        import_cmd = [
            "/home/wenhao/6tx0/software/dali/DaliLite.v5/bin/import.pl",
            "--pdbfile", query_structure,
            "--pdbid", query_dat_id,
            "--dat", query_dat_dir
        ]
        subprocess.run(import_cmd, check=True)
        print(f"✅ 转换完成：{query_structure} → {dat_path}")
    else:
        print(f"📦 已存在 dat 文件：{dat_path}")

    # Step 4: 与所有 NTP结构进行比对（在 DAT/ 中）
    ntp_ids = [f.split(".")[0] for f in os.listdir("DAT") if f.endswith(".dat")]
    found = False
    for ref_id in ntp_ids:
        dali_out = f"dali_results/{query_dat_id}_vs_{ref_id}.txt"
        run_dali_lite(query_dat_id, ref_id, dali_out, query_dat_dir, "DAT")
        z_score = parse_dali_result(dali_out)
        print(f"🔬 DALI比对结果: {query_dat_id} vs {ref_id} → Z = {z_score}")
        if z_score > 2.0:
            print(f"✅ 结构归类为 NTP processing family ✔️ (与 {ref_id})")
            found = True
            break

    if not found:
        print(f"❌ 未能归类为 NTP processing family ✖️")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python predict_ntp_family.py your.fasta")
        sys.exit(1)
    classify_protein(sys.argv[1])
