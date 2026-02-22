type Props = {
  title: string;
  result: string;
};

export const CaseCard = ({ title, result }: Props) => (
  <article className="card card--case">
    <h3>{title}</h3>
    <p>{result}</p>
  </article>
);
