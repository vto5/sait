import { Link } from 'react-router-dom';
import { blogPosts } from '../content/blog';

export const BlogListPage = () => {
  return (
    <main className="container section">
      <h1>Блог</h1>
      <p>Раздел для SEO-статей и экспертных материалов.</p>
      {blogPosts.map((post) => (
        <article key={post.slug} className="card">
          <h2>
            <Link to={`/blog/${post.slug}`}>{post.title}</Link>
          </h2>
          <p>{post.excerpt}</p>
        </article>
      ))}
    </main>
  );
};
