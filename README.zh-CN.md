# AI Computational Chemist（AICC）

[English](README.md) | 简体中文

AICC 是一套面向计算化学与材料科学的 Agent 技能框架，兼容不同的 Agent
运行环境。

它把科研请求整理成可追踪的计算流程：明确计算目标、保留方法来源、准备输入、
取得人工批准、在本地或 HPC 上执行、验证输出，最后生成可以写进报告的证据。
Claude Code、Codex、Cursor、opencode、DSH，以及能够发现 `SKILL.md` 的自定义
Agent 都可以使用这套框架。

AICC 遵守两条基本规则：

1. 计算方法必须来自原稿、文献或明确批准的方案；
2. 调度器显示成功不等于科学计算有效。只有通过解析、收敛性、来源和科学验收，
   结果才能进入报告。

## 系统架构

计算服务器上不需要安装 Agent。

```text
Windows 工作站
  DSH / Codex / Claude
          |
          | 发现 AICC Skills，维护 .research 状态
          v
  本地 remote-compute MCP 网关
          |
          | OpenSSH/SCP：只传输受限文件，执行网关生成的固定操作
          v
Linux 计算服务器
  SSH + GNU 工具 + Slurm/PBS + 科学计算软件
  不安装 Agent，不运行 MCP 服务，不保存模型 API Key
```

Skill 保存科研知识和软件操作规则，本地 MCP 网关提供受限的远程执行能力。
`.research/` 是工作站上的控制面，记录任务、审批和证据；计算文件与调度器是服务器
上的执行面。

## AICC 能做什么

- 根据论文、补充材料和审稿意见规划补充计算，生成经过验证的回复信和 SI 内容；
- 用任务 DAG、决策、产物、事件、租约和验收门管理复杂科研项目；
- 操作 VASP、CP2K、Gaussian、GROMACS、LAMMPS、DeePMD、phonopy、CatMAP、
  LOBSTER、Multiwfn、VASPKIT 和 OVITO 等工具；
- 生成分子、表面、缺陷和吸附结构，并在昂贵计算前执行独立结构审查；
- 支持本地、调度器、持久远程 Shell，以及无 Agent 的远程执行模式；
- 用确定性的预检查和解析器识别失败，避免把未完成的输出当成科研结果。

## 选择执行方式

| 场景 | 使用方式 | 服务器安装 Agent？ |
|---|---|---:|
| Agent 和计算软件在同一台机器 | 计算引擎 Skill + `hpc-submit` | 已在本地 |
| 从 Windows 下发普通 SSH/Slurm/PBS 任务 | `remote-compute` + `hpc-submit` | 否 |
| 交互排错需要持续的工作目录、环境变量或 `tmux` | `rsess` + `hpc-submit` | 否 |
| 机构明确选择在集群部署 Agent | 计算引擎 Skill + HPC Skill | 是 |

通常的无 Agent 远程计算应使用 `remote-compute`。它只提供目标探测、文件暂存、
任务提交、状态查询、限量日志读取、产物校验、下载和取消等明确操作，不提供任意
Shell 命令接口。

## 快速开始：安装 Skills

把技能集合安装到 Agent 使用的技能目录：

```bash
./install.sh --target ~/.codex/skills
./install.sh --target ~/.claude/skills --harness claude --project /path/to/work
```

安装脚本只部署 Skills，不会安装 VASP、Gaussian、GROMACS、LAMMPS、调度器、
赝势、基组、授权数据或容器镜像。

也可以手动安装：

- Claude Code：让 `procedures/*/` 和 `tools/*/` 在 Claude 的技能目录中可见，
  并把 `AGENTS.md` 作为项目指令加载；
- Codex 或其他支持 `AGENTS.md` 的 Agent：把 `AGENTS.md` 放在项目根目录，
  再将技能目录复制或链接到对应位置；
- 自定义 Agent：用每个 Skill 的 frontmatter `description` 做路由，并把
  `AGENTS.md` 作为系统指令或项目指令。

`knowledge/` 是共享科研知识库，不是一组独立 Skills，不要把其中每个文件注册成
工具。

## 快速开始：通过 Windows DSH 连接计算服务器

