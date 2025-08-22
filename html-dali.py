import os
import re
import subprocess
from bs4 import BeautifulSoup

# ========== 配置路径 ==========
sp_results_root = "/mnt/data2/supfam/jiajun/run/sp_results/"
input_json_dir = "/mnt/data2/supfam/jiajun/run/input_jsons/"
step1_script = "/mnt/data2/supfam/jiajun/scripts/step1.py"
output_txt = "unclassified_seq_ids.txt"

# 确保 JSON 目录存在
os.makedirs(input_json_dir, exist_ok=True)

unclassified_ids = []


def extract_unannotated_seq_ids(html_path):
    """从 html 文件中提取未注释的 Seq_ID"""
    with open(html_path, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')

    table_rows = soup.find_all('tr')
    records = []

    for row in table_rows[1:]:  # Skip header
        cols = row.find_all('td')
        if not cols:
            continue
        seq_id = cols[0].get_text(strip=True)
        is_empty = all(col.get_text(strip=True) in ["", "-", "–"] for col in cols[1:])
        records.append((seq_id, is_empty))

    from collections import defaultdict
    grouped = defaultdict(list)
    for seq_id, empty in records:
        grouped[seq_id].append(empty)

    unclassified = [sid for sid, flags in grouped.items() if all(flags)]
    return unclassified


def extract_sequence_from_fasta(fasta_path, seq_id):
    """从 .fa 文件中提取特定 ID 的氨基酸序列"""
    sequence = ""
    current_id = None
    with open(fasta_path, 'r') as f:
        for line in f:
            if line.startswith(">"):
                current_id = line.strip()[1:]
            elif current_id == seq_id:
                sequence += line.strip()
    return sequence


def seq_id_to_uniprot_id(seq_id):
    """从 seq_id 中提取 Uniprot ID"""
    # 示例：sp|Q8PUQ1|PPS_THEON → Q8PUQ1
    match = re.match(r"sp\|(\w+)\|", seq_id)
    return match.group(1) if match else None


def create_json_from_seq(seq_id, sequence):
    """生成 ProteinX 输入用的 JSON 文件"""
    uniprot_id = seq_id_to_uniprot_id(seq_id)
    if not uniprot_id or not sequence:
        print(f"❌ 无法生成 JSON：{seq_id}")
        return None

    json_path = os.path.join(input_json_dir, f"{uniprot_id}.json")
    json_obj = {
        "target_id": uniprot_id,
        "sequence": sequence
    }

    import json
    try:
        with open(json_path, 'w') as f:
            json.dump(json_obj, f)
        print(f"✅ 已生成 JSON: {json_path}")
        return json_path
    except Exception as e:
        print(f"❌ 写入 JSON 失败: {json_path}, 错误: {e}")
        return None


def run_step1(json_filename):
    """调用 step1.py 处理结构预测 + DALI"""
    try:
        subprocess.run(
            ["python", step1_script, "--input_json", json_filename],
            check=True
        )
        print(f"✅ step1.py 完成: {json_filename}")
    except subprocess.CalledProcessError as e:
        print(f"❌ step1.py 执行失败: {json_filename}")
        print(str(e))


def main():
    for root, _, files in os.walk(sp_results_root):
        for file in files:
            if not file.endswith(".html"):
                continue

            html_path = os.path.join(root, file)
            base_name = os.path.splitext(file)[0]
            fa_path = os.path.join(root, f"{base_name}.fa")

            if not os.path.exists(fa_path):
                print(f"⚠️ 未找到 .fa 文件: {fa_path}")
                continue

            seq_ids = extract_unannotated_seq_ids(html_path)
            if not seq_ids:
                continue

            for seq_id in seq_ids:
                print(f"\n🔍 未分类序列: {seq_id}")
                sequence = extract_sequence_from_fasta(fa_path, seq_id)
                if not sequence:
                    print(f"❌ 未找到对应序列内容: {seq_id}")
                    continue

                json_path = create_json_from_seq(seq_id, sequence)
                if json_path:
                    unclassified_ids.append(seq_id)
                    run_step1(os.path.basename(json_path))

    with open(output_txt, 'w') as f:
        for sid in unclassified_ids:
            f.write(sid + "\n")

    print(f"\n📄 已保存未注释序列列表到: {output_txt}")


if __name__ == "__main__":
    main()
