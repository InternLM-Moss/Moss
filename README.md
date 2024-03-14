# Moss🤖
<p align="left">
    <a href="./LICENSE"><img src="https://img.shields.io/badge/license-GNU-dfd.svg"></a>
    <a href=""><img src="https://img.shields.io/badge/series-AI_Operating-yellow.svg"></a>
    <a href=""><img src="https://img.shields.io/badge/python-3.9+-aff.svg"></a>
</p>

基于大模型的AI任务机器人系统，添加[微信](assets/moss_bot_wechat.png)直接体验Moss🤖效果

Moss是基于 LLM 的任务机器人助手，以下几大能力：

1. 应对微信私聊、群聊等场景，基于国产InternLM大模型解答用户问题，时延低
2. 完整的大模型任务执行管理框架，采用 ```LLM识别``` + ```高级代码模块``` 实现大模型语义理解、任务调度、执行作业等
3. 一套完整的作业后台管理系统，部署成本低，可扩展性极强：采用 ```低代码平台``` + ```Falcon RESTful API```


## DiggerLM 大模型任务管理 

**代码路径:** `MOSS/diggerLM`

### 环境部署

- 借助 conda 准备虚拟环境

  ```bash
  conda create --name moss python=3.10 -y
  conda activate moss
  ```
- 安装依赖包

  ```bash
  pip install -r diggerLM/requeirements.txt
  ```
  
### 运行服务端

- 执行运行diggerLM服务端程序
  ```bash
  pythonß -m diggerLM.main --run
  ```

## CookJobs 作业后台管理系统 

**代码路径:** `MOSS/cookjobs`

- 初始化DB: SQLlite3

  ```bash
  cd cookjobs/server
  python manage.py initdb
  ```
- 运行前后端程序

  ```bash
  cd cookjobs/server
  python manage.py runserver
  ```

## 微信聊天机器人

本文参考 https://github.com/ethanhwang1024/AI-Operating-Wechat 

实现自动回复微信聊天，支持私聊和群聊（需要手动@）。只支持中文Windows客户端。

## 快速开始

- 安装依赖：
  ```bash
  pip install -r assistant/requirement.txt
  ```

- 打开电脑微信窗口，确保整个窗口可见

- 运行程序
  ```bash 
  cd assistant
  python main.py
  ```