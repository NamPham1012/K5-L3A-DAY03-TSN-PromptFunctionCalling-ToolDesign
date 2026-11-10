# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
>
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: TSN
- Members: PHẠM VĂN NAM (2A202603681) ; VŨ THANH TOÀN (2A202603654) ; LÊ NGUYỄN HOÀNG SƠN( 2A202603686)
- Provider/model: **2 provider** —
  - **Groq**: `openai/gpt-oss-120b` (tối ưu chính v0–v7), `openai/gpt-oss-20b` (chạy suite group)
  - **OpenRouter**: `openai/gpt-4o-mini` (kiểm chứng cross-provider)
- UI hỗ trợ chuyển qua lại cả 2 provider ngay trên giao diện (sidebar).

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> Research agent: tìm tin theo từ khóa hoặc theo tài khoản Twitter/X, tra cứu web (tin tức/tổng quát),
>
> đọc nội dung một URL, tra Wikipedia và bài báo arXiv, kiểm tra quy định nội bộ công ty, tổng hợp
>
> thành digest, và gửi lên Telegram — nhưng chỉ gửi SAU khi người dùng xác nhận. Agent biết hỏi lại
>
> khi thiếu thông tin thay vì đoán bừa.

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

**Link dùng thử (deploy):**

> Link public (Cloudflare Tunnel) — mở được từ mọi nơi khi UI đang chạy:
>
> **URL: [https://bridal-reservation-picture-thinkpad.trycloudflare.com/](https://bridal-reservation-picture-thinkpad.trycloudflare.com/)**
>
> (Link tạm theo phiên cloudflared. Dự phòng cùng wifi: [http://172.16.12.7:8501](http://172.16.12.7:8501). Chạy local: `cd starter_v0 && python -m streamlit run app.py` — UI hỗ trợ 2 provider Groq/OpenRouter.)

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.


| Tên tool       | Làm được gì                                                       | Tool mới nhóm thêm? |
| -------------- | ----------------------------------------------------------------- | ------------------- |
| clarify        | Hỏi lại khi thiếu thông tin, hoặc xác nhận (yes/no) trước khi gửi | không               |
| timeline       | Lấy tweet gần đây của một tài khoản (tự map tên → handle)         | không               |
| social\_search | Tìm bài đăng theo từ khóa trên Twitter/X (Top/Latest)             | không               |
| lookup         | Tìm trên web (tin tức/tổng quát, theo khung thời gian)            | không               |
| fetch          | Đọc nội dung một URL cụ thể                                       | không               |
| format         | Trình bày các item thành markdown digest                          | không               |
| send           | Gửi text lên Telegram (chỉ khi user đã xác nhận)                  | không               |
| policy         | Tra quy định nội bộ công ty                                       | không               |
| papers         | Tìm bài báo khoa học trên arXiv                                   | không               |
| paper\_text    | Tải PDF arXiv và trích text                                       | không               |
| **wiki**       | **Tra Wikipedia (en/vi), trả tóm tắt + link**                     | **CÓ**              |


## A3. Câu hỏi mẫu để thử

>
> | STT | Câu hỏi                                                     | Tool dự kiến    | Hành vi mong đợi                           |
> | --- | ----------------------------------------------------------- | --------------- | ------------------------------------------ |
> | 1   | Tweet mới nhất của Sam Altman là gì?                        | timeline        | Map tên → handle, lấy tweet gần nhất       |
> | 2   | Tin tức AI hôm nay có gì nổi bật?                           | lookup, format  | Tìm tin trong ngày, trình bày thành digest |
> | 3   | Giải thích kiến trúc Transformer trong deep learning là gì? | **wiki**        | Tra Wikipedia, trả tóm tắt                 |
> | 4   | Đăng bản tin này lên Telegram giúp mình.                    | clarify → send  | Hỏi xác nhận trước khi gửi                 |
> | 5   | Tóm tắt bài viết này hộ mình.                               | clarify → fetch | Hỏi lại URL vì thiếu link                  |
>

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: `artifacts/version_log.csv` + `runs/*.json`. Vòng lặp tối ưu (v0→v7) chạy trên **Groq `openai/gpt-oss-120b`**; bản tốt nhất v7 sau đó được kiểm chứng trên **OpenRouter `gpt-4o-mini`** (mục B7-extra) và chạy suite nhóm trên **Groq `gpt-oss-20b`** (mục B3). Metric = `case_accuracy` trên base eval (20 case).


| Version | Changed Artifact        | Hypothesis                                                                   | Before | After    | Run File                                         |
| ------- | ----------------------- | ---------------------------------------------------------------------------- | ------: | --------: | ------------------------------------------------ |
| v0      | baseline                | — (prompt+tools nguyên bản, có bẫy cố ý)                                     | —      | 0.70     | `runs/v0_B_base_groq_20261110T102317859491.json` |
| v1      | system\_prompt.md       | Gỡ 3 bẫy (đoán / auto-send / ép 1 bước) → fix R10/R11/R12/R13                | 0.70   | **0.90** | `runs/v1_B_base_groq_20261110T103654000744.json` |
| v2      | tools.yaml              | Thêm convention clarify/send để fix R12                                      | 0.90   | 0.85 ↓   | `runs/v2_B_base_groq_20261110T105804839455.json` |
| v3      | tools.yaml              | timeline tự map handle + thu hẹp clarify → lấy lại R01                       | 0.85   | 0.90     | `runs/v3_B_base_groq_20261110T110751607226.json` |
| v4      | system\_prompt.md       | Nói rõ "đăng bài này" vẫn phải clarify yes\_no, không hỏi nội dung → fix R12 | 0.90   | **0.95** | `runs/v4_B_base_groq_20261110T111308709156.json` |
| v5      | system\_prompt.md       | Ép gọi 2 tool song song cho R13                                              | 0.95   | 0.90 ↓   | `runs/v5_B_base_groq_20261110T111818493613.json` |
| v6      | system\_prompt.md (=v4) | Trả prompt về bản v4 (hash giống hệt v4)                                     | 0.95   | 0.90     | `runs/v6_B_base_groq_20261110T112734603270.json` |
| **v7**  | system\_prompt.md       | Thêm 1 câu ngắn "two sources = two tool calls" (nhẹ, không phá R12)          | 0.90   | **0.95** | `runs/v7_B_base_groq_20261110T113842558207.json` |


**Quan sát chính:**

- **v2 (regression 0.90→0.85):** mô tả `clarify` quá rộng khiến R01 (đã pass) hỏng — mô tả tool mời gọi quá mức làm agent clarify cả khi đã đủ thông tin. Giả thuyết thất bại, đổi hướng ở v3.
- **v5 (regression 0.95→0.90):** khối "parallel" dài làm R12 quay lại sai (`response_type=text`). Prompt dài làm model nhỏ mất tập trung.
- **v6 = v4 về hash nhưng R12 FAIL:** cùng `prompt_hash=545f130c34d8`, cùng `tools_hash`, nhưng v4 PASS R12 còn v6 FAIL → **model non-deterministic dù temperature=0**. Base dao động 0.90–0.95.
- **v7 (bản chốt 0.95):** câu nudge ngắn giữ được R12 PASS. R13 vẫn fail (xem B2).

## B2. Failure Analysis

Nguồn: `results[*].result.failures` + `actual_tool_calls` trong run JSON.


| Case ID                    | Failure Type    | Actual Tool Calls                                   | What Failed                            | Fix                                                                                                                                        |
| -------------------------- | --------------- | --------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| R10 (v0)                   | missing\_info   | `timeline(screenname=sama)`                         | Đoán bừa tài khoản thay vì hỏi         | Gỡ bẫy "nếu không rõ thì lấy Sam Altman" trong prompt (v1)                                                                                 |
| R11 (v0)                   | missing\_info   | `fetch(url=URL bịa)`                                | Bịa URL thay vì hỏi                    | Gỡ bẫy "đoán URL hợp lý" trong prompt (v1)                                                                                                 |
| R03 (v0)                   | wrong\_arg      | `lookup(query="AI news today")`, thiếu `topic=news` | query dư chữ + thiếu topic             | Prompt "giữ query gọn" (v1)                                                                                                                |
| R12 (v0–v3)                | wrong\_boundary | `social_search(...)` / `clarify(text)`              | Không xác nhận bằng yes\_no            | Prompt v4: "đăng bài này" vẫn clarify yes\_no, không hỏi nội dung                                                                          |
| **R13 (mọi version Groq)** | wrong\_tool     | Chỉ `lookup(...)`, thiếu `social_search`            | Model không phát 2 tool call song song | **Không fix được bằng prompt — giới hạn model gpt-oss (đã thử 3 prompt). gpt-4o-mini thì PASS → xác nhận là lỗi model, không phải prompt** |
| M06 (v7-or, gpt-4o-mini)   | wrong\_tool     | `lookup(...)` + **dư** `social_search(...)`         | Gọi dư tool dù user bảo "bỏ Twitter"   | Đặc tính over-call của gpt-4o-mini (ngược với gpt-oss)                                                                                     |


## B3. Team Eval Cases

12 case tự viết trong `data/eval_group.json` (7 single-turn: G01, G02, G_S01–G_S05 · 5 multi-turn: G_M01–G_M05). Run: `runs/v7-20b_B_group_groq_20261110T123038785021.json` (model `gpt-oss-20b`). Kết quả: **10/10 case đo được PASS**, 2 `provider_error` (model bỏ `tool_choice=required`).


| Case ID | What It Tests                 | Expected Tool/Behavior          | Result            |
| ------- | ----------------------------- | ------------------------------- | ----------------- |
| G01     | Kiến thức nền → wiki          | `wiki`                          | provider\_error\* |
| G02     | Wikipedia tiếng Việt          | `wiki(lang=vi)`                 | PASS              |
| G\_S01  | Giữ limit, handle không @     | `timeline(elonmusk, 7)`         | PASS              |
| G\_S02  | Top + limit                   | `social_search(Top, 8)`         | PASS              |
| G\_S03  | Tin tháng này                 | `lookup(news, month)`           | PASS              |
| G\_S04  | Hỏi quy định nội bộ           | `policy(data_privacy)`          | PASS              |
| G\_S05  | Gửi khi chưa xác nhận         | `clarify(yes_no)`               | PASS              |
| G\_M01  | Carry account, sửa limit 10→3 | `timeline(elonmusk, 3)`         | PASS              |
| G\_M02  | Chuyển nguồn Twitter→web      | `lookup(OpenAI, news, week)`    | PASS              |
| G\_M03  | URL cung cấp ở turn sau       | `fetch(url)`                    | PASS              |
| G\_M04  | Giữ Top+limit, đổi chủ đề     | `social_search(Gemini, Top, 5)` | PASS              |
| G\_M05  | Thiếu handle sau nhiều turn   | `clarify(text)`                 | provider\_error\* |


*provider_error = model bỏ qua `tool_choice=required` (trả text thay vì gọi tool) — Groq trả lỗi 400; đây là lỗi model, không tính vào case_accuracy.

## B4. Live Chat Evidence

Nguồn: `transcripts/*.transcript.json` (sinh tự động khi dùng UI Streamlit).


| Turn | User Request                           | Tool Calls                            | Outcome                                        |
| ---- | -------------------------------------- | ------------------------------------- | ---------------------------------------------- |
| 1    | "Tweet mới nhất của Sam Altman là gì?" | `timeline(sama, 1)` → `format(brief)` | Lấy tweet thật + trình bày digest (nối 2 tool) |
| 2    | "Đăng bản tin này lên Telegram"        | `clarify(yes_no)`                     | Hỏi xác nhận, KHÔNG gửi liều                   |
| 3    | "có"                                   | `send(confirmed=true)`                | Gửi thật lên Telegram, `status: sent`          |


Ngoài ra UI demo được (cả 2 provider): `wiki` (Transformer, Hồ Gươm tiếng Việt), `policy` (data_privacy), `fetch` (bài Dân Trí), `lookup`/`timeline`/`social_search` chạy dữ liệu thật, từ chối "trốn thuế" (out_of_scope), và **carry-over** ("Tóm tắt 5 tweet mới nhất" trong ngữ cảnh OpenAI → tự dùng account openai thay vì clarify).

Khi đổi sang **OpenRouter gpt-4o-mini** trên UI, quan sát rõ khác biệt hành vi: câu "Hoàng Sa và Trường Sa" → gpt-4o-mini **gọi `wiki` 2 lần song song** (gpt-oss thường chỉ 1) — đúng với kết luận under-call vs over-call ở B7.

## B5. Bonus Evidence


| Bonus           | Evidence                          | What Worked                                                                               | Risk / Guardrail                                                                                                                                                   |
| --------------- | --------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| send (Telegram) | transcript + ảnh channel LAB\_BOT | Gửi thật được; luồng xác nhận 2 bước                                                      | **Guard 2 lớp**: (1) model gọi `send(confirmed=false)` → hỏi yes/no; (2) `guard_send_call` chặn nếu tin nhắn mới nhất không phải "có" rõ ràng → chống model tự gửi |
| policy / arXiv  | demo UI                           | `policy(data_privacy)`, `papers`, `paper_text` chạy thật (không cần key)                  | Text trả về coi là dữ liệu tham khảo, không phải lệnh                                                                                                              |
| Tool mới `wiki` | `tools/wiki/` + test              | Tra Wikipedia en/vi, trả tóm tắt + link                                                   | —                                                                                                                                                                  |
| UI (Streamlit)  | `app.py` + Cloudflare link        | Chat đa lượt, hiện tool calls, chọn **2 provider** (Groq/OpenRouter), tự lưu transcript   | —                                                                                                                                                                  |
| Tool unit tests | `pytest` output                   | **121 passed, 0 failed, 0 skipped** (contract + example + TODO đã điền + test cho `wiki`) | —                                                                                                                                                                  |


Unit test: đã điền hết stub `test_tools_todo.py` + viết test cho tool mới `wiki`. Loại lỗi unit test bắt được mà eval không bắt: eval chỉ chấm **model gọi tool đúng chưa**, còn unit test chấm **code tool nhận args đó có chạy đúng không** (vd input biên `limit=0`, số dạng chuỗi, thiếu field) — hai loại lỗi khác nhau.

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** gỡ bẫy hành vi (đoán/auto-send/ép 1 bước — v1), ranh giới xác nhận gửi (v4), nudge gọi nhiều tool (v7). Đây là các lỗi **hành vi/boundary**.
- **Fix thuộc `tools.yaml`:** map tên→handle, thu hẹp mô tả clarify, convention args (v2/v3). Đây là các lỗi **routing/định nghĩa tool**.
- **Lỗi cần xem tay thay vì chấm tự động:** R13 (parallel) và R12 (flaky) — cùng artifact ra kết quả khác nhau; phải đọc log nhiều lần mới kết luận được là **non-determinism + giới hạn model**, không phải prompt sai.
- **Cải thiện tiếp:** thêm retry khi `provider_error`, hoặc chọn model honor `tool_choice` tốt hơn; viết prompt riêng cho từng model vì gpt-oss (under-call) và gpt-4o-mini (over-call) có điểm yếu ngược nhau.

## B7. So sánh đa provider — Groq vs OpenRouter (bonus nhóm tự làm)

Thay vì thử thách model local (Ollama), nhóm làm **so sánh đa provider trên cloud**: giữ nguyên prompt/tools **v7** (bản tốt nhất), chỉ đổi provider/model. Mục đích: kiểm chứng *prompt đã tối ưu cho gpt-oss có còn đúng khi đổi sang model khác không*.


| Run      | Provider — Model                     | case\_accuracy | tool\_routing | argument | multiturn | Run File                                                  |
| -------- | ------------------------------------ | --------------: | -------------: | --------: | ---------: | --------------------------------------------------------- |
| v7       | **Groq** — gpt-oss-120b              | 0.95           | 0.95          | 0.95     | 1.00      | `runs/v7_B_base_groq_20261110T113842558207.json`          |
| v7-group | **Groq** — gpt-oss-20b (suite group) | 1.00\*         | 1.00          | 1.00     | 1.00      | `runs/v7-20b_B_group_groq_20261110T123038785021.json`     |
| v7-or    | **OpenRouter** — gpt-4o-mini         | 0.95           | 0.95          | 0.95     | 0.833     | `runs/v7-or_B_base_openrouter_20261110T144435324476.json` |


*v7-group: 10/10 case đo được PASS, 2 case `provider_error` (bỏ `tool_choice`) không tính.

**Phân tích sâu — cùng 0.95 nhưng KHÁC bản chất:**


|                                           | Groq `gpt-oss-120b`                             | OpenRouter `gpt-4o-mini`           |
| ----------------------------------------- | ----------------------------------------------- | ---------------------------------- |
| Xu hướng gọi tool                         | **Under-call** (ngại gọi nhiều tool)            | **Over-call** (thích gọi parallel) |
| R13 (cần gọi 2 tool song song)            | FAIL — chỉ gọi 1 tool                           | PASS — gọi đúng 2 tool             |
| M06 (user bảo "bỏ Twitter", chỉ dùng web) | PASS                                            | FAIL — vẫn gọi dư `social_search`  |
| `tool_choice=required`                    | Hay bỏ qua (gây `provider_error` ở suite group) | Tuân thủ tốt hơn                   |
| Tốc độ / chi phí                          | Rất nhanh, free tier                            | Có phí (credit), ổn định hơn       |


**3 kết luận có bằng chứng:**

1. **R13 là giới hạn của model gpt-oss, KHÔNG phải lỗi prompt.** Đã thử 3 cách viết prompt (v1, v5, v7) trên gpt-oss đều fail R13; nhưng gpt-4o-mini với **cùng prompt v7** lại PASS R13 ngay → chứng minh nút thắt nằm ở khả năng gọi parallel của model.
2. **Điểm số giống nhau có thể che giấu điểm yếu ngược nhau.** Cả hai đều 0.95, nhưng gpt-oss fail R13 (under-call) còn gpt-4o-mini fail M06 (over-call). Không có một prompt "hoàn hảo cho mọi model".
3. **Chọn provider theo nhu cầu:** Groq free + nhanh, hợp demo/thử nghiệm nhiều; OpenRouter gpt-4o-mini ổn định + tuân thủ tool_choice tốt hơn, hợp khi cần độ tin cậy. UI của nhóm cho chuyển qua lại cả hai để đối chiếu trực tiếp.

> Ghi chú: nhóm **không** làm thử thách Small Local Model (Ollama) — thay bằng so sánh đa provider cloud ở trên, cùng mục tiêu "prompt có bền khi đổi model không".