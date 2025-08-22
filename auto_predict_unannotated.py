import os
import subprocess
from bs4 import BeautifulSoup

# 路径配置
sp_results_root = "/mnt/data2/supfam/jiajun/run/sp_results/"
step1_script = "/mnt/data2/supfam/jiajun/run/step1.py"
output_txt = "unclassified_seq_ids.txt"

# 存储无注释序列的 Seq_ID 列表
unannotated_ids = []

def extract_unannotated_seq_ids(html_path):
    with open(html_path, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')

    table_rows = soup.find_all('tr')
    records = []

    for row in table_rows[1:]:  # Skip header
        cols = row.find_all('td')
        if not cols:
            continue
        seq_id = cols[0].get_text(strip=True)
        all_empty = all(col.get_text(strip=True) in ["", "-", "–"] for col in cols[1:])
        records.append((seq_id, all_empty))

    # Group by seq_id → check if **all** entries for the same seq_id are empty
    from collections import defaultdict
    group = defaultdict(list)
    for seq_id, is_empty in records:
        group[seq_id].append(is_empty)

    unclassified_ids = [seq_id for seq_id, flags in group.items() if all(flags)]
    return unclassified_ids

def process_html_and_predict():
    for root, _, files in os.walk(sp_results_root):
        for file in files:
            if not file.endswith(".html"):
                continue

            html_path = os.path.join(root, file)
            base_name = os.path.splitext(file)[0]
            fa_path = os.path.join(root, f"{base_name}.fa")

            if not os.path.exists(fa_path):
                print(f"⚠️ No corresponding .fa file for {html_path}")
                continue

            # 提取无注释序列 ID
            unclassified_seq_ids = extract_unannotated_seq_ids(html_path)

            if not unclassified_seq_ids:
                continue

            for seq_id in unclassified_seq_ids:
                unannotated_ids.append(seq_id)
                print(f"\n🔍 Found unannotated sequence: {seq_id}")
                print(f"🎯 Running step1.py for: {fa_path}")
                try:
                    subprocess.run(
                        ["python", step1_script, "--input", fa_path],
                        check=True
                    )
                    print(f"✅ Finished: {seq_id}")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed on: {seq_id}")
                    print(str(e))

if __name__ == "__main__":
    process_html_and_predict()

    # 写入未分类 ID
    with open(output_txt, 'w') as f:
        for seq_id in unannotated_ids:
            f.write(seq_id + "\n")

    print(f"\n📄 All unannotated Seq_IDs saved to: {output_txt}")
