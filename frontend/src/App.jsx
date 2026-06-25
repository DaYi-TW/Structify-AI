// Structify AI 前端單頁應用
// 提供 JSON 輸入框、解析模式選擇、結果顯示三個區塊
// 透過 fetch 呼叫後端 POST /api/structure-data，不依賴任何 HTTP 函式庫

import React, { useState } from "react";

// VITE_BACKEND_URL 在 Docker build 時由 build arg 注入
// 本地開發時 Vite 環境未設定此變數，fallback 到 localhost:8000
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

// 預設輸入範例，方便使用者開啟頁面即可直接測試
const defaultInput = JSON.stringify(
  [
    { content: "Waterproof outdoor shoe, cost 25." },
    { content: "Running shoe, cost 20." },
  ],
  null,
  2
);

export default function App() {
  const [input, setInput] = useState(defaultInput);   // 輸入框文字
  const [method, setMethod] = useState("auto");        // 解析模式
  const [output, setOutput] = useState("");            // 結果 JSON 字串
  const [error, setError] = useState("");              // 錯誤訊息
  const [loading, setLoading] = useState(false);       // 按鈕 loading 狀態

  async function handleConvert() {
    try {
      // 每次送出前重置上一次的狀態
      setError("");
      setOutput("");
      setLoading(true);

      // 先在前端驗證 JSON 格式，避免帶著無效資料送到後端
      const rawData = JSON.parse(input);

      const response = await fetch(`${BACKEND_URL}/api/structure-data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method, rawData }),
      });

      const result = await response.json();

      // 後端回傳 success: false 時，將 detail/message 顯示為錯誤訊息
      if (!result.success) {
        throw new Error(result.detail || result.message);
      }

      // 格式化輸出 JSON，縮排 2 空格方便閱讀
      setOutput(JSON.stringify(result.data, null, 2));
    } catch (err) {
      // 統一捕捉 JSON.parse 失敗與 API 錯誤
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1>Structify AI</h1>
        <p style={styles.subtitle}>
          Convert unstructured product text into structured JSON.
        </p>

        {/* 輸入區：使用者貼上 rawData JSON 陣列 */}
        <label style={styles.label}>Input JSON</label>
        <textarea
          style={styles.textarea}
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />

        {/* 解析模式選擇：auto / rule / llm */}
        <label style={styles.label}>Parsing Method</label>
        <select
          style={styles.select}
          value={method}
          onChange={(e) => setMethod(e.target.value)}
        >
          <option value="auto">auto — Rule first, LLM fallback</option>
          <option value="rule">rule — Rule-based Parsing</option>
          <option value="llm">llm — LLM Structured Output</option>
        </select>

        {/* 送出按鈕：loading 時禁用避免重複送出 */}
        <button style={styles.button} onClick={handleConvert} disabled={loading}>
          {loading ? "Processing..." : "Convert to Structured Data"}
        </button>

        {/* 錯誤訊息區：只在有錯誤時顯示 */}
        {error && <div style={styles.error}>Error: {error}</div>}

        {/* 結果顯示區：使用 <pre> 保留 JSON 縮排格式 */}
        <label style={styles.label}>Output JSON</label>
        <pre style={styles.output}>{output || "Result will appear here."}</pre>
      </div>
    </div>
  );
}

// 所有樣式集中在檔案尾端，與元件邏輯分離
const styles = {
  page: {
    minHeight: "100vh",
    background: "#f5f5f5",
    display: "flex",
    justifyContent: "center",
    padding: "40px",
    fontFamily: "Arial, sans-serif",
  },
  card: {
    width: "900px",
    background: "#ffffff",
    borderRadius: "12px",
    padding: "32px",
    boxShadow: "0 8px 24px rgba(0,0,0,0.08)",
  },
  subtitle: { color: "#666", marginBottom: "24px" },
  label: { display: "block", fontWeight: "bold", marginTop: "20px", marginBottom: "8px" },
  textarea: {
    width: "100%",
    height: "200px",
    padding: "12px",
    fontFamily: "monospace",
    fontSize: "14px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    boxSizing: "border-box",
  },
  select: { width: "100%", padding: "10px", border: "1px solid #ddd", borderRadius: "8px" },
  button: {
    marginTop: "20px",
    padding: "12px 20px",
    border: "none",
    borderRadius: "8px",
    background: "#111",
    color: "#fff",
    fontWeight: "bold",
    cursor: "pointer",
  },
  output: {
    background: "#111",
    color: "#0f0",
    padding: "16px",
    borderRadius: "8px",
    minHeight: "160px",
    whiteSpace: "pre-wrap",
  },
  error: {
    marginTop: "16px",
    padding: "12px",
    background: "#ffe8e8",
    color: "#b00020",
    borderRadius: "8px",
  },
};
