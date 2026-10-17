# 英语每日一句 · 微信推送

每天早上 **7:30**，微信收到一句英语：原句、中文翻译、英式音标、朗读要点（连读 / 失爆 / 同化 / 弱读 / 语调），外加一条能点开就听的英音链接。

**跑在 GitHub 的免费服务器上，电脑关着也照推。**

```
GitHub Actions（每天 UTC 23:30 = 北京时间 07:30）
   └─ 按日期选出今天这一句 → 拼好消息 → 调用 Server酱 → 你的微信「服务通知」
```

推送长这样：

```
## 每日一句 · 2026-10-17

**Could you give me a hand with this?**
你能帮我个忙吗？

/kʊdʒuː ˈɡɪv mi ə ˈhænd wɪð ðɪs/

朗读要点
- 【同化】Could you 中 /d/ + /j/ 融合成 /dʒ/，读起来像 "库久"。
- 【弱读】me 在句中弱读作 /mi/，a 弱读作 /ə/。
- 【语调】请求句用降调，句尾 this 收得干脆，别上扬。
- 【重音】重音落在 hand 和 this 上：give me a HAND with THIS。

跟读音频
- 在线英音（点开就能听）：https://fanyi.baidu.com/gettts?lan=uk&...
```

---

## 一、你能拿到什么

| 功能 | 说明 |
| --- | --- |
| 每天固定时间推送 | 北京时间 07:30，GitHub 的定时任务 |
| 24 句轮换 | 按日期算，同一天永远是同一句，跨天自动往后走，一轮完自动循环 |
| 中文翻译 | 每句配一句自然的中文 |
| 英式音标 | 人工校订的 RP 音标（`data/sentences.json` 的 `ipa_uk`） |
| 朗读要点 | 连读、失爆、同化、弱读、省音、重音、语调逐条讲 |
| 英音音频 | 推送里一条在线英音链接，微信内点开就播 |
| 零成本 | GitHub Actions 免费 + Server酱免费 |

---

## 二、先拿到 Server酱 的 SendKey（3 分钟）

1. 手机微信扫一扫，打开 <https://sct.ftqq.com/> 登录；
2. 点左侧 **「SendKey」**；
3. 复制那串 **`SCT...`**（或 `sctp...`）开头的字符串，先存到记事本。

> 免费额度每天 5 条，一天推 1 条完全够。消息会出现在微信的「服务通知」里。

---

## 三、部署到 GitHub（10 分钟，全程网页操作）

> 不需要装 Git，不需要命令行。下面每一步都在浏览器里点。

### 1. 建一个仓库

1. 登录 <https://github.com>（没账号就注册一个，免费）；
2. 右上角 **+** → **New repository**；
3. 名字填 `english-daily`（**建议就用这个名字**，后面默认值都按它写）；
4. 选 **Public**（免费无限额度；选 Private 也行，每月 2000 分钟也够）；
5. 不要勾 "Add a README file"，直接 **Create repository**。

### 2. 上传代码

1. 在新仓库页面点 **「uploading an existing file」**（或 `Add file → Upload files`）；
2. 打开本机的 `english-daily` 文件夹（就是现在这个），**把里面的所有文件/文件夹一起框选，拖进浏览器**；
3. 等文件列表出现后，点下方 **Commit changes**。

> 我已经把不该上传的东西清掉了（虚拟环境、密钥、生成的文件），直接拖就是干净的。
> 如果 `.github` 这个文件夹没被拖上去（浏览器有时会漏掉隐藏文件夹），看 2.1 手动补。

#### 2.1 手动补上 workflow（只有漏了才需要）

仓库页面 `Add file → Create new file`，文件名填：

```
.github/workflows/daily.yml
```

内容粘贴 [`.github/workflows/daily.yml`](.github/workflows/daily.yml) 里的全部文字，然后 Commit。

### 3. 加密钥（Secret）

1. 仓库页面 → **Settings** → 左侧 **Secrets and variables → Actions**；
2. 点 **New repository secret**；
3. Name 填 **`SERVERCHAN_SENDKEY`**（必须一字不差，全大写）；
4. Secret 填你第二步复制的那串 SendKey；
5. **Add secret**。

### 4. 手动跑一次，验证链路

1. 仓库页面 → **Actions** 标签；
2. 如果提示要启用，点 **I understand my workflows, go ahead and enable them**；
3. 左侧点 **daily-english** → 右侧 **Run workflow** → 绿色按钮 **Run workflow**；
4. 等 30 秒左右刷新，看到一个绿勾就成功了；
5. 这时你的微信应该收到今天的句子。

> 收到就说明整条链路通了。之后**什么都不用做**，每天 07:30 自动推。

### 5. 之后就是全自动了

- 每天北京时间 07:30 触发（GitHub 用 UTC，配置里写的是 `30 23 * * *`，已经算好时差）；
- 想立刻重跑：Actions → daily-english → Run workflow；
- 想改时间：改 `.github/workflows/daily.yml` 里的 cron，`23:30 UTC` 换成你要的 UTC 时间（北京时间减 8 小时）。

---

## 四、本地运行（可选）

云端跑起来之后，这一节可以完全跳过。只有想在电脑上调整语料、预览效果时才用得上。

