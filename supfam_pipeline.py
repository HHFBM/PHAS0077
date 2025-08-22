import os
import re
import subprocess
import argparse

def run_supfam(fasta_path, supfam_dir):
    """
    使用 superfamily.pl 运行 SUPFAM 注释
    :param fasta_path: 输入的 FASTA 文件路径
    :param supfam_dir: superfamily.pl 所在目录
    :return: 生成的 HTML 文件路径，若失败返回 None
    """
    fasta_name = os.path.basename(fasta_path)
    base_name = os.path.splitext(fasta_name)[0]
    html_path = os.path.join(supfam_dir, f"{base_name}.html")

    print(f"🚀 Running SUPFAM on {fasta_name} ...")
    result = subprocess.run(
        [os.path.join(supfam_dir, "superfamily.pl"), fasta_path],
        cwd=supfam_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ SUPFAM execution failed: {result.stderr}")
        return None

    if not os.path.exists(html_path):
        print(f"❌ Expected HTML output not found: {html_path}")
        return None

    print(f"✅ SUPFAM annotation done: {html_path}")
    return html_path


def extract_sf_id(html_path):
    """
    从 HTML 文件中提取 superfamily ID
    :param html_path: SUPFAM 生成的 HTML 文件
    :return: superfamily ID（如 '3.40.50.300'），若失败返回 None
    """
    try:
        with open(html_path, "r") as f:
            html_content = f.read()
        match = re.search(r"Superfamily\s+ID[:：]?\s*([\d\.]+)", html_content)
        if match:
            sf_id = match.group(1).strip()
            print(f"✅ Extracted Superfamily ID: {sf_id}")
            return sf_id
        else:
            print(f"❌ No Superfamily ID found in {html_path}")
            return None
    except Exception as e:
        print(f"❌ Failed to parse {html_path}: {e}")
        return None


def check_ntp_superfamily(sf_id, ntp_list_file):
    """
    检查提取的 superfamily ID 是否在 NTP-processing 列表中
    :param sf_id: 提取的 superfamily ID
    :param ntp_list_file: NTP-processing SF 列表路径
    :return: True / False
    """
    try:
        with open(ntp_list_file, "r") as f:
            ntp_ids = {line.strip() for line in f if line.strip()}
        if sf_id in ntp_ids:
            print(f"✅ {sf_id} belongs to NTP-processing superfamily.")
            return True
        else:
            print(f"❌ {sf_id} is NOT an NTP-processing superfamily.")
            return False
    except FileNotFoundError:
        print(f"❌ NTP list file not found: {ntp_list_file}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SUPFAM annotation script")
    parser.add_argument("--fasta", required=True, help="Path to the input FASTA file")
    parser.add_argument("--supfam_dir", default="/mnt/data2/supfam/supfam", help="Path to SUPFAM tool directory")
    parser.add_argument("--ntp_list", default="/mnt/data2/supfam/jiajun/data/ntp_sf_list.txt",
                        help="Path to NTP-processing superfamily list")
    args = parser.parse_args()

    html_path = run_supfam(args.fasta, args.supfam_dir)
    if not html_path:
        exit(1)

    sf_id = extract_sf_id(html_path)
    if not sf_id:
        exit(1)

    is_ntp = check_ntp_superfamily(sf_id, args.ntp_list)
    if is_ntp:
        print("🎉 SUPFAM matched NTP-processing superfamily. Pipeline stops here.")
        exit(0)
    else:
        print("➡️ SUPFAM did not match NTP-processing superfamily. Proceed to next step.")
        exit(2)


if __name__ == "__main__":
    main()
