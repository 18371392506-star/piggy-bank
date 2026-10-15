# -*- coding: utf-8 -*-
"""
🐷 可爱小猪存钱罐 · Cute Piggy Bank
-----------------------------------
一个 Streamlit 小网页：
  * 人民币 ¥ 和 港币 HK$ 分开记账（各自独立，不做任何汇率换算）
  * 可以随时手动修改自己的余额（输入即生效）
  * 存钱 / 取钱都有可爱的动画（金币掉进小猪 + 小猪弹跳 / 小猪抖动吐币）
  * 余额、目标、流水会保存在同目录的 piggy_state.json 里

本地运行：  streamlit run piggy_bank_app.py
"""

from __future__ import annotations

import json
import os
import string
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

# ----------------------------------------------------------------------------
# 基础配置
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="🐷 小猪存钱罐",
    page_icon="🐷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(APP_DIR, "piggy_state.json")

CURRENCIES = {
    "CNY": {
        "name": "人民币",
        "symbol": "¥",
        "flag": "🇨🇳",
        "theme": {
            "body1": "#ffd3e0",
            "body2": "#ff9fbe",
            "ear": "#ff7fa6",
            "snout1": "#ffe3ec",
            "dot": "#e4738f",
            "slot": "#d95f7f",
            "coin1": "#ffe08a",
            "coin2": "#f0aa1e",
            "accent": "#ff5f8f",
        },
        "card": "card-cny",
    },
    "HKD": {
        "name": "港币",
        "symbol": "HK$",
        "flag": "🇭🇰",
        "theme": {
            "body1": "#ded2ff",
            "body2": "#b6a2fb",
            "ear": "#9c83f5",
            "snout1": "#ece5ff",
            "dot": "#7b5ed6",
            "slot": "#6b4bc4",
            "coin1": "#e8f4ff",
            "coin2": "#a8c8e8",
            "accent": "#8b5cf6",
        },
        "card": "card-hkd",
    },
}

MAX_HISTORY = 30


# ----------------------------------------------------------------------------
# 数据存取（用一个小 json 文件持久化；云端写不了也不会报错）
# ----------------------------------------------------------------------------
def _default_state() -> dict:
    return {
        "balances": {"CNY": 0.0, "HKD": 0.0},
        "goals": {"CNY": 0.0, "HKD": 0.0},
        "history": {"CNY": [], "HKD": []},
        "token": 0,
    }


def load_state() -> dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return _default_state()

    state = _default_state()
    try:
        for ccy in CURRENCIES:
            state["balances"][ccy] = float(data.get("balances", {}).get(ccy, 0.0) or 0.0)
            state["goals"][ccy] = float(data.get("goals", {}).get(ccy, 0.0) or 0.0)
            state["history"][ccy] = list(data.get("history", {}).get(ccy, []))[:MAX_HISTORY]
        state["token"] = int(data.get("token", 0) or 0)
    except Exception:
        return _default_state()
    return state


def save_state() -> None:
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.piggy, f, ensure_ascii=False, indent=2)
    except Exception:
        # Streamlit Cloud 等环境可能不可写，忽略即可（本次会话仍然正常）
        pass


if "piggy" not in st.session_state:
    st.session_state.piggy = load_state()
if "flash" not in st.session_state:
    st.session_state.flash = None


def state() -> dict:
    return st.session_state.piggy


def money(symbol: str, value: float) -> str:
    return f"{symbol}{value:,.2f}"


def flash(kind: str, text: str, ccy: str) -> None:
    st.session_state.flash = {"kind": kind, "text": text, "ccy": ccy}


def next_token() -> int:
    s = state()
    s["token"] = int(s.get("token", 0)) + 1
    return s["token"]


def log(ccy: str, action: str, amount: float, balance_after: float) -> None:
    s = state()
    s["history"][ccy].insert(
        0,
        {
            "time": datetime.now().strftime("%m-%d %H:%M"),
            "action": action,
            "amount": round(float(amount), 2),
            "balance": round(float(balance_after), 2),
        },
    )
    del s["history"][ccy][MAX_HISTORY:]


# ----------------------------------------------------------------------------
# 回调函数（Streamlit 的 on_click / on_change 在重跑前执行，动画不会闪掉）
# ----------------------------------------------------------------------------
def _amount_key(ccy: str) -> str:
    return f"amt_{ccy}"


def _manual_key(ccy: str) -> str:
    return f"manual_{ccy}"


def _goal_key(ccy: str) -> str:
    return f"goal_{ccy}"


