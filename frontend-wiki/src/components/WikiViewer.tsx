import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import mermaid from 'mermaid';
import 'highlight.js/styles/github-dark.css';

interface WikiViewerProps {
  content: string;
  className?: string;
}

// Mermaid initialization
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
});

const MermaidDiagram: React.FC<{ chart: string }> = ({ chart }) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      // Unique ID for each diagram
      const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
      ref.current.innerHTML = ''; // Clear previous render
      
      try {
        mermaid.render(id, chart).then(({ svg }) => {
          if (ref.current) {
            ref.current.innerHTML = svg;
          }
        });
      } catch (error) {
        console.error('Mermaid render error:', error);
        ref.current.innerHTML = '<div class="text-red-500">Failed to render diagram</div>';
      }
    }
  }, [chart]);

  return <div ref={ref} className="mermaid-diagram my-4 flex justify-center bg-white dark:bg-gray-800 p-4 rounded-lg overflow-x-auto" />;
};

export const WikiViewer: React.FC<WikiViewerProps> = ({ content, className }) => {
  return (
    <div className={`prose prose-blue dark:prose-invert max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          code: (props) => {
            const { children, className, ...rest } = props;
            // Check for inline code or block code based on children type or missing className
            // In newer react-markdown, 'inline' is not passed directly.
            // Usually, block code has a className like 'language-xxx'.
            
            const match = /language-(\w+)/.exec(className || '');
            const isMermaid = match && match[1] === 'mermaid';

            // Determine if it is likely inline (no match and simple content) or block
            // A safer check: if match exists, it's definitely a block with language. 
            // If no match, it might be inline code or block code without language.
            const isBlock = !!match; 

            if (isMermaid) {
               return <MermaidDiagram chart={String(children).replace(/\n$/, '')} />;
            }

            return isBlock ? (
              <div className="relative group">
                <code className={className} {...rest}>
                  {children}
                </code>
              </div>
            ) : (
              <code className={className} {...rest}>
                {children}
              </code>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
