import { useRef, useState } from "react";

interface Props {
  onAnalyze: (file: File) => void;
  disabled: boolean;
}

// Drag-and-drop + file-picker upload area.
export default function UploadPanel({ onAnalyze, disabled }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  }

  function handleSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0];
    if (picked) setFile(picked);
  }

  return (
    <div
      className={`upload-panel${dragging ? " dragging" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <p style={{ margin: "0 0 12px", color: "#444" }}>
        Drag a <code>.json</code> or <code>.csv</code> log file here, or
      </p>
      <label htmlFor="logfile">Choose file</label>
      <input
        id="logfile"
        ref={inputRef}
        type="file"
        accept=".json,.csv"
        onChange={handleSelect}
      />
      <button
        className="btn"
        disabled={!file || disabled}
        onClick={() => file && onAnalyze(file)}
      >
        Analyze
      </button>
      {file && <div className="filename">Selected: {file.name}</div>}
    </div>
  );
}