def handle_action(ccy: str, action: str) -> None:
    st_ = state()
    symbol = CURRENCIES[ccy]["symbol"]
    try:
        amount = round(abs(float(st.session_state.get(_amount_key(ccy), 0.0) or 0.0)), 2)
    except Exception:
        amount = 0.0

    if amount <= 0:
        flash("warn", "先写一个大于 0 的金额，小猪才有力气动起来哦～ 🐽", ccy)
        return

    if action == "deposit":
        st_["balances"][ccy] = round(st_["balances"][ccy] + amount, 2)
        log(ccy, "存入", amount, st_["balances"][ccy])
        flash("ok", f"存入 {money(symbol, amount)}，小猪吃饱啦！🎉", ccy)
    else:
        if amount > st_["balances"][ccy] + 1e-9:
            flash(
                "error",
                f"小猪肚子里只有 {money(symbol, st_['balances'][ccy])}，"
                f"取不出 {money(symbol, amount)} 呀 💦",
                ccy,
            )
            return
        st_["balances"][ccy] = round(st_["balances"][ccy] - amount, 2)
        log(ccy, "取出", amount, st_["balances"][ccy])
        flash("ok", f"取出 {money(symbol, amount)}，记得省着点花～ 💸", ccy)

    st_["anim"] = {
        "ccy": ccy,
        "action": action,
        "amount": amount,
        "token": next_token(),
        "shown": False,
    }
    st.session_state.pop(_manual_key(ccy), None)  # 让输入框同步到新余额
    save_state()


def handle_manual(ccy: str) -> None:
    st_ = state()
    symbol = CURRENCIES[ccy]["symbol"]
    try:
        value = max(0.0, round(float(st.session_state.get(_manual_key(ccy), 0.0) or 0.0), 2))
    except Exception:
        return

    old = st_["balances"][ccy]
    if abs(value - old) < 1e-9:
        return

    st_["balances"][ccy] = value
    delta = value - old
    log(ccy, "手动修改", abs(delta), value)
    st_["anim"] = {
        "ccy": ccy,
        "action": "deposit" if delta > 0 else "withdraw",
        "amount": abs(delta),
        "token": next_token(),
        "shown": False,
    }
    flash("ok", f"余额已更新为 {money(symbol, value)} ✨", ccy)
    save_state()


def handle_goal(ccy: str) -> None:
    try:
        value = max(0.0, round(float(st.session_state.get(_goal_key(ccy), 0.0) or 0.0), 2))
    except Exception:
        return
    state()["goals"][ccy] = value
    flash("ok", "目标已保存 🎯", ccy)
    save_state()


