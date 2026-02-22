import { Link, useParams } from 'react-router-dom';
import { blogPosts } from '../content/blog';

export const BlogPostPage = () => {
  const { slug } = useParams();
  const post = blogPosts.find((item) => item.slug === slug);

  if (!post) {
    return (
      <main className="container section">
        <h1>Статья не найдена</h1>
        <Link to="/blog">Вернуться в блог</Link>
      </main>
    );
  }

  return (
    <main className="container section article">
      <Link to="/blog">← К списку статей</Link>
      <h1>{post.title}</h1>
      <h2>Введение</h2>
      <p>{post.content}</p>
      <h3>Что добавить дальше</h3>
      <p>Семантические блоки, FAQ и внутренние ссылки на услуги.</p>
    </main>
  );
};
