function Icon({ size = 18, children, ...props }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      {children}
    </svg>
  );
}

export const SparkIcon = (props) => (
  <Icon {...props}>
    <path d="M12 3v4M12 17v4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M3 12h4M17 12h4M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8" />
  </Icon>
);

export const ImageIcon = (props) => (
  <Icon {...props}>
    <rect x="3" y="4" width="18" height="16" rx="2.5" />
    <circle cx="8.5" cy="9.5" r="1.5" />
    <path d="M21 16l-4.5-4.5L7 21" />
  </Icon>
);

export const DownloadIcon = (props) => (
  <Icon {...props}>
    <path d="M12 3v12" />
    <path d="M7.5 10.5L12 15l4.5-4.5" />
    <path d="M4 17v2.5A1.5 1.5 0 005.5 21h13a1.5 1.5 0 001.5-1.5V17" />
  </Icon>
);

export const TrashIcon = (props) => (
  <Icon {...props}>
    <path d="M4 7h16" />
    <path d="M9 7V5a1 1 0 011-1h4a1 1 0 011 1v2" />
    <path d="M6 7l1 12.5A1.5 1.5 0 008.5 21h7a1.5 1.5 0 001.5-1.5L18 7" />
    <path d="M10 11.5v5M14 11.5v5" />
  </Icon>
);

export const RefreshIcon = (props) => (
  <Icon {...props}>
    <path d="M20 11a8 8 0 10-2.2 5.5" />
    <path d="M20 5v6h-6" />
  </Icon>
);

export const CloseIcon = (props) => (
  <Icon {...props}>
    <path d="M6 6l12 12M18 6L6 18" />
  </Icon>
);

export const AlertIcon = (props) => (
  <Icon {...props}>
    <path d="M12 4.5l8.5 15h-17l8.5-15z" />
    <path d="M12 10v4" />
    <circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />
  </Icon>
);

export const CheckIcon = (props) => (
  <Icon {...props}>
    <path d="M5 12.5l4.5 4.5L19 7.5" />
  </Icon>
);

export const InfoIcon = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5" />
    <circle cx="12" cy="8" r="0.6" fill="currentColor" stroke="none" />
  </Icon>
);

export const HistoryIcon = (props) => (
  <Icon {...props}>
    <path d="M3.5 12a8.5 8.5 0 108.5-8.5A8.4 8.4 0 005.6 6.4" />
    <path d="M3.5 3.5V7H7" />
    <path d="M12 7.5V12l3 1.8" />
  </Icon>
);

export const SunIcon = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </Icon>
);

export const MoonIcon = (props) => (
  <Icon {...props}>
    <path d="M20 14.5A8.5 8.5 0 019.5 4a8.5 8.5 0 1010.5 10.5z" />
  </Icon>
);

export const MonitorIcon = (props) => (
  <Icon {...props}>
    <rect x="3" y="4" width="18" height="12" rx="2" />
    <path d="M9 20h6M12 16v4" />
  </Icon>
);

export const ExpandIcon = (props) => (
  <Icon {...props}>
    <path d="M4 9V5.5A1.5 1.5 0 015.5 4H9" />
    <path d="M15 4h3.5A1.5 1.5 0 0120 5.5V9" />
    <path d="M20 15v3.5a1.5 1.5 0 01-1.5 1.5H15" />
    <path d="M9 20H5.5A1.5 1.5 0 014 18.5V15" />
  </Icon>
);

export const LogoutIcon = (props) => (
  <Icon {...props}>
    <path d="M15 4h3a2 2 0 012 2v12a2 2 0 01-2 2h-3" />
    <path d="M10 8l-4 4 4 4" />
    <path d="M6 12h9" />
  </Icon>
);

export const BookmarkIcon = (props) => (
  <Icon {...props}>
    <path d="M6 4.5A1.5 1.5 0 017.5 3h9A1.5 1.5 0 0118 4.5V21l-6-4-6 4V4.5z" />
  </Icon>
);

export const LinkIcon = (props) => (
  <Icon {...props}>
    <path d="M10 13a5 5 0 007.07 0l2.83-2.83a5 5 0 00-7.07-7.07L11.5 4.5" />
    <path d="M14 11a5 5 0 00-7.07 0L4.1 13.83a5 5 0 007.07 7.07L12.5 19.5" />
  </Icon>
);

export const CopyIcon = (props) => (
  <Icon {...props}>
    <rect x="9" y="9" width="12" height="12" rx="2" />
    <path d="M5 15H4a1 1 0 01-1-1V4a1 1 0 011-1h10a1 1 0 011 1v1" />
  </Icon>
);