# ----------------------------------------------------------------------------
# 小猪 + 金币动画（放进 iframe，每次动作都会重新播放）
# ----------------------------------------------------------------------------
PIG_TEMPLATE = string.Template(
    """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&display=swap" rel="stylesheet">
<style>
  :root{
    --body1:$body1; --body2:$body2; --ear:$ear; --snout1:$snout1; --dot:$dot;
    --slot:$slot; --coin1:$coin1; --coin2:$coin2; --accent:$accent;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;height:100%;overflow:hidden;background:transparent;
    font-family:'ZCOOL KuaiLe','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;}
  .stage{position:relative;width:100%;height:100%;}

  /* ---------- 小猪 ---------- */
  .pig{position:absolute;bottom:26px;left:50%;width:180px;height:140px;margin-left:-90px;
       transform-origin:50% 100%;}
  .pig.idle{animation:pig-idle 3.4s ease-in-out infinite;}
  .pig.bounce{animation:pig-bounce 1.15s cubic-bezier(.34,1.56,.64,1) .38s both;}
  .pig.shake{animation:pig-shake .95s ease-in-out .1s both;}
  .pig .body{position:absolute;inset:0;border-radius:50% 50% 45% 45%/56% 56% 44% 44%;
    background:radial-gradient(circle at 34% 26%, #fffafc 0%, var(--body1) 36%, var(--body2) 100%);
    box-shadow:inset 0 -16px 0 rgba(255,255,255,.20), inset 0 12px 0 rgba(255,255,255,.30),
               0 16px 26px rgba(196,140,175,.28);}
  .ear{position:absolute;top:-12px;width:46px;height:46px;border-radius:62% 22% 62% 22%;
    background:linear-gradient(140deg,var(--body1),var(--ear));}
  .ear.l{left:12px;transform:rotate(-26deg);}
  .ear.r{right:12px;transform:rotate(26deg) scaleX(-1);}
  .slot{position:absolute;top:6px;left:50%;margin-left:-27px;width:54px;height:11px;border-radius:7px;
    background:var(--slot);box-shadow:inset 0 3px 4px rgba(0,0,0,.35),0 1px 0 rgba(255,255,255,.65);
    z-index:3;}
  .eye{position:absolute;top:36px;width:13px;height:15px;border-radius:50%;background:#4a3b45;
    box-shadow:inset 2px 2px 0 rgba(255,255,255,.9);animation:blink 4.6s infinite;}
  .eye.l{left:40px;} .eye.r{right:40px;}
  .cheek{position:absolute;top:60px;width:24px;height:12px;border-radius:50%;
    background:rgba(255,120,160,.45);filter:blur(1.5px);}
  .cheek.l{left:20px;} .cheek.r{right:20px;}
  .snout{position:absolute;left:50%;margin-left:-34px;top:58px;width:68px;height:50px;border-radius:50%;
    background:linear-gradient(var(--snout1),var(--body1));
    box-shadow:inset 0 -5px 0 rgba(255,255,255,.5);}
  .snout i{position:absolute;top:16px;width:12px;height:16px;border-radius:50%;background:var(--dot);}
  .snout i:first-child{left:14px;} .snout i:last-child{right:14px;}
  .leg{position:absolute;bottom:-13px;width:26px;height:22px;border-radius:0 0 13px 13px;
    background:var(--body2);box-shadow:inset -3px -3px 0 rgba(255,255,255,.28);}
  .leg.l1{left:26px;} .leg.l2{left:62px;} .leg.r1{right:62px;} .leg.r2{right:26px;}
  .tail{position:absolute;right:-13px;top:42px;width:28px;height:28px;border:6px solid var(--ear);
    border-radius:50%;border-left-color:transparent;border-bottom-color:transparent;
    transform:rotate(-15deg);}

  /* ---------- 金币 ---------- */
  .coin{position:absolute;top:0;left:50%;width:38px;height:38px;margin-left:-19px;border-radius:50%;
    background:radial-gradient(circle at 34% 30%, #fffdf2, var(--coin1) 45%, var(--coin2) 100%);
    border:2px solid rgba(255,255,255,.8);color:#8a5a12;display:flex;align-items:center;
    justify-content:center;font-size:16px;font-weight:700;letter-spacing:-1px;
    box-shadow:0 4px 10px rgba(170,130,40,.35);opacity:0;z-index:4;}
  .coin.small{font-size:11px;}
  .coin.in{animation:coin-in 1.05s ease-in forwards;}
  .coin.out{animation:coin-out 1.2s ease-in forwards;}

  /* ---------- 飘字 / 星星 ---------- */
  .float-label{position:absolute;top:4px;left:0;width:100%;text-align:center;font-size:27px;
    font-weight:700;text-shadow:0 2px 0 #fff,0 0 12px rgba(255,255,255,.9);opacity:0;z-index:6;}
  .float-label.plus{color:#ff5f8f;animation:float-up 1.7s ease-out .55s forwards;}
  .float-label.minus{color:#7c5cd6;animation:float-up 1.7s ease-out .35s forwards;}
  .sparkles{position:absolute;top:34px;left:0;width:100%;text-align:center;font-size:26px;
    letter-spacing:12px;opacity:0;z-index:6;animation:pop 1.6s ease-out .62s both;}

  @keyframes coin-in{
    0%{opacity:0;transform:translate(var(--tx,0px),-70px) scale(.7) rotate(0deg);}
    12%{opacity:1;}
    55%{opacity:1;transform:translate(var(--tx,0px),42px) scale(1) rotate(190deg);}
    72%{opacity:1;transform:translate(calc(var(--tx,0px)*.5),102px) scale(.62) rotate(250deg);}
    88%{opacity:1;transform:translate(calc(var(--tx,0px)*.34),110px) scale(.34) rotate(290deg);}
    100%{opacity:0;transform:translate(calc(var(--tx,0px)*.3),112px) scale(.12) rotate(320deg);}
  }
  @keyframes coin-out{
    0%{opacity:0;transform:translate(0px,104px) scale(.4) rotate(0deg);}
    18%{opacity:1;transform:translate(0px,100px) scale(1) rotate(20deg);}
    40%{opacity:1;transform:translate(calc(var(--tx,0px)*.35),72px) scale(1) rotate(90deg);}
    100%{opacity:0;transform:translate(var(--tx,0px),252px) scale(.9) rotate(var(--rot,420deg));}
  }
  @keyframes pig-idle{
    0%,100%{transform:translateY(0) scale(1,1);}
    50%{transform:translateY(-6px) scale(1.012,.99);}
  }
  @keyframes pig-bounce{
    0%{transform:translateY(0) scale(1,1);}
    18%{transform:translateY(9px) scale(1.09,.9);}
    38%{transform:translateY(-17px) scale(.94,1.08);}
    58%{transform:translateY(2px) scale(1.05,.95);}
    76%{transform:translateY(-6px) scale(.99,1.02);}
    100%{transform:translateY(0) scale(1,1);}
  }
  @keyframes pig-shake{
    0%,100%{transform:rotate(0deg) translateY(0);}
    12%{transform:rotate(-5deg) translateY(3px);}
    26%{transform:rotate(5deg) translateY(-3px);}
    40%{transform:rotate(-4deg) translateY(2px);}
    54%{transform:rotate(4deg) translateY(-2px);}
    70%{transform:rotate(-2deg) translateY(1px);}
    86%{transform:rotate(2deg) translateY(0);}
  }
  @keyframes float-up{
    0%{opacity:0;transform:translateY(16px) scale(.85);}
    22%{opacity:1;transform:translateY(0) scale(1.1);}
    70%{opacity:1;transform:translateY(-26px) scale(1);}
    100%{opacity:0;transform:translateY(-60px) scale(.95);}
  }
  @keyframes pop{
    0%{opacity:0;transform:scale(.6);}
    30%{opacity:1;transform:scale(1.12);}
    70%{opacity:1;transform:scale(1);}
    100%{opacity:0;transform:scale(1.25) translateY(-14px);}
  }
  @keyframes blink{0%,92%,100%{transform:scaleY(1);}96%{transform:scaleY(.15);}}
</style>
</head>
<body>
  <div class="stage">
    $coins
    <div class="pig $pig_class">
      <div class="ear l"></div>
      <div class="ear r"></div>
      <div class="tail"></div>
      <div class="body"></div>
      <div class="leg l1"></div>
      <div class="leg l2"></div>
      <div class="leg r1"></div>
      <div class="leg r2"></div>
      <div class="cheek l"></div>
      <div class="cheek r"></div>
      <div class="eye l"></div>
      <div class="eye r"></div>
      <div class="snout"><i></i><i></i></div>
      <div class="slot"></div>
    </div>
    $label
    $sparkles
  </div>
</body>
</html>
"""
)


