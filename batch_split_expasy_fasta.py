import os

def split_fasta(input_fasta, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    with open(input_fasta, 'r') as infile:
        content = infile.read()

    entries = content.strip().split('>')[1:]  # 跳过空项
    for entry in entries:
        lines = entry.strip().split('\n')
        header = lines[0]
        seq = '\n'.join(lines[1:])
        protein_id = header.split('|')[1] if '|' in header else header.split()[0]
        output_path = os.path.join(output_dir, f"{protein_id}.fa")

        with open(output_path, 'w') as outfile:
            outfile.write(f">{header}\n{seq}\n")

def batch_split_expasy_folder(expasy_dir, output_root):
    for filename in os.listdir(expasy_dir):
        if filename.endswith(".fa"):
            input_fasta = os.path.join(expasy_dir, filename)
            base_name = os.path.splitext(filename)[0]
            output_dir = os.path.join(output_root, base_name)
            print(f"▶ 拆分: {filename} → {output_dir}")
            split_fasta(input_fasta, output_dir)
    print("✅ 所有FASTA文件处理完毕。")

# 示例调用
if __name__ == "__main__":
    expasy_folder = "/mnt/data2/supfam/expasy"
    output_root = "/mnt/data2/supfam/jiajun/split_fasta"
    batch_split_expasy_folder(expasy_folder, output_root)
