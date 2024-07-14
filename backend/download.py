import os
import requests
from tqdm import tqdm
import tarfile

# 定义URL和目标目录
url = "https://azurepublicdatasettraces.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2019/azurefunctions-dataset2019.tar.xz"
target_dir = os.path.join(os.getcwd(), 'data')

# 确保目标目录存在
os.makedirs(target_dir, exist_ok=True)

# 定义目标文件路径
target_file = os.path.join(target_dir, 'azurefunctions-dataset2019.tar.xz')

# 获取文件总大小
response = requests.head(url)
total_size = int(response.headers.get('content-length', 0))

# 检查目标文件是否已经存在且完整
if os.path.exists(target_file):
    if os.path.getsize(target_file) == total_size:
        print(f"文件已存在且完整: {target_file}")
    else:
        print(f"文件已存在但不完整，重新下载: {target_file}")
else:
    print(f"文件不存在，开始下载: {target_file}")

# 下载文件
if not (os.path.exists(target_file) and os.path.getsize(target_file) == total_size):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        # 使用tqdm创建进度条
        progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
        
        with open(target_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    progress_bar.update(len(chunk))
                    file.write(chunk)
        progress_bar.close()
        
        if total_size != 0 and progress_bar.n != total_size:
            print("下载过程中可能出现了错误")
        else:
            print(f"文件已成功下载到 {target_file}")
    else:
        print(f"下载失败，状态码: {response.status_code}")

# 解压文件
if os.path.exists(target_file) and os.path.getsize(target_file) == total_size:
    print(f"开始解压文件: {target_file}")
    with tarfile.open(target_file, 'r:xz') as tar:
        tar.extractall(path=target_dir)
    print(f"文件已成功解压到 {target_dir}")
else:
    print("文件不完整，无法解压")
