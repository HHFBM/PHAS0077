import os
import argparse
import subprocess

def predict_with_protenix(json_file):
    # 获取不含扩展名的文件名作为输出前缀
    json_filename = os.path.basename(json_file)
    output_name = os.path.splitext(json_filename)[0]
    output_dir = f"./{output_name}_output"

    # 构造命令
    cmd = [
        "protenix", "predict",
        "--input", json_file,
        "--out_dir", output_dir,
        "--seeds", "101",
        "--use_msa_server"
    ]

    print(f"[INFO] 开始 ProteinX 结构预测：{json_file}")
    try:
        subprocess.run(cmd, check=True)
        print(f"[✅] 预测完成，结果输出到: {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"[❌] 调用 ProteinX 失败：{e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用 ProteinX 预测结构（输入为 JSON 文件）")
    parser.add_argument("json_file", type=str, help="输入的 ProteinX JSON 文件路径")

    args = parser.parse_args()
    predict_with_protenix(args.json_file)
