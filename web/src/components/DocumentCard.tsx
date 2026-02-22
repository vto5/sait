type Props = {
  title: string;
  fileUrl: string;
};

export const DocumentCard = ({ title, fileUrl }: Props) => (
  <article className="card card--document">
    <h3>{title}</h3>
    <a href={fileUrl} target="_blank" rel="noreferrer">
      Открыть PDF
    </a>
  </article>
);
