export default function Card({ children, className = '', hover = false, as: Tag = 'div', ...rest }) {
  return (
    <Tag
      className={[
        'rounded-2xl border border-white/10 dark:border-white/10',
        'bg-[#120e24]/75 dark:bg-[#120e24]/85 backdrop-blur-xl',
        'shadow-[0_4px_24px_rgba(0,0,0,0.25)]',
        hover ? 'transition-all duration-200 hover:border-white/20 hover:shadow-[0_8px_32px_rgba(52,55,160,0.15)] hover:-translate-y-0.5' : '',
        className,
      ].join(' ')}
      {...rest}
    >
      {children}
    </Tag>
  );
}
