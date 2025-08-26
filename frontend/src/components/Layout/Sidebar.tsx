import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  HomeIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  XMarkIcon,
  Bars3Icon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon, permission: 'read' },
  { name: 'ChatOps', href: '/chatops', icon: ChatBubbleLeftRightIcon, permission: 'read' },
  { name: 'Monitoring', href: '/monitoring', icon: ChartBarIcon, permission: 'read' },
  { name: 'Admin', href: '/admin', icon: Cog6ToothIcon, permission: 'admin' },
];

const Sidebar: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, hasPermission } = useAuth();

  const filteredNavigation = navigation.filter(item => hasPermission(item.permission));

  return (
    <>
      {/* Mobile sidebar */}
      <div className={clsx(
        'fixed inset-0 z-50 lg:hidden',
        sidebarOpen ? 'block' : 'hidden'
      )}>
        <div className="fixed inset-0 bg-gray-900/80" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 z-50 w-72 bg-white">
          <div className="flex h-full flex-col">
            <div className="flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 px-6">
              <img
                className="h-8 w-auto"
                src="/logo.svg"
                alt="SmartCloudOps AI"
              />
              <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
                <div className="flex items-center gap-x-4 lg:gap-x-6">
                  <span className="text-sm font-semibold leading-6 text-gray-900">
                    SmartCloudOps AI
                  </span>
                </div>
              </div>
              <button
                type="button"
                className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
                onClick={() => setSidebarOpen(false)}
              >
                <span className="sr-only">Close sidebar</span>
                <XMarkIcon className="h-6 w-6" aria-hidden="true" />
              </button>
            </div>
            <nav className="flex flex-1 flex-col">
              <ul role="list" className="flex flex-1 flex-col gap-y-7 px-6 py-4">
                <li>
                  <ul role="list" className="-mx-2 space-y-1">
                    {filteredNavigation.map((item) => (
                      <li key={item.name}>
                        <NavLink
                          to={item.href}
                          className={({ isActive }) =>
                            clsx(
                              isActive
                                ? 'bg-gray-50 text-indigo-600'
                                : 'text-gray-700 hover:text-indigo-600 hover:bg-gray-50',
                              'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold'
                            )
                          }
                          onClick={() => setSidebarOpen(false)}
                        >
                          <item.icon
                            className="h-6 w-6 shrink-0"
                            aria-hidden="true"
                          />
                          {item.name}
                        </NavLink>
                      </li>
                    ))}
                  </ul>
                </li>
                <li className="mt-auto">
                  <div className="flex items-center gap-x-4 px-6 py-3 text-sm font-semibold leading-6 text-gray-900">
                    <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
                      <span className="text-white font-medium">
                        {user?.username?.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <span className="sr-only">Your profile</span>
                    <span aria-hidden="true">{user?.username}</span>
                  </div>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white px-6 pb-4">
          <div className="flex h-16 shrink-0 items-center">
            <img
              className="h-8 w-auto"
              src="/logo.svg"
              alt="SmartCloudOps AI"
            />
            <div className="ml-3">
              <span className="text-lg font-semibold text-gray-900">
                SmartCloudOps AI
              </span>
            </div>
          </div>
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-7">
              <li>
                <ul role="list" className="-mx-2 space-y-1">
                  {filteredNavigation.map((item) => (
                    <li key={item.name}>
                      <NavLink
                        to={item.href}
                        className={({ isActive }) =>
                          clsx(
                            isActive
                              ? 'bg-gray-50 text-indigo-600'
                              : 'text-gray-700 hover:text-indigo-600 hover:bg-gray-50',
                            'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold'
                          )
                        }
                      >
                        <item.icon
                          className="h-6 w-6 shrink-0"
                          aria-hidden="true"
                        />
                        {item.name}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              </li>
              <li className="mt-auto">
                <div className="flex items-center gap-x-4 px-6 py-3 text-sm font-semibold leading-6 text-gray-900">
                  <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
                    <span className="text-white font-medium">
                      {user?.username?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="sr-only">Your profile</span>
                  <span aria-hidden="true">{user?.username}</span>
                </div>
              </li>
            </ul>
          </nav>
        </div>
      </div>

      {/* Mobile menu button */}
      <div className="sticky top-0 z-40 flex items-center gap-x-6 bg-white px-4 py-4 shadow-sm sm:px-6 lg:hidden">
        <button
          type="button"
          className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
          onClick={() => setSidebarOpen(true)}
        >
          <span className="sr-only">Open sidebar</span>
          <Bars3Icon className="h-6 w-6" aria-hidden="true" />
        </button>
        <div className="flex-1 text-sm font-semibold leading-6 text-gray-900">
          SmartCloudOps AI
        </div>
      </div>
    </>
  );
};

export default Sidebar;
