# Serverless in the wild论文复现项目介绍

## 论文见解

见同文件的[paper.md](paper.md)

## 如何运行

### 下载可执行程序

会放到release下，后端源码可能也需要下载与exe在同一目录下。

### 下载数据集

运行/backend/目录下的[download.exe](backend/download.exe)文件，下载数据集到/backend/data/目录下。


或者手动下载（论文中官方数据集）：
https://azurepublicdatasettraces.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2019/azurefunctions-dataset2019.tar.xz
### 运行后端服务

运行/backend/目录下的[main.exe](backend/main.exe)文件，启动后端服务。

### 访问前端网址

打开浏览器，访问在线网址：https://likewind221.top:9000/

## 源代码

### 安装与启动
python:
> pip install -r requirements.txt

Vue.js:
> npm i
> npm run dev

### 技术栈
前端：Vue.js + Element Plus + TypeScript  
后端：Python + FastApi

前端部署：ubuntu + nginx
### 目录结构

```
serverless/
├── backend/  # 后端代码  
│   ├── result/  # 存放模拟器运行结果
│   ├── data/  # 数据集  
│   ├── download.exe  # 下载数据集的工具  
│   ├── main.exe  # 启动后端服务的入口文件
│   ├── requirements.txt  # 后端依赖
│   ├── model.py  # 源码，模拟器类
│   ├── record.py  # 源码，记录类
│   ├── dataset.py  # 源码，数据集类
│   ├── controller.py  # 源码，控制器类
│   ├── compute_node.py  # 源码，计算节点类
│   └── main.py # 源码，后端服务入口文件   
├── frontend/  # 前端代码
│   ├── public/  # 静态资源
│   ├── src/  # 前端源代码
│   ├── package.json  # 前端依赖
│   ├── tsconfig.json  # 前端TypeScript配置
│   └── vue.config.js  # 前端Vue配置
├── README.md  # 项目说明
└── paper.md  # 中文版项目说明
```