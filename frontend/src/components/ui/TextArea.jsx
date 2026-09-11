import { controlBorder, controlClasses } from "./Field";

export function TextArea({ invalid = false, className = "", ...props }) {
  return (
    <textarea
      aria-invalid={invalid || undefined}
      className={[
        controlClasses,
        controlBorder(invalid),
        "min-h-32 resize-y py-2.5 leading-relaxed",
        className,
      ].join(" ")}
      {...props}
    />
  );
}
