import type { ButtonHTMLAttributes, PropsWithChildren } from 'react';

type ButtonVariant = 'primary' | 'secondary';

type Props = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
  }
>;

export const Button = ({ children, variant = 'primary', className = '', ...props }: Props) => {
  return (
    <button {...props} className={`btn btn--${variant} ${className}`.trim()}>
      {children}
    </button>
  );
};
