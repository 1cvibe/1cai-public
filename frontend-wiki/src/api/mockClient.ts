import { WikiApi as RealApi } from './client';

// Types mirroring the backend models
export interface WikiPageSummary {
  id: string;
  slug: string;
  title: string;
  updated_at: string;
  version: number;
}

export interface WikiPageDetail extends WikiPageSummary {
  content: string;
  current_revision?: { content: string };
}

// Mock Data
const MOCK_PAGES: WikiPageDetail[] = [
  {
    id: '1',
    slug: 'architecture-overview',
    title: 'Architecture Overview',
    updated_at: new Date().toISOString(),
    version: 5,
    content: `# Architecture Overview\n\nThis system follows a **Microservices** approach.\n\n## Components\n- **API Gateway**: Entry point.\n- **Wiki Service**: Documentation engine.\n- **Auth Service**: User management.\n\n\`\`\`mermaid\ngraph TD\n  Client --> Gateway\n  Gateway --> Wiki\n  Gateway --> Auth\n\`\`\``,
    current_revision: { content: `# Architecture Overview\n\nThis system follows a **Microservices** approach.\n\n## Components\n- **API Gateway**: Entry point.\n- **Wiki Service**: Documentation engine.\n- **Auth Service**: User management.\n\n\`\`\`mermaid\ngraph TD\n  Client --> Gateway\n  Gateway --> Wiki\n  Gateway --> Auth\n\`\`\`` }
  },
  {
    id: '2',
    slug: 'getting-started',
    title: 'Getting Started',
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    version: 1,
    content: `# Getting Started\n\nRun \`npm install\` to start.\n\n## Prerequisites\n1. Node.js\n2. Python 3.10\n`,
    current_revision: { content: `# Getting Started\n\nRun \`npm install\` to start.\n\n## Prerequisites\n1. Node.js\n2. Python 3.10\n` }
  },
  {
    id: '3',
    slug: 'codebase-src-services-wiki',
    title: 'src.services.wiki',
    updated_at: new Date().toISOString(),
    version: 2,
    content: `# src.services.wiki\n\n**Path**: \`src/services/wiki\`\n\n## Description\nCore Wiki logic module.\n\n## Architecture (Classes)\n\n\`\`\`mermaid\nclassDiagram\n    class WikiService {\n        +get_page()\n        +create_page()\n    }\n    class CodeSyncService {\n        +sync_all()\n    }\n    WikiService <|-- CodeSyncService : uses\n\`\`\``,
    current_revision: { content: `# src.services.wiki\n\n**Path**: \`src/services/wiki\`\n\n## Description\nCore Wiki logic module.\n\n## Architecture (Classes)\n\n\`\`\`mermaid\nclassDiagram\n    class WikiService {\n        +get_page()\n        +create_page()\n    }\n    class CodeSyncService {\n        +sync_all()\n    }\n    WikiService <|-- CodeSyncService : uses\n\`\`\`` }
  }
];

const MockApi = {
  getPages: async () => {
    await new Promise(resolve => setTimeout(resolve, 500)); // Fake delay
    return MOCK_PAGES.map(({ content, current_revision, ...summary }) => ({ content, current_revision, ...summary }));
  },

  getPage: async (slug: string) => {
    await new Promise(resolve => setTimeout(resolve, 300));
    const page = MOCK_PAGES.find(p => p.slug === slug);
    if (!page) throw new Error('Page not found');
    return page;
  },

  createPage: async (data: any) => {
    await new Promise(resolve => setTimeout(resolve, 800));
    const newPage = {
        ...data,
        id: Math.random().toString(),
        updated_at: new Date().toISOString(),
        version: 1,
        current_revision: { content: data.content }
    };
    MOCK_PAGES.push(newPage);
    return newPage;
  },

  updatePage: async (_slug: string, _data: any) => {
      // stub
      return MOCK_PAGES[0];
  },
  
  search: async (_query: string) => {
      return [];
  }
};

// Export either Real or Mock based on env var (defaulting to Real for safety, but settable)
// Ideally, we use a Vite env var. For now, let's export a helper to switch.
export const useMock = import.meta.env.VITE_USE_MOCK === 'true';

export const WikiApi = useMock ? MockApi : RealApi;
