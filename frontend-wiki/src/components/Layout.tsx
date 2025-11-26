import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { BookOpen, Search, Menu, X, Home, Code, FileText, Settings } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import clsx from 'clsx';
import { NamespaceTree } from './NamespaceTree';

interface SidebarItemProps {
    to: string;
    icon: LucideIcon;
    label: string;
    active: boolean;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ to, icon: Icon, label, active }) => (
  <Link
    to={to}
    className={clsx(
      "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
      active 
        ? "bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400" 
        : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
    )}
  >
    <Icon size={18} />
    <span>{label}</span>
  </Link>
);

export const Layout = () => {
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(true);

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900">
      {/* Sidebar */}
      <aside 
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-64 bg-gray-50 dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0 flex flex-col",
          !isSidebarOpen && "-translate-x-full lg:hidden"
        )}
      >
        <div className="flex items-center h-14 px-4 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
          <BookOpen className="w-6 h-6 text-blue-600 mr-2" />
          <span className="font-bold text-lg text-gray-900 dark:text-white">1cAI Wiki</span>
          <button onClick={() => setIsSidebarOpen(false)} className="ml-auto lg:hidden">
            <X size={20} />
          </button>
        </div>

        <div className="p-3 space-y-1 flex-shrink-0">
          <SidebarItem to="/" icon={Home} label="Home" active={location.pathname === "/"} />
          <SidebarItem to="/pages" icon={FileText} label="All Pages" active={location.pathname === "/pages"} />
          <SidebarItem to="/code" icon={Code} label="Code Explorer" active={location.pathname.startsWith("/code")} />
        </div>
        
        <div className="flex-1 overflow-y-auto px-2">
            <NamespaceTree />
        </div>

        <div className="p-3 border-t border-gray-200 dark:border-gray-800 flex-shrink-0">
          <SidebarItem to="/settings" icon={Settings} label="Settings" active={location.pathname === "/settings"} />
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="h-14 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 -ml-2 text-gray-600 lg:hidden">
            <Menu size={20} />
          </button>

          <div className="flex-1 max-w-2xl mx-auto px-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input 
                type="text" 
                placeholder="Search documentation and code..." 
                className="w-full pl-9 pr-4 py-1.5 bg-gray-100 dark:bg-gray-800 border-none rounded-md text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* User profile placeholder */}
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs">
              U
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