def pig_html(ccy: str, anim: dict | None = None) -> str:
    info = CURRENCIES[ccy]
    theme = dict(info["theme"])
    symbol = info["symbol"]
    coin_cls = "coin small" if len(symbol) > 1 else "coin"

    coins = ""
    label = ""
    sparkles = ""
    pig_class = "idle"

    if anim:
        tag = symbol
        if anim["action"] == "deposit":
            pig_class = "bounce"
            coins = "".join(
                f'<div class="{coin_cls} in" style="--tx:{-72 + i * 36}px;'
                f'animation-delay:{0.02 + i * 0.13:.2f}s">{tag}</div>'
                for i in range(5)
            )
            label = f'<div class="float-label plus">+{money(symbol, anim["amount"])} 🎉</div>'
            sparkles = '<div class="sparkles">✨💖✨</div>'
        else:
            pig_class = "shake"
            coins = "".join(
                f'<div class="{coin_cls} out" style="--tx:{-120 + i * 60}px;'
                f'--rot:{-380 + i * 190}deg;animation-delay:{0.14 + i * 0.15:.2f}s">{tag}</div>'
                for i in range(5)
            )
            label = f'<div class="float-label minus">-{money(symbol, anim["amount"])} 💸</div>'
            sparkles = '<div class="sparkles">💫💧💫</div>'

    return PIG_TEMPLATE.substitute(
        coins=coins, label=label, sparkles=sparkles, pig_class=pig_class, **theme
    )


# ----------------------------------------------------------------------------
# 页面样式
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&display=swap');

html, body, [class*="css"] {
  font-family: 'ZCOOL KuaiLe', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}