1. PyCharm 打开 `english-daily` 文件夹；
2. `pip install -r requirements.txt`（只有 edge-tts 一个依赖）；
3. `python run.py --open`，会生成 `output/日期/index.html` 并打开，可以听常速/慢速两个 mp3；
4. 想本地也推送，跑 `python setup_push.py` 选渠道、粘密钥。

想本地每天定时（关机就不跑，不如云端省心）：双击 `scripts\install_task.bat`。

---

## 五、命令行用法

```bash
python run.py --by-date        # 云端用法：按日期轮换 + 推送
python run.py                  # 本地用法：按本地状态轮换 + 推送
python run.py --no-push        # 只生成，不推送
python run.py --open           # 生成后打开预览页
python run.py --index 5        # 指定第 5 句（从 1 开始）
python run.py --force          # 今天已推过也强制再推 / 强制换一句
python run.py --no-audio       # 不生成 mp3，只要文字
python run.py --list           # 列出语料库里所有句子
python run.py --test-push      # 只发一条测试消息
python run.py --date 2026-10-17  # 指定日期（方便测试）
```

---

## 六、自己加句子

编辑 `data/sentences.json`，往 `sentences` 数组里加一条：

```json
{
  "id": "s25",
  "text": "That ship has sailed.",
  "zh": "那件事已经错过时机了。",
  "ipa_uk": "/ðæt ʃɪp həz seɪld/",
  "tips": [
    { "type": "连读", "text": "that ship 中 /t/ 遇 /ʃ/ 失去爆破，直接读 ship。" },
    { "type": "弱读", "text": "has 在句中弱读作 /həz/。" }
  ]
}
```

- `tips` 的 `type` 可用：`连读`、`失爆`、`同化`、`弱读`、`省音`、`重音`、`语调`；
- 不写 `ipa_uk` 也能跑，会用本机 `espeak-ng` 或在线词典自动生成，并在页面上标注「仅供参考」；
- 云端部署的话，改完直接在 GitHub 网页上编辑这个文件并 Commit 即可，下次推送就生效。

---

## 七、常见问题

**1. 每天早上没收到**

- Actions 页面看最近一次运行是不是绿的；红了点进去看日志；
- 最常见原因是 Secret 名字写错（必须是 `SERVERCHAN_SENDKEY`）；
- 也确认一下 Server酱 那边有没有关注「服务通知」。

**2. 推送时间不准**

GitHub 的定时任务在整点高峰期可能延迟几分钟到二十分钟，这是它自己的调度排队，不是代码问题。

**3. 过一阵子突然不推了**

GitHub 会在**仓库连续 60 天没有提交**时自动停用定时任务（会发邮件）。到 Actions 页面点一下 **Enable workflow** 就恢复了。

**4. 每天多推了几条**

不会。云端每次是新环境，按日期算，一天一次就是一条；手动 Run workflow 才会多推一条。

**5. 想换渠道（企业微信 / pushplus / WxPusher）**

改 `.github/workflows/daily.yml` 里的两个环境变量：

```yaml
env:
  ENGLISH_DAILY_CHANNEL: wecom          # serverchan / pushplus / wxpusher / wecom
  WECOM_WEBHOOK: ${{ secrets.WECOM_WEBHOOK }}
```

然后去 Settings → Secrets 里加对应的密钥（`PUSHPLUS_TOKEN` / `WXPUSHER_TOKEN` + `WXPUSHER_UID` / `WECOM_WEBHOOK`）。

---

## 八、项目结构

```
english-daily/
├── .github/workflows/daily.yml  # GitHub Actions：每天 07:30 跑一次
├── run.py                       # 入口
├── setup_push.py                # 本地配置推送渠道的向导（云端用不上）
├── requirements.txt
├── config.ini                   # 本地配置（不进仓库）
├── data/
│   ├── sentences.json           # 语料库：句子 / 翻译 / 音标 / 要点
│   └── state.json               # 本地轮换状态（不进仓库）
├── daily_english/
│   ├── clock.py                 # 统一的「今天」（云端按北京时间算）
│   ├── config.py                # 配置：config.ini + 环境变量覆盖
│   ├── corpus.py                # 读语料库
│   ├── phonetics.py             # 音标（人工 / espeak-ng / 在线词典）
│   ├── tips.py                  # 朗读要点
│   ├── audio.py                 # edge-tts 英音 + 在线播放链接
│   ├── render.py                # Markdown / HTML 渲染
│   ├── push.py                  # Server酱 / pushplus / WxPusher / 企业微信
│   └── state.py                 # 轮换（本地按状态，云端按日期）
└── scripts/                     # 本地定时任务相关（云端不需要）
```

---

## 九、几个设计取舍

- **云端不提交、不落库**：Actions 每次都是干净环境，所以轮换改成「按日期算」（`toordinal % 24`），不依赖任何状态文件，也不会往仓库里塞垃圾提交。
- **音标以人工标注为主**：句子级 IPA 自动生成质量不稳定，与其给你一堆错的，不如人工写 24 句；缺句子时才退到自动生成并明确标注。
- **音频用百度翻译的 `lan=uk` 接口**：免注册、国内直连、微信里点开就播。本地仍可用 edge-tts 生成更高质量的常速/慢速 mp3。
- **密钥只放 GitHub Secrets**：`config.ini` 在 `.gitignore` 里，仓库里任何文件都不含你的 SendKey。
- **除 `edge-tts` 外全是标准库**：没有框架依赖，不会因为某个库停更就跑不起来。
