import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { WikiApi } from '../api';
import { WikiViewer } from '../components/WikiViewer';
import { Loader2, AlertCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export const PageDetail = () => {
  const { slug } = useParams<{ slug: string }>();
  const [page, setPage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPage = async () => {
      if (!slug) return;
      try {
        setLoading(true);
        const data = await WikiApi.getPage(slug);
        setPage(data);
      } catch (err) {
        console.error(err);
        setError('Failed to load page. It might not exist yet.');
      } finally {
        setLoading(false);
      }
    };

    fetchPage();
  }, [slug]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || !page) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Page Not Found</h2>
        <p className="text-gray-500 mt-2">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8 border-b border-gray-200 dark:border-gray-800 pb-6">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">{page.title}</h1>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>Version {page.version}</span>
          <span>•</span>
          <span>Updated {formatDistanceToNow(new Date(page.updated_at))} ago</span>
        </div>
      </div>

      <WikiViewer content={page.current_revision?.content || page.content || ''} />
    </div>
  );
};
