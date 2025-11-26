import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { WikiApi } from '../api';
import { FileText, Plus, Loader2, AlertCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface WikiPageSummary {
  id: string;
  slug: string;
  title: string;
  updated_at: string;
  version: number;
}

export const PagesList = () => {
  const [pages, setPages] = useState<WikiPageSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPages = async () => {
      try {
        setLoading(true);
        const data = await WikiApi.getPages();
        setPages(data);
      } catch (err) {
        console.error("Failed to fetch pages:", err);
        setError('Failed to load pages. Please check API connection.');
      } finally {
        setLoading(false);
      }
    };

    fetchPages();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Wiki Pages</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage and view documentation</p>
        </div>
        <Link to="/pages/new" className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            <Plus size={18} />
            New Page
        </Link>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
            <AlertCircle size={20} />
            {error}
        </div>
      )}

      {!loading && pages.length === 0 ? (
        <div className="text-center py-16 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-lg bg-gray-50 dark:bg-gray-900/50">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">No pages found</h3>
            <p className="text-gray-500 mb-4">Get started by creating your first wiki page.</p>
            <Link to="/pages/new" className="text-blue-600 hover:underline font-medium">Create Page</Link>
        </div>
      ) : (
        <div className="grid gap-4">
            {pages.map((page) => (
                <Link 
                    key={page.id} 
                    to={`/pages/${page.slug}`}
                    className="block p-4 border border-gray-200 dark:border-gray-800 rounded-lg hover:border-blue-500 dark:hover:border-blue-500 bg-white dark:bg-gray-900 transition-colors"
                >
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">{page.title}</h3>
                            <div className="text-sm text-gray-500 font-mono bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded inline-block">
                                /{page.slug}
                            </div>
                        </div>
                        <span className="text-xs text-gray-400">
                            v{page.version} • {formatDistanceToNow(new Date(page.updated_at))} ago
                        </span>
                    </div>
                </Link>
            ))}
        </div>
      )}
    </div>
  );
};
