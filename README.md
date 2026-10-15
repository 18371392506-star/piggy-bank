# 🐷 小猪存钱罐 Cute Piggy Bank

一个可爱风格的 Streamlit 存钱罐网页：

![预览](preview.png)


- 💴 **人民币 ¥** 和 **港币 HK$** 各一只小猪，**分开记账，互不换算**
- ✏️ 余额可以**实时手动修改**（输入框里改，回车立刻生效）
- 🪙 **存钱动画**：金币从天而降掉进小猪的投币口，小猪开心弹跳 + 飘出 `+¥xx`
- 💸 **取钱动画**：小猪抖动，金币从投币口蹦出来掉到地上 + 飘出 `-¥xx`
- 🎯 可选储蓄目标 + 进度条
- 📒 每个币种各自的最近流水记录

## 一、文件说明

| 文件 | 作用 |
| --- | --- |
| `piggy_bank_app.py` | 主程序（整个网页都在这里） |
| `requirements.txt` | 依赖包（只有 streamlit） |
| `README.md` | 本说明 |
| `preview.png` | 页面预览图（README 里显示用，可传可不传） |
| `piggy_state.json` | 运行时自动生成的余额存档（**不用上传到 GitHub**） |

## 二、本地先试一下（可选）

```bash
pip install -r requirements.txt
streamlit run piggy_bank_app.py
```

浏览器会自动打开 http://localhost:8501

## 三、上传到 GitHub

1. 打开 https://github.com/new ，新建一个仓库（Repository name 随便取，例如 `piggy-bank`），
   选 **Public**，点 **Create repository**。
2. 在新仓库页面点 **uploading an existing file**（或 `Add file` → `Upload files`）。
3. 把这个文件夹里的 **`piggy_bank_app.py`、`requirements.txt`、`README.md`** 三个文件
   拖进去（`preview.png` 想一起传也可以；`piggy_state.json` 千万不要传），点 **Commit changes**。

> 命令行方式也行：
> ```bash
> cd 这个文件夹
> git init
> git add piggy_bank_app.py requirements.txt README.md preview.png .gitignore
> git commit -m "cute piggy bank"
> git branch -M main
> git remote add origin https://github.com/你的用户名/piggy-bank.git
> git push -u origin main
> ```

## 四、部署到 Streamlit Cloud

1. 打开 https://share.streamlit.io ，用 **GitHub 账号登录**（第一次会让你授权，点同意）。
2. 点 **Create app** → **Deploy a public app from GitHub**。
3. 填：
   - **Repository**：`你的用户名/piggy-bank`
   - **Branch**：`main`
   - **Main file path**：`piggy_bank_app.py`
4. 点 **Deploy!**，等 1～2 分钟，就会得到一个网址：
   `https://xxxxxxxx.streamlit.app` —— 这个就是你要的「小猪存钱罐网址」，手机也能打开。

之后每次在 GitHub 改代码，Streamlit 会自动重新部署。

## 五、注意事项

- **关于存钱数据**：余额写在 `piggy_state.json` 里，本地运行时能长期保存；
  在 Streamlit 云端，应用重启（长时间没人访问 / 重新部署）后文件会被还原，余额可能回到 0。
  想永久保存可以后续换成 Google Sheets 或 Supabase 之类的云存储。
- **两种货币完全独立**：页面上不会做任何汇率换算，¥ 和 HK$ 各记各的。
- **想换颜色**：打开 `piggy_bank_app.py`，最上面的 `CURRENCIES` 里改 `theme` 的颜色值即可。
- **想改字**：小猪的文案、提示语都在 `piggy_bank_app.py` 里直接搜中文就能找到。
