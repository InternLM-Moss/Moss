# Moss🤖 大模型AI任务
## 简介
在当今快速发展的数字化时代，人工智能技术已经成为推动企业创新和效率提升的关键驱动力之一。为满足企业在任务调度和智能管理方面的需求，团队基于大模型技术开发了一款名为Moss的高度智能化AI助手。Moss通过调用大模型，利用槽位填充技术，实现复杂任务的智能调度和处理，从而提高工作效率，降低人力成本，为企业创造更大的价值。
Moss具备实时反馈机制，能够及时识别和处理异常情况。
通过先进的槽位填充技术，Moss可以有效地将用户提供的信息（槽位）填入预定义的模板中，生成完整的任务调度指令，实现对复杂任务的智能管理和执行。


## 环境准备

- 借助 conda 准备虚拟环境

  ```bash
  conda create --name one-company python=3.10 -y
  conda activate one-company
  ```
- 安装依赖包

  ```bash
  pip install -r requeirements.txt
  ```
  
## 运行服务端
- 执行运行diggerLM服务端程序
  ```bash
  python3 -m diggerLM.main --run
  ```
