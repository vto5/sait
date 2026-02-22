import type { PropsWithChildren } from 'react';

type Props = PropsWithChildren<{
  id?: string;
  title: string;
  subtitle?: string;
}>;

export const Section = ({ id, title, subtitle, children }: Props) => (
  <section id={id} className="section container">
    <header className="section__header">
      <h2>{title}</h2>
      {subtitle ? <p>{subtitle}</p> : null}
    </header>
    {children}
  </section>
);
