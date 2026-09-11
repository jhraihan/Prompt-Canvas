import { controlBorder, controlClasses } from "./Field";

export function TextInput({ invalid = false, className = "", ...props }) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={[controlClasses, controlBorder(invalid), "h-10", className].join(" ")}
      {...props}
    />
  );
}
