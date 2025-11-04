import type { CSSProperties } from "react";

const buttonStyle: CSSProperties = {
  width: "2rem",
  height: "2rem",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  borderRadius: "50%",
  border: "1px solid rgba(0,0,0,0.1)",
  background: "#fff",
  cursor: "pointer",
};

const containerStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "0.5rem",
};

export const QuantitySelector = ({
  value,
  onChange,
  min = 0,
  max,
}: {
  value: number;
  onChange: (next: number) => void;
  min?: number;
  max?: number;
}) => {
  const handleChange = (delta: number) => {
    const next = value + delta;
    if (typeof max === "number" && next > max) return;
    if (next < min) return;
    onChange(next);
  };

  return (
    <div style={containerStyle}>
      <button type="button" style={buttonStyle} onClick={() => handleChange(-1)} disabled={value <= min}>
        -
      </button>
      <span>{value}</span>
      <button type="button" style={buttonStyle} onClick={() => handleChange(1)} disabled={typeof max === "number" && value >= max}>
        +
      </button>
    </div>
  );
};
