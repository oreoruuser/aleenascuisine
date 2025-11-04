import type { CSSProperties } from "react";

const spinnerStyle: CSSProperties = {
  width: "2.5rem",
  height: "2.5rem",
  border: "3px solid rgba(0,0,0,0.1)",
  borderTopColor: "var(--primary-color, #6b21a8)",
  borderRadius: "50%",
  animation: "spin 1s linear infinite",
  margin: "0 auto",
};

export const Loader = ({ message }: { message?: string }) => (
  <div style={{ textAlign: "center", padding: "2rem" }}>
    <div style={spinnerStyle} />
    {message ? <p style={{ marginTop: "1rem" }}>{message}</p> : null}
  </div>
);
