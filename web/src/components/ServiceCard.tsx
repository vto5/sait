import type { ServiceItem } from '../content/services';

export const ServiceCard = ({ title, description }: ServiceItem) => (
  <article className="card">
    <h3>{title}</h3>
    <p>{description}</p>
  </article>
);
