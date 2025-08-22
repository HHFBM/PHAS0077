import os
import pandas as pd
from glob import glob

def extract_template_name(filename):
    # 示例: q8puA_vs_3wdlC.txt → 3WDL
    parts = filename.lower().split("_vs_")
    if len(parts) == 2:
        pdb_chain = parts[1].split(".")[0]  # 3wdlC
        pdb_code = pdb_chain[:4].upper()    # 3WDL
        return pdb_code
    return None

def generate_single_pml(zscore_path, pred_dir, template_dir, output_dir):
    basename = os.path.basename(zscore_path).replace("_zscores.csv", "")
    pred_pdb = os.path.join(pred_dir, f"{basename}_sample_0.pdb")

    if not os.path.exists(pred_pdb):
        print(f"❌ Predicted PDB not found: {pred_pdb}")
        return None

    try:
        df = pd.read_csv(zscore_path)
        df = df.sort_values(by="Z-score", ascending=False)
        if df.empty:
            print(f"❌ Empty Z-score file: {zscore_path}")
            return None
        top_filename = df.iloc[0]["filename"]
        top_template_code = extract_template_name(top_filename)
        z = df.iloc[0]["Z-score"]
    except Exception as e:
        print(f"❌ Failed to read {zscore_path}: {e}")
        return None

    template_pdb = os.path.join(template_dir, f"{top_template_code}.pdb")
    if not os.path.exists(template_pdb):
        print(f"❌ Template PDB not found: {template_pdb}")
        return None

    os.makedirs(output_dir, exist_ok=True)
    output_pml = os.path.join(output_dir, f"{basename}_top1_align.pml")

    with open(output_pml, "w") as f:
        f.write(f"# Alignment: {basename} vs {top_template_code} (Z={z})\n")
        f.write(f"load {pred_pdb}, pred\n")
        f.write(f"load {template_pdb}, ref\n")
        f.write("align pred, ref\n\n")
        f.write("hide everything\nshow cartoon, all\n")
        f.write("color cyan, pred\ncolor white, ref\n")
        f.write("bg_color white\nset cartoon_transparency, 0.2\nzoom all\n")
        f.write("select ligand, resn ATP\nshow sticks, ligand\ncolor orange, ligand\n")

    print(f"✅ Generated PML: {output_pml}")
    return output_pml


def batch_generate(zscore_dir, pred_dir, template_dir, output_dir):
    zscore_files = glob(os.path.join(zscore_dir, "*_zscores.csv"))
    for zf in zscore_files:
        generate_single_pml(zf, pred_dir, template_dir, output_dir)


if __name__ == "__main__":
    # 修改成你当前的路径
    batch_generate(
        zscore_dir="/mnt/data2/supfam/jiajun/run/batch_results/",
        pred_dir="/mnt/data2/supfam/jiajun/run/predicted_structures/",
        template_dir="/mnt/data2/supfam/jiajun/superfamily_pdbs/",
        output_dir="/mnt/data2/supfam/jiajun/run/vis_scripts/"
    )
