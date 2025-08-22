# 加载两个 PDB 文件
load model1.pdb, model1
load 7TGK_D.pdb, model2

# 对齐两个结构
align model1, model2

# 选择并显示 ATP 分子
select atp, resn ATP
show sticks, atp
color yellow, atp

# 显示 4Å 范围内的氨基酸残基
select near_atp, (byres (all within 4 of atp)) and polymer
show sticks, near_atp
color cyan, near_atp
util.cbag near_atp

# 美化图像并截图
ray 1200,900
png atp_binding_site.png