.stApp {
  background:
    radial-gradient(circle at 12% 8%, #ffe8f1 0%, transparent 42%),
    radial-gradient(circle at 88% 12%, #e9f0ff 0%, transparent 40%),
    radial-gradient(circle at 50% 100%, #fff6e8 0%, transparent 45%),
    linear-gradient(160deg, #fffafc 0%, #f7fbff 55%, #fffaf5 100%);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"] { display: none; }
footer { visibility: hidden; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1180px; }

.hero { text-align: center; margin-bottom: 6px; }
.hero .emoji { font-size: 54px; line-height: 1; display:inline-block; animation: hero-bob 2.6s ease-in-out infinite; }
.hero h1 {
  margin: 4px 0 6px 0; font-size: 42px; letter-spacing: 2px;
  background: linear-gradient(92deg, #ff7aa8, #ff9f68 45%, #9a7bff);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { margin: 0; color: #9a8b95; font-size: 15px; }
@keyframes hero-bob { 0%,100%{transform:translateY(0) rotate(-4deg);} 50%{transform:translateY(-9px) rotate(4deg);} }

.balance-card {
  position: relative; border-radius: 26px; padding: 18px 20px 20px 20px; margin-bottom: 6px;
  border: 3px dashed rgba(255,255,255,.9); box-shadow: 0 10px 24px rgba(214,170,196,.22);
  overflow: hidden;
}
.card-cny { background: linear-gradient(140deg,#ffe6ef,#ffd0e2 60%,#ffc4dc); }
.card-hkd { background: linear-gradient(140deg,#ece6ff,#dcd0ff 60%,#cfc0ff); }
.balance-card .ccy { font-size: 17px; color: #7d6672; display:flex; align-items:center; gap:8px; }
.card-hkd .ccy { color: #665a8c; }
.balance-card .tag {
  font-size: 11px; padding: 2px 9px; border-radius: 999px; background: rgba(255,255,255,.75);
  color: #a8849b; letter-spacing: .5px;
}
.card-hkd .tag { color: #7f6bb5; }
.balance-card .num {
  font-size: 46px; font-weight: 700; color: #5c4450; margin: 6px 0 2px 0; line-height: 1.1;
  text-shadow: 0 3px 0 rgba(255,255,255,.85);
}
.card-hkd .num { color: #4c3f78; }
.balance-card .sub { font-size: 12.5px; color: #a08b97; }
.card-hkd .sub { color: #8377ad; }
.balance-card .deco { position:absolute; right:-6px; bottom:-14px; font-size:74px; opacity:.28; }

.flash { border-radius: 18px; padding: 10px 16px; margin: 6px 0 2px 0; font-size: 14.5px; }
.flash.ok { background:#e8fbef; color:#2f8a5b; border:2px dashed #b3ebc9; }
.flash.warn { background:#fff8e3; color:#a97a12; border:2px dashed #ffe0a3; }
.flash.error { background:#ffeef0; color:#c94a5f; border:2px dashed #ffc7ce; }
.flash-slot { height: 6px; }

div.stButton > button {
  width: 100%; border-radius: 999px; border: none; padding: 10px 0; font-size: 16px;
  font-family: inherit; color: #fff; box-shadow: 0 6px 14px rgba(214,150,180,.35);
  transition: transform .12s ease, box-shadow .12s ease;
}
div.stButton > button:hover { transform: translateY(-2px) scale(1.02); box-shadow: 0 10px 20px rgba(214,150,180,.45); }
div.stButton > button:active { transform: scale(.97); }
div.stButton > button[kind="primary"] { background: linear-gradient(120deg,#ff8fb6,#ff6f9c); }
div.stButton > button[kind="secondary"] { background: linear-gradient(120deg,#b9a4ff,#9b7bf0); }

div[data-testid="stNumberInput"] input { border-radius: 14px; font-family: inherit; }
div[data-testid="stNumberInput"] button { font-family: inherit; }
[data-testid="stExpander"] details {
  border-radius: 18px; border: 2px dashed #ffd8e6; background: rgba(255,255,255,.72);
}
[data-testid="stExpander"] summary { font-size: 15px; color: #a3859a; }
.stProgress > div > div > div { background: linear-gradient(90deg,#ffb3cd,#ff8fb6,#9b7bf0); }

.hist { width:100%; border-collapse: collapse; font-size:13px; }
.hist th { color:#a89aa4; font-weight:400; text-align:left; padding:5px 6px; border-bottom:2px dashed #f0dde7; }
.hist td { padding:5px 6px; color:#7d6b76; border-bottom:1px dashed #f6ecf2; }
.hist .in { color:#3f9e6b; } .hist .out { color:#c94a5f; } .hist .set { color:#8b5cf6; }
.empty { color:#c3b4bd; font-size:13px; padding:6px 2px; }
.tip { text-align:center; color:#b6a7b0; font-size:12.5px; margin-top:10px; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
  <div class="emoji">🐷</div>
  <h1>小猪存钱罐</h1>
  <p>人民币 ¥ 和 港币 HK$ 各养一只小猪，分开记账、互不换算 · 余额随时可改</p>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# 主体：两种货币各一栏
# ----------------------------------------------------------------------------
cols = st.columns(2, gap="large")

for col, ccy in zip(cols, ["CNY", "HKD"]):
    info = CURRENCIES[ccy]
    symbol, name, flag = info["symbol"], info["name"], info["flag"]
    balance = state()["balances"][ccy]
    goal = state()["goals"][ccy]

    with col:
        # ---- 余额卡片 ----
        st.markdown(
            f"""
<div class="balance-card {info['card']}">
  <div class="ccy">{flag} {name} <span class="tag">{ccy}</span></div>
  <div class="num">{money(symbol, balance)}</div>
  <div class="sub">独立记账 · 不与另一种货币换算</div>
  <div class="deco">{'🐷' if ccy == 'CNY' else '🐖'}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        # ---- 提示条 ----
        f = st.session_state.flash
        if f and f.get("ccy") == ccy:
            st.markdown(f'<div class="flash {f["kind"]}">{f["text"]}</div>', unsafe_allow_html=True)
            st.session_state.flash = None
        else:
            # 占位，保证左右两只小猪永远在同一高度
            st.markdown('<div class="flash-slot"></div>', unsafe_allow_html=True)

        # ---- 小猪动画 ----
        anim = state().get("anim")
        play = None
        if anim and anim.get("ccy") == ccy and not anim.get("shown"):
            play = anim
            anim["shown"] = True
        components.html(pig_html(ccy, play), height=285 if play else 215, scrolling=False)

        # ---- 存取操作 ----
        st.number_input(
            "金额",
            min_value=0.0,
            step=10.0,
            format="%.2f",
            key=_amount_key(ccy),
            help="先填金额，再点「存入」或「取出」",
        )
        b1, b2 = st.columns(2)
        with b1:
            st.button(
                "🪙 存入",
                key=f"dep_{ccy}",
                type="primary",
                on_click=handle_action,
                args=(ccy, "deposit"),
            )
        with b2:
            st.button(
                "💸 取出",
                key=f"wdr_{ccy}",
                on_click=handle_action,
                args=(ccy, "withdraw"),
            )

        # ---- 手动改余额 + 目标 ----
        with st.expander("✏️ 实时修改我的余额 / 设置储蓄目标"):
            st.number_input(
                "我现在实际有多少（输入即生效）",
                min_value=0.0,
                step=10.0,
                format="%.2f",
                value=float(balance),
                key=_manual_key(ccy),
                on_change=handle_manual,
                args=(ccy,),
            )
            st.number_input(
                "储蓄目标（0 = 不设置）",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                value=float(goal),
                key=_goal_key(ccy),
                on_change=handle_goal,
                args=(ccy,),
            )
            if goal > 0:
                pct = min(1.0, balance / goal) if goal else 0.0
                st.progress(pct, text=f"目标进度 {pct * 100:.1f}%（{money(symbol, balance)} / {money(symbol, goal)}）")

        # ---- 流水 ----
        st.markdown("##### 📒 最近记录")
        rows = state()["history"][ccy]
        if not rows:
            st.markdown('<div class="empty">还没有记录，存一笔试试吧～</div>', unsafe_allow_html=True)
        else:
            body = ""
            for r in rows[:8]:
                cls = {"存入": "in", "取出": "out", "手动修改": "set"}.get(r["action"], "")
                sign = "+" if r["action"] == "存入" else ("-" if r["action"] == "取出" else "±")
                body += (
                    f"<tr><td>{r['time']}</td>"
                    f"<td class=\"{cls}\">{r['action']}</td>"
                    f"<td class=\"{cls}\">{sign}{money('', r['amount'])}</td>"
                    f"<td>{money(symbol, r['balance'])}</td></tr>"
                )
            st.markdown(
                '<table class="hist"><tr><th>时间</th><th>操作</th><th>金额</th><th>余额</th></tr>'
                + body
                + "</table>",
                unsafe_allow_html=True,
            )

st.markdown(
    '<div class="tip">🐽 小提示：两种货币各自独立累计，不做任何汇率转换 · '
    "余额会保存在 piggy_state.json 里（Streamlit 云端重启后可能重置）</div>",
    unsafe_allow_html=True,
)
