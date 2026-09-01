export default function StateBlock({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="state-wrap">
      <div className="state-blob" aria-hidden="true" />
      <div className="state-title">{title}</div>
      {subtitle && <div className="state-sub">{subtitle}</div>}
    </div>
  );
}
