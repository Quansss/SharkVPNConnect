import os
import shutil
import json
from pathlib import Path

base_dir = Path("C:\\Users\\15062\\.qclaw\\workspace\\palworld-client-app")
dist_dir = base_dir / "dist"
release_dir = base_dir / "release" / "PalworldClient-v1.0.0"

# 清理
if release_dir.exists():
    shutil.rmtree(release_dir)
release_dir.mkdir(parents=True, exist_ok=True)

# 复制 exe
shutil.copy(dist_dir / "PalworldClient.exe", release_dir)
shutil.copy(dist_dir / "LicenseGenerator.exe", release_dir)

# 配置文件
config = {
    "server": "sharkconnect.sharkos.cn:11010",
    "protocol": "tcp",
    "network_name": "palworld",
    "network_secret": "PALWORLD2024SECRET",
    "game_server": "10.144.0.1:8211"
}
with open(release_dir / "server_config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

# 说明
readme = """Palworld 联机客户端 v1.0.0
================================

文件说明
--------
PalworldClient.exe    - 客户端程序（给朋友使用）
LicenseGenerator.exe  - 授权码生成器（你自己使用）
server_config.json    - 服务器配置文件

使用流程
--------
1. 【你】运行 LicenseGenerator.exe
2. 【朋友】运行 PalworldClient.exe，复制机器码发给你
3. 【你】在生成器中输入机器码，生成授权码
4. 【朋友】在客户端输入授权码，验证通过
5. 【朋友】点击"启动组网"，等待连接成功
6. 【朋友】启动帕鲁游戏，加入多人游戏
7. 【朋友】输入服务器地址: 10.144.0.1:8211

授权说明
--------
- 每个授权码绑定一台机器
- 支持 7/30/90/365 天有效期
- 过期后需要重新授权

授权码格式
--------
- 24位字母数字组合
- 大小写不敏感
- 例: A1B2C3D4E5F6G7H8I9J0K1L2
"""
with open(release_dir / "README.txt", "w", encoding="utf-8") as f:
    f.write(readme)

# 打包
zip_path = base_dir / "release" / "PalworldClient-v1.0.0.zip"
shutil.make_archive(str(zip_path).replace(".zip", ""), 'zip', release_dir)

print(f"打包完成: {zip_path}")
print(f"大小: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
print("\n文件列表:")
for f in sorted(release_dir.iterdir()):
    size = f.stat().st_size / 1024
    print(f"  {f.name:30} {size:>8.1f} KB")
