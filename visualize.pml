
load model1.pdb, model1
load 8DCD.pdb, model2
align model1, model2

select atp, resn ATP
show sticks, atp
color yellow, atp

select near_atp, (byres (all within 4 of atp)) and polymer
show sticks, near_atp
color cyan, near_atp
util.cbag near_atp

ray 1200,900
png model1_vs_8DCD_20250805_203426.png
quit
