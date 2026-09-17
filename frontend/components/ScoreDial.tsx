export default function ScoreDial({ score, label, size = 132 }: { score: number; label: string; size?: number }) {
  const radius = (size - 14) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color = score >= 80 ? "#4f8ff7" : score >= 60 ? "#8d9bf5" : score >= 40 ? "#e0a530" : "#c23f52";

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="#1c212e" strokeWidth={10} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={10}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="middle"
          transform={`rotate(90 ${size / 2} ${size / 2})`}
          className="fill-mist-50 font-display text-[28px] font-medium"
        >
          {Math.round(score)}
        </text>
      </svg>
      <span className="font-mono text-xs uppercase tracking-wider text-mist-300">{label}</span>
    </div>
  );
}
