# Load PDB files
load A0K832.pdb, ref_model
load 3WDL_B.pdb, target_model

# Color for clarity
color cyan, ref_model
color orange, target_model

# Align target_model to ref_model
align target_model, ref_model

# Zoom in on both
zoom ref_model or target_model

# Show cartoons for clarity
hide everything
show cartoon, all

# Optional: Add transparency to reference
set cartoon_transparency, 0.3, ref_model

# Print RMSD value to the command line
rms_cur target_model, ref_model

# Save the aligned structure (optional)
save target_model_aligned.pdb, target_model

# Save image (optional)
png /Users/jason/Documents/webserver/jiajun/true.png, dpi=300
