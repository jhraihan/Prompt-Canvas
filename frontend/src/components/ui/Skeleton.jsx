export function Skeleton({ className = "", rounded = "md" }) {
  const radius = {
    md: "rounded-md",
    lg: "rounded-lg",
    xl: "rounded-xl",
    full: "rounded-full",
  }[rounded];

  return (
    <div aria-hidden="true" className={`pc-shimmer bg-inset ${radius} ${className}`} />
  );
}