### 1. 准备工作站

工作站需要：

- Python 3.11 或更高版本；
- Windows OpenSSH 的 `ssh.exe` 和 `scp.exe`；
- 已测试的 OpenSSH 别名，使用密钥或 SSH Agent 完成非交互认证；
- 已核对并写入 `known_hosts` 的服务器指纹。

服务器需要 GNU 兼容的 `sh`、`sha256sum`、`stat`、`find`、`realpath`、
`tail` 和 `mv`，以及 Slurm 或 PBS 与实际使用的科学计算软件。

### 2. 创建本地私有配置

将示例复制到仓库外：

```powershell
Copy-Item `
  .\tools\remote-compute\examples\config.example.json `
  "$env:USERPROFILE\.dsh\remote-compute.private.json"
```

替换文件里的占位符，并设置范围尽可能小的目录：

- `allowedUploadRoots`：允许上传的已准备任务目录；
- `allowedDownloadRoots`：允许保存下载结果的目录；
- `allowedResearchRoots`：其中 `.research/decisions.jsonl` 可以批准提交或取消的
  科研项目；
- `remoteRoot`：网关在服务器上唯一可以访问的任务根目录。

初次配置时让 `submitEnabled` 和 `cancelEnabled` 保持 `false`。私有配置不得提交
到 Git。

不连接服务器即可检查配置格式：

```powershell
C:\Users\REPLACE_USER\miniconda3\python.exe `
  .\tools\remote-compute\scripts\remote_compute_mcp.py `
  --config "$env:USERPROFILE\.dsh\remote-compute.private.json" `
  --check-config
```

### 3. 创建 DSH 科研模式并注册 MCP 网关

在 DSH 的 Agent Presets 设置中复制随软件发布的 `standard` preset，新 preset 的
ID 填写 `sci`。然后把
[`tools/remote-compute/examples/dsh-sci.cordis.example.yml`](tools/remote-compute/examples/dsh-sci.cordis.example.yml)
中的直接插件行追加到 `sci/agent.cordis.yml`，并替换所有 `REPLACE_*` 值。这个示例
是 preset composition 条目，不是 profile `cordis.patch.yml` 操作。不要修改 DSH
随软件发布的 preset。保存后新建一个使用 `sci` 的会话。

注册后，DSH 会看到以下工具：

```text
mcp__aicc-compute__compute_list_targets
mcp__aicc-compute__compute_probe_target
mcp__aicc-compute__compute_stage_job
mcp__aicc-compute__compute_submit_job
mcp__aicc-compute__compute_get_status
mcp__aicc-compute__compute_fetch_artifact
```

同一个 stdio MCP 服务也能注册到 Codex、Claude Code 或其他 MCP 客户端。完整
配置见
[`tools/remote-compute/references/configuration.md`](tools/remote-compute/references/configuration.md)。

### 4. 先做只读验收

开启任务提交前，按顺序完成：

1. 调用 `compute_list_targets`；
2. 用配置中的别名调用 `compute_probe_target`；
3. 调用 `compute_read_cluster_guide`，将指南的大小和 SHA-256 记入来源信息；
4. 使用新的任务 ID 暂存一个无害的小型任务包；
5. 检查暂存清单和远程目录；
6. 确认前面步骤无误后，只为这个目标开启提交，并运行最小调度器任务。

网关不会在失败后改成本地执行。目标不存在、SSH 失败、清单被修改、审批不匹配或
调度器报错都会直接返回错误。

### 5. 为具体任务记录审批

`compute_stage_job` 返回 `manifest_sha256` 后，先取得用户批准，再向项目的
`.research/decisions.jsonl` 追加审批记录：

```json
{"decision_id":"D-HPC-001","task_id":"T004","kind":"approval","decision":"approved","by":"user","approval_type":"expensive_hpc_submission","manifest_sha256":"<暂存返回的准确 SHA-256>","reason":"已检查目标、计算方法和预计成本，同意提交。","created_at":"2026-09-07T12:00:00+08:00"}
```

`compute_submit_job` 会检查决策 ID、任务 ID、审批类型和清单哈希是否完全一致。
已经被替代的审批或不绑定输入文件的通用审批不能提交任务。

取消任务需要另一条 `remote_job_cancellation` 审批，并绑定准确的
`scheduler_job_id`。提交前，网关还会在远端创建防重复标记。即使 SSH 回包中断，
Agent 也不会自动重复提交昂贵任务。

## 核心工作流

```text
论文原稿 + SI + 审稿意见（+ 原始计算文件）
  -> review-response：提取方法指纹，判断哪些意见需要计算
  -> 用户批准计算计划
  -> comp-chem-workflow + 计算引擎 Skills 执行各项计算
  -> 解析、收敛性、来源和科学有效性检查
  -> 生成回复信段落与 SI 表格/图片
  -> 用户批准最终草稿
