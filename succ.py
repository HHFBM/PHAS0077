#!/usr/bin/env python3
"""
Remote processing script - Run all AlphaFold predictions and subsequent processing steps on remote server
Please place this script in the ~/student/students_webserver/zhijing/ directory on the remote server
"""

import os
import sys
import subprocess
import argparse
import time
import glob


class RemotePipeline:
    def __init__(self, json_filename):
        self.json_filename = json_filename
        self.output_name = os.path.splitext(json_filename)[0]
        self.base_dir = os.path.expanduser("~/student/students_webserver/zhijing")
        self.input_dir = os.path.join(self.base_dir, "input_jsons")
        self.output_dir = os.path.join(self.base_dir, "predicted_structures")

    def run_alphafold_prediction(self):
        """Run AlphaFold prediction"""
        print(f"🔬 Starting AlphaFold prediction...")

        # Ensure we're in the correct directory
        os.chdir(self.base_dir)

        # Build command
        cmd = [
            "protenix", "predict",
            "--input", f"{self.input_dir}/{self.json_filename}",
            "--out_dir", f"./{self.output_name}_output",
            "--seeds", "101",
            "--use_msa_server"
        ]

        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ AlphaFold prediction failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False

        print(f"✅ AlphaFold prediction completed")
        return True

    def convert_cif_to_pdb(self):
        """Convert CIF file to PDB file"""
        print(f"🔄 Converting CIF file to PDB file...")

        # The actual output path is sequence_1_output instead of predicted_structures
        actual_output_dir = f"{self.base_dir}/{self.output_name}_output"
        cif_pattern = f"{actual_output_dir}/{self.output_name}/seed_101/predictions/{self.output_name}_seed_101_sample_0.cif"

        print(f"Looking for CIF file: {cif_pattern}")

        if not os.path.exists(cif_pattern):
            print(f"❌ CIF file not found: {cif_pattern}")
            # Try to find with wildcard
            cif_files = glob.glob(f"{actual_output_dir}/{self.output_name}/seed_101/predictions/*sample_0.cif")
            if cif_files:
                cif_pattern = cif_files[0]
                print(f"Found CIF file: {cif_pattern}")
            else:
                return False

        # Generate output PDB filename to predicted_structures directory
        os.makedirs(self.output_dir, exist_ok=True)
        pdb_file = f"{self.output_dir}/{self.output_name}_sample_0.pdb"

        # Run conversion script
        cmd = ["python", "convert_cif_to_pdb.py", cif_pattern, pdb_file]
        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ CIF to PDB conversion failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False

        print(f"✅ CIF to PDB conversion completed")
        print(result.stdout)
        return True

    def convert_pdb_to_dat(self):
        """Convert PDB file to DAT file"""
        print(f"🔄 Converting PDB file to DAT file...")

        # Look for the converted PDB file
        pdb_file = f"{self.output_dir}/{self.output_name}_sample_0.pdb"

        if not os.path.exists(pdb_file):
            print(f"❌ PDB file does not exist: {pdb_file}")
            return False

        print(f"Found PDB file: {pdb_file}")

        # Run conversion script (your script will automatically process all PDB files in predicted_structures directory)
        cmd = ["python", "import_pdbs_to_dat.py"]
        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ PDB to DAT conversion failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False

        print(f"✅ PDB to DAT conversion completed")
        print(result.stdout)
        return True

    def run_dali_comparison(self):
        """Run DALI structure comparison"""
        print(f"🔍 Starting DALI structure comparison...")

        # Ensure we're in the correct directory
        os.chdir(self.base_dir)

        # Create dali_results directory
        os.makedirs("dali_results", exist_ok=True)

        # According to import_pdbs_to_dat.py script, query structure name is first 4 characters lowercase
        # sequence_1 -> sequ
        query_name = (self.output_name[:4].lower() + "xxx")[:4]

        # But from your manual testing, it actually uses sequA
        # Let's first check the actual files in query_structures_DAT directory
        dat_files_in_query = []
        if os.path.exists("query_structures_DAT"):
            dat_files_in_query = [f for f in os.listdir("query_structures_DAT") if f.endswith('.dat')]

        if dat_files_in_query:
            # Use the actual generated DAT filename as query structure name
            actual_query_name = os.path.splitext(dat_files_in_query[0])[0]
            print(f"Query structure name found in query_structures_DAT: {actual_query_name}")
            query_name = actual_query_name
        else:
            print(f"⚠️ No DAT files found in query_structures_DAT directory, using default name: {query_name}")

        print(f"Using query structure name: {query_name}")

        # Check DAT directory
        dat_dir = "DAT"
        if not os.path.exists(dat_dir):
            print(f"❌ DAT directory does not exist: {dat_dir}")
            return False

        # Get all DAT files
        dat_files = [f for f in os.listdir(dat_dir) if f.endswith('.dat')]
        if not dat_files:
            print(f"❌ No .dat files found in DAT directory")
            return False

        print(f"Found {len(dat_files)} reference structures")

        # Run DALI comparison for each DAT file
        successful_comparisons = 0
        for dat_file in dat_files:
            ref_id = os.path.splitext(dat_file)[0]
            print(f"🔗 Comparing {query_name} vs {ref_id}")

            cmd = [
                "/home/wenhao/6tx0/software/dali/DaliLite.v5/bin/dali.pl",
                "--cd1", query_name,
                "--cd2", ref_id,
                "--dat1", "query_structures_DAT",
                "--dat2", "DAT",
                "--outfmt", "summary",
                "--clean"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"⚠️ DALI comparison failed for {ref_id}: {result.stderr}")
                continue

            # DALI generates query_name.txt file by default, need to move to dali_results directory
            default_output = f"{query_name}.txt"
            target_output = f"dali_results/{query_name}_vs_{ref_id}.txt"

            if os.path.exists(default_output):
                try:
                    os.rename(default_output, target_output)
                    successful_comparisons += 1
                    print(f"✅ Successfully compared {ref_id}, result saved to {target_output}")
                except Exception as e:
                    print(f"⚠️ Failed to move output file: {e}")
            else:
                print(f"⚠️ Output file not found: {default_output}")

        print(f"✅ DALI comparison completed, successfully compared {successful_comparisons} structures")

        # Check generated result files
        if os.path.exists("dali_results"):
            result_files = os.listdir("dali_results")
            print(f"📁 Generated result files: {len(result_files)} files")
            for f in result_files[:5]:  # Show first 5 files
                print(f"  - {f}")

        return successful_comparisons > 0

    def extract_results(self):
        """Extract Z-score results"""
        print(f"📊 Extracting results...")

        # Check if dali_results directory exists
        if not os.path.exists("dali_results"):
            print(f"❌ dali_results directory does not exist, please run DALI comparison first")
            return False

        cmd = ["python", "extract_zscores.py"]
        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Result extraction failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False

        print(f"✅ Result extraction completed")
        print(result.stdout)
        return True

    def check_prerequisites(self):
        """Check required files and directories"""
        print(f"🔍 Checking environment...")

        # Check input file
        input_file = f"{self.input_dir}/{self.json_filename}"
        if not os.path.exists(input_file):
            print(f"❌ Input file does not exist: {input_file}")
            return False

        # Check script files
        required_scripts = [
            "convert_cif_to_pdb.py",
            "import_pdbs_to_dat.py",
            "extract_zscores.py"
        ]

        for script in required_scripts:
            if not os.path.exists(script):
                print(f"❌ Missing required script: {script}")
                return False

        # Check directories
        required_dirs = [
            "DAT",
            "query_structures_DAT",
            "predicted_structures"
        ]

        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                print(f"❌ Missing required directory: {dir_name}")
                return False

        print(f"✅ Environment check passed")
        return True

    def debug_find_output_files(self):
        """Debug: Find prediction output files"""
        print(f"🔍 Finding prediction output files...")

        base_dir = os.path.expanduser("~/student/students_webserver/zhijing")

        debug_commands = [
            f"find {base_dir} -name '*{self.output_name}*' -type d",
            f"find {base_dir} -name '*{self.output_name}*' -type f",
            f"find {base_dir} -name '*.cif' | grep {self.output_name}",
            f"ls -la {base_dir}/predicted_structures/",
            f"find {base_dir} -name '*sequence_1*' | head -20",
            f"find {base_dir} -name '*.cif' | head -20"
        ]

        for cmd in debug_commands:
            print(f"Executing: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(f"Output: {result.stdout.strip()}")
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
            print("-" * 40)

    def run_pipeline(self):
        """Run complete remote processing pipeline"""
        print(f"🚀 Starting remote processing pipeline...")
        print(f"📋 JSON file: {self.json_filename}")
        print(f"📋 Output name: {self.output_name}")
        print(f"📋 Working directory: {self.base_dir}")
        print("=" * 50)

        try:
            # Step 1: Check environment
            if not self.check_prerequisites():
                return False

            # Step 2: Run AlphaFold prediction
            if not self.run_alphafold_prediction():
                return False

            # Step 3: Convert CIF to PDB
            if not self.convert_cif_to_pdb():
                return False

            # Step 4: Convert PDB to DAT
            if not self.convert_pdb_to_dat():
                return False

            # Step 5: Run DALI comparison
            if not self.run_dali_comparison():
                return False

            # Step 6: Extract results
            if not self.extract_results():
                return False

            print("=" * 50)
            print("🎉 All steps completed!")

        except Exception as e:
            print(f"❌ Pipeline execution failed: {str(e)}")
            return False

        return True


def main():
    parser = argparse.ArgumentParser(description='Remote AlphaFold prediction and structure comparison pipeline')
    parser.add_argument('json_filename', help='JSON filename (not path, just filename)')
    parser.add_argument('--check', '-c', action='store_true', help='Only check environment, do not run pipeline')
    parser.add_argument('--find-files', '-f', action='store_true', help='Find output files')
    parser.add_argument('--skip-prediction', '-s', action='store_true',
                        help='Skip prediction step, directly process existing files')

    args = parser.parse_args()

    pipeline = RemotePipeline(args.json_filename)

    if args.check:
        print("🔍 Check mode")
        success = pipeline.check_prerequisites()
        if success:
            print("✅ Environment check passed, pipeline can be run")
        return

    if args.find_files:
        print("🔍 Find files mode")
        pipeline.debug_find_output_files()
        return

    if args.skip_prediction:
        print("⏭️ Skipping prediction step")
        try:
            # Skip prediction, start directly from conversion
            if not pipeline.convert_cif_to_pdb():
                print("💥 CIF to PDB conversion failed!")
                sys.exit(1)

            if not pipeline.convert_pdb_to_dat():
                print("💥 PDB to DAT conversion failed!")
                sys.exit(1)

            if not pipeline.run_dali_comparison():
                print("💥 DALI comparison failed!")
                sys.exit(1)

            if not pipeline.extract_results():
                print("💥 Result extraction failed!")
                sys.exit(1)

            print("🎉 Processing completed!")

        except Exception as e:
            print(f"❌ Processing failed: {str(e)}")
            sys.exit(1)
        return

    # Run complete pipeline
    success = pipeline.run_pipeline()

    if success:
        print("\n🎊 Pipeline executed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Pipeline execution failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
