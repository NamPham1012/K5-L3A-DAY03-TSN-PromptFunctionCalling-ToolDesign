"""Streamlit UI cho Research Agent.

Chạy:  streamlit run app.py
Tái dùng vòng lặp multi-round + ghi transcript từ chat.py, nên mỗi phiên chat
trên UI cũng tự lưu transcripts/*.transcript.json (phục vụ deliverable chat live).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import (
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="centered")

PROVIDER_MODELS = {
    "groq": ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"],
    "openrouter": [
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
    ],
    "ollama": ["qwen2.5:7b", "llama3.2:3b"],
}
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4


# ---------- Khởi tạo một lần cho mỗi phiên ----------
@st.cache_resource
def load_agent_config(provider_name: str, model: str, version: str) -> dict[str, Any]:
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    tool_decls = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    openai_tools = to_openai_tools(tool_decls)
    provider = make_provider(provider_name)
    artifact_version = build_artifact_version(
        version, ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml"
    )
    return {
        "system_prompt": system_prompt,
        "tools": openai_tools,
        "provider": provider,
        "artifact_version": artifact_version,
    }


def new_transcript(version: str, provider_name: str, model: str) -> dict[str, Any]:
    ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    tid = "_".join([safe_slug(version), safe_slug(provider_name), ts])
    cfg = load_agent_config(provider_name, model, version)
    return {
        "transcript_id": tid,
        **artifact_version_dict(cfg["artifact_version"]),
        "provider": provider_name,
        "model": model,
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Cấu hình")
    provider_name = st.selectbox("Provider", list(PROVIDER_MODELS.keys()), index=0)
    model = st.selectbox("Model", PROVIDER_MODELS[provider_name], index=0)
    version = st.text_input("Version label", value="v7")
    if st.button("🔄 Hội thoại mới"):
        st.session_state.pop("messages", None)
        st.session_state.pop("history", None)
        st.session_state.pop("transcript", None)
        st.rerun()
    st.caption("Mỗi phiên chat tự lưu vào `transcripts/`.")

# ---------- State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []   # hiển thị trên UI
if "history" not in st.session_state:
    st.session_state.history = []     # ngữ cảnh gửi cho model
if "transcript" not in st.session_state:
    st.session_state.transcript = new_transcript(version, provider_name, model)

st.title("🔎 Research Agent")
st.caption("Tìm tin theo tài khoản/chủ đề · đọc URL · Wikipedia · arXiv · policy · gửi Telegram (cần xác nhận)")

# ---------- Hiển thị lịch sử ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        for ev in m.get("tool_events", []):
            with st.expander(f"🔧 {ev.get('tool')}  ·  args: {ev.get('args')}"):
                st.json(ev.get("result"))

# ---------- Nhập ----------
prompt = st.chat_input("Nhập yêu cầu, ví dụ: Tweet mới nhất của Sam Altman là gì?")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    cfg = load_agent_config(provider_name, model, version)
    messages = [
        {"role": "system", "content": cfg["system_prompt"]},
        *trim_history(st.session_state.history, HISTORY_WINDOW),
        {"role": "user", "content": prompt},
    ]

    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy nghĩ..."):
            turn: dict[str, Any] = {
                "turn_index": len(st.session_state.transcript["turns"]) + 1,
                "started_at": now_iso(),
                "user": prompt,
            }
            try:
                result = run_model_tool_loop(
                    provider=cfg["provider"],
                    messages=messages,
                    tools=cfg["tools"],
                    model=model,
                    max_tool_rounds=MAX_TOOL_ROUNDS,
                )
                answer = result["assistant_text"]
                tool_events = result.get("tool_events", [])
                turn.update(result)
                st.markdown(answer)
                for ev in tool_events:
                    with st.expander(f"🔧 {ev.get('tool')}  ·  args: {ev.get('args')}"):
                        st.json(ev.get("result"))
                st.session_state.history.append({"role": "user", "content": prompt})
                st.session_state.history.append({"role": "assistant", "content": answer})
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "tool_events": tool_events}
                )
            except Exception as exc:
                err = f"{type(exc).__name__}: {exc}"
                turn.update({"status": "provider_error", "error": err})
                st.error(f"Lỗi provider (vd rate limit 429 / tool_choice): {err}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"⚠️ {err}"}
                )

            turn["ended_at"] = now_iso()
            st.session_state.transcript["turns"].append(turn)
            write_transcript(
                ROOT / "transcripts" / f"{st.session_state.transcript['transcript_id']}.transcript.json",
                st.session_state.transcript,
            )