```

补充计算默认沿用论文的方法指纹。如果必须修改方法，需要说明原因并取得批准。
结果与论文结论冲突时，流程会停止并交还作者判断，不会隐藏冲突，也不会把它包装成
支持性证据。

## 科研编排层

`procedures/research-orchestrator/` 为复杂项目和多 Agent 协作提供机器可读的控制面：

- `.research/project.yaml`：项目元数据、策略、假设和总体状态；
- `.research/tasks/*.yaml`：任务依赖、Skills、必读资料、检查命令、成功标准和输出；
- `.research/artifacts.jsonl`：产物身份、来源、哈希、验证和验收状态；
- `.research/decisions.jsonl`：人工审批与科研决策；
- `.research/events.jsonl`：只追加的工作流与恢复历史；
- `.research/leases/*.json`：昂贵或有状态任务的独占执行权。

流程明确区分以下状态：

```text
completed（执行完成）
  -> validated（验证通过）
  -> accepted（科学验收）
  -> reportable（可写入报告）
```

调度器中的 `COMPLETED` 本身不能通过任何科学验收门。计算引擎解析器和独立审查
必须确认收敛性与问题相关性，报告才能使用该结果。

结构建模也有独立审查边界。表面、缺陷、吸附、slab 和负载团簇任务会分开执行
文献依据检索、结构生成与只读结构审查，然后才允许昂贵的计算任务使用该模型。

无 Agent 远程任务的暂存回执、调度器任务 ID、哈希、审批和结果取回状态见
[`procedures/research-orchestrator/references/remote-execution.md`](procedures/research-orchestrator/references/remote-execution.md)。

## 仓库结构

```text
AGENTS.md                    全局安全规则与任务路由
STRUCTURE.md                 扩展与组织规范
procedures/
  review-response/           论文与审稿意见 -> 经过验证的回复材料
  comp-chem-workflow/        计算生命周期与科学验收门
  literature-to-calculation/ 文献/SI -> 明确的计算目标
  research-orchestrator/     任务 DAG、产物、决策、事件和租约
knowledge/                   与具体软件无关的科研知识
tools/
  structure-prep/            分子与周期结构准备
  vasp/ cp2k/ gaussian/      电子结构与量子化学计算
  gromacs/ lammps/ deepmd/   分子动力学与机器学习势
  phonopy/ catmap/ lobster/  声子、微观动力学与成键分析
  multiwfn/ vaspkit/ ovito/  分析、后处理和可视化
  hpc-submit/                调度脚本、监控和恢复
  remote-compute/            本地 MCP -> 无 Agent 的 SSH/Slurm/PBS 执行
  rsess/                     持久交互式远程 Shell
  report/                    报告与审稿回复材料生成
benchmark/                   审稿意见复现案例与评测结果
```

每个 procedure 和 tool 都遵守 [`STRUCTURE.md`](STRUCTURE.md) 中的组织方式：

- `SKILL.md` 是简短的任务入口和路由说明；
- `references/` 保存详细操作、验证、错误处理和来源规则；
- `examples/` 保存清理过敏感信息的配置或验证案例；
- `scripts/` 保存确定性的预检查和输出解析器。

## 辅助脚本运行环境

需要第三方依赖的辅助脚本推荐使用 [`uv`](https://docs.astral.sh/uv/)。依赖
pymatgen、RDKit 或 OVITO 的脚本会声明自己的依赖，可在隔离且可复用的缓存环境中
运行：

```bash
uv run path/to/script.py ...
```

只使用 Python 标准库的预检查和解析器只需要现代 Python。计算节点不能联网时，
应先在可联网的登录节点构建 `uv` 环境，将 `UV_CACHE_DIR` 放在共享存储，然后使用
`uv run --offline`。如果 PyPI 不可用，或者某个包更适合从 conda-forge 安装，
可以使用准备好的 conda/mamba 环境。

镜像地址、分区、module、软件路径、配额和任务脚本模板都属于站点配置，应写入
远端用户自己的 `~/.cluster-agents.md`，不要提交到本仓库。

## 安全模型

无 Agent 网关采用失败即停止的策略：

- 调用者只能选择预先配置的别名，不能传入任意主机名或用户名；
- OpenSSH 强制使用批处理认证和严格主机密钥检查；
- 上传、下载、科研状态和服务器目录都受白名单约束；
- 任务 ID 和相对路径只允许有限的可移植字符；
- 拒绝符号链接、路径穿越、保留名称和文件覆盖；
- 暂存输入和下载结果都需要通过 SHA-256 校验；
- 提交审批绑定准确的任务清单；
- 每个目标默认关闭提交和取消；
- 远端提交带防重放标记；
- 密码、私钥、真实主机名、模型密钥和授权文件不会写入项目状态或仓库。

网关审计日志是执行证据，不是科研事实的唯一来源。调度器任务 ID、清单哈希、审批、
租约和结果哈希应写回 `.research/`。接受结果前必须运行对应计算引擎的解析器。

生产使用前请阅读完整协议和验收流程：

- [`tools/remote-compute/references/protocol.md`](tools/remote-compute/references/protocol.md)
- [`tools/remote-compute/references/validation.md`](tools/remote-compute/references/validation.md)
- [`tools/remote-compute/references/errors.md`](tools/remote-compute/references/errors.md)

## 当前状态

Skill 结构、本地网关逻辑、MCP 握手与工具发现、Windows 命令处理、配置示例和原有
科研编排流程已经通过离线测试。新的工作站与集群组合仍需完成只读探测和无害任务
验收，才能开启生产提交。

使用 Python 3.11 或更高版本运行本地检查：

```bash
python -m unittest discover -s tools/remote-compute/scripts -p "test_*.py"
python procedures/research-orchestrator/scripts/smoke_tests.py
```

第二条命令需要 PyYAML，也可以在已经提供该依赖的环境中运行。

## 设计原则

1. Skill 保存具体的科研和软件操作知识，不依赖空泛提示词；
2. 任务通过 frontmatter 描述路由，不维护一个硬编码的中央路由器；
3. 确定性检查和解析器优先于临场判断；
4. 昂贵、破坏性或会改变科研结论的操作必须先取得人工批准；
5. 任务、决策、租约和产物状态应持久记录，项目才能恢复、移交和审计；
6. 远程计算接口必须比通用远程 Shell 更窄。

## 参考参数

仓库中的 INCAR 模板、Hubbard U、收敛阈值和力场默认值来自常见文献或社区实践，
只能作为起点。复现论文或执行课题组规范时，应以文献方法或经过批准的组内策略为准。
你可以修改参考文件，保存课题组已经审查过的计算规范。

## 审稿意见复现 Benchmark

`benchmark/` 包含 5 个经过脱敏的 Nature Communications 案例。案例保留了审稿人
提出的计算问题，但隐藏了作者原本的计算回答。仓库同时提供任务提示、评分规则、强制
风险项、Agent 报告、编排协议、设计说明，以及两组独立评测结果。详见
[`benchmark/README.md`](benchmark/README.md)。

## 许可证

本仓库采用 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) 许可。
Benchmark 案例来自采用 CC BY 4.0 的开放获取 Nature Communications 文章，
每个案例都提供 DOI 来源。

## 引用

使用本技能集合或 Benchmark 时，请通过 `CITATION.cff` 引用仓库和配套论文：

> R. Wang, J. Cai & J.-C. Liu. *A harness-neutral skill framework for agentic
> computational chemistry evaluated on peer-review-derived tasks.* Manuscript in
> preparation (2026).
