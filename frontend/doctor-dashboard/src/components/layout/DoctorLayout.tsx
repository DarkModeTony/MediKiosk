'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  LogOut,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
  Bell,
  Search,
  Stethoscope,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Video,
  FileText,
  X,
  ExternalLink,
  Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  DocTalkNotification,
  getNotifications,
  getUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
} from '@/lib/api/notifications';

interface NavItem {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  badge?: number;
}

interface DoctorLayoutProps {
  children: React.ReactNode;
}

export default function DoctorLayout({ children }: DoctorLayoutProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [dark, setDark] = useState(false);

  // Active physician profile
  const [currentUser, setCurrentUser] = useState<{
    displayName: string;
    specialty: string;
    subSpecialty?: string;
    hospital: string;
    city?: string;
    initials: string;
  } | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('currentUser');
      const token = localStorage.getItem('token');
      if (stored) {
        const parsed = JSON.parse(stored);
        setCurrentUser(parsed);
        if (!token && parsed?.username) {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
          fetch(`${apiUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: parsed.username, password: 'demo1234' }),
          })
            .then((res) => (res.ok ? res.json() : null))
            .then((data) => {
              if (data?.access_token) {
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('access_token', data.access_token);
              }
            })
            .catch(() => {});
        }
      }
    } catch (e) {
      console.warn('Could not read user profile from storage', e);
    }
  }, []);

  // Notification state
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notificationOpen, setNotificationOpen] = useState<boolean>(false);
  const [notifications, setNotifications] = useState<DocTalkNotification[]>([]);
  const [loadingNotifs, setLoadingNotifs] = useState<boolean>(false);
  const [activeToast, setActiveToast] = useState<DocTalkNotification | null>(null);
  const notifDropdownRef = useRef<HTMLDivElement>(null);

  const toggleDark = () => {
    setDark((d) => !d);
    document.documentElement.classList.toggle('dark');
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        notifDropdownRef.current &&
        !notifDropdownRef.current.contains(event.target as Node)
      ) {
        setNotificationOpen(false);
      }
    };
    if (notificationOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [notificationOpen]);

  // Polling for notifications & unread count
  useEffect(() => {
    let prevCount = 0;
    const fetchCount = async () => {
      try {
        const count = await getUnreadNotificationCount();
        if (count > prevCount && count > 0) {
          // New notification arrived! Fetch latest and show active toast
          try {
            const list = await getNotifications(true, 1);
            if (list && list.length > 0) {
              setActiveToast(list[0]);
              // Auto dismiss toast after 6s
              setTimeout(() => {
                setActiveToast((current) => (current?.id === list[0].id ? null : current));
              }, 6000);
            }
          } catch {
            // silent
          }
        }
        prevCount = count;
        setUnreadCount(count);
      } catch {
        // silent
      }
    };

    fetchCount();
    const interval = setInterval(fetchCount, 6000);
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    setLoadingNotifs(true);
    try {
      const list = await getNotifications(false, 15);
      setNotifications(list);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoadingNotifs(false);
    }
  };

  const handleToggleNotifications = () => {
    const nextState = !notificationOpen;
    setNotificationOpen(nextState);
    if (nextState) {
      loadNotifications();
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
    }
  };

  const handleMarkSingleRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const navItems: NavItem[] = [
    { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { href: '/queue', icon: Users, label: 'Patient Queue' },
    {
      href: '/doctalk',
      icon: Stethoscope,
      label: 'DocTalk Requests',
      badge: unreadCount > 0 ? unreadCount : undefined,
    },
  ];

  const getNotificationIcon = (type: string, severity: string) => {
    switch (type) {
      case 'DOCTALK_ACCEPTED':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />;
      case 'DOCTALK_DECLINED':
        return <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />;
      case 'DOCTALK_EXPIRED':
        return <Clock className="w-4 h-4 text-amber-500 shrink-0" />;
      case 'DOCTALK_STARTED':
        return <Video className="w-4 h-4 text-teal-500 shrink-0" />;
      case 'DOCTALK_COMPLETED':
        return <Check className="w-4 h-4 text-teal-600 shrink-0" />;
      case 'DOCTALK_REQUEST_CREATED':
        return <Stethoscope className="w-4 h-4 text-teal-500 shrink-0" />;
      case 'DOCTALK_CANCELLED':
        return <X className="w-4 h-4 text-slate-400 shrink-0" />;
      default:
        return severity === 'WARNING' || severity === 'URGENT' ? (
          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
        ) : (
          <Bell className="w-4 h-4 text-teal-500 shrink-0" />
        );
    }
  };

  return (
    <div className={cn('min-h-screen flex h-screen overflow-hidden', dark ? 'dark' : '')}>
      {/* ── Active Real-Time Toast Notification Banner ──────────────────────── */}
      {activeToast && (
        <div className="fixed top-5 right-5 z-50 max-w-sm w-full animate-bounce-short shadow-2xl rounded-2xl bg-white dark:bg-slate-800 border border-teal-500/40 p-4 flex items-start gap-3">
          <div className="p-2 rounded-xl bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5">
            {getNotificationIcon(activeToast.event_type, activeToast.severity)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate">
                {activeToast.title}
              </p>
              <button
                onClick={() => setActiveToast(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5 line-clamp-2">
              {activeToast.message}
            </p>
            <div className="mt-2 flex items-center gap-2">
              <Link
                href="/doctalk"
                onClick={() => {
                  handleMarkSingleRead(activeToast.id);
                  setActiveToast(null);
                }}
                className="text-[10px] font-bold text-teal-600 dark:text-teal-400 hover:underline flex items-center gap-1"
              >
                <span>View DocTalk</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside
        className={cn(
          'flex flex-col bg-slate-900 text-slate-300 shrink-0 transition-all duration-300 ease-in-out border-r border-slate-800',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-slate-800 bg-slate-950 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center shrink-0 p-1 shadow-md">
            <Image
              src="/logo-white.png"
              alt="MediPlatform"
              width={22}
              height={22}
              className="w-full h-full object-contain"
            />
          </div>
          {!collapsed && (
            <div className="ml-3 min-w-0">
              <p className="text-white font-bold text-sm truncate">MediPlatform</p>
              <p className="text-teal-400 text-[10px] font-semibold tracking-wider truncate">PHYSICIAN WORKSPACE</p>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-5 px-2 space-y-1 overflow-y-auto">
          {navItems.map(({ href, icon: Icon, label, badge }) => {
            const active = pathname === href || pathname.startsWith(href + '/');
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group',
                  active
                    ? 'bg-teal-600/20 text-teal-300 border border-teal-600/30'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                )}
              >
                {/* Active left bar */}
                {active && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-teal-400 rounded-full -ml-2" />
                )}
                <Icon
                  className={cn(
                    'w-5 h-5 shrink-0 transition-colors',
                    active ? 'text-teal-400' : 'text-slate-500 group-hover:text-slate-300'
                  )}
                />
                {!collapsed && (
                  <span className="truncate">{label}</span>
                )}
                {!collapsed && badge !== undefined && badge > 0 && (
                  <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-red-500 text-white animate-pulse shadow-sm">
                    {badge}
                  </span>
                )}
                {collapsed && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-slate-700 text-slate-100 text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
                    {label}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="border-t border-slate-800 p-2 space-y-1 shrink-0">
          {/* Dark mode toggle */}
          <button
            onClick={toggleDark}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-all"
          >
            {dark ? <Sun className="w-5 h-5 shrink-0 text-amber-400" /> : <Moon className="w-5 h-5 shrink-0 text-slate-500" />}
            {!collapsed && <span>{dark ? 'Light Mode' : 'Dark Mode'}</span>}
          </button>

          {/* Doctor avatar */}
          <div className={cn('flex items-center gap-3 px-3 py-2.5 rounded-xl', !collapsed && 'bg-slate-800/50')}>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center text-white text-xs font-black shrink-0 shadow-sm">
              {currentUser?.initials || 'PS'}
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <p className="text-slate-200 text-xs font-bold truncate">{currentUser?.displayName || 'Dr. Priya Sharma'}</p>
                <p className="text-slate-400 text-[10px] truncate">{currentUser?.specialty || 'Internal Medicine'}</p>
              </div>
            )}
          </div>

          {/* Sign out */}
          <Link
            href="/login"
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:bg-red-900/30 hover:text-red-400 transition-all"
          >
            <LogOut className="w-5 h-5 shrink-0" />
            {!collapsed && <span>Sign Out</span>}
          </Link>

          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="w-full flex items-center justify-center p-2 rounded-xl text-slate-600 hover:bg-slate-800 hover:text-slate-300 transition-all"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-50 dark:bg-slate-900">
        {/* Top header */}
        <header className="h-16 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center px-6 gap-4 shadow-sm z-10 shrink-0">
          {/* Search */}
          <div className="flex-1 flex items-center gap-2 max-w-md">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="search"
                placeholder="Search patients, encounters…"
                className="w-full pl-9 pr-4 py-2 rounded-xl text-sm border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all"
              />
            </div>
          </div>

          <div className="flex items-center gap-3 ml-auto relative">
            {/* Active Doctor & Hospital Badge */}
            {currentUser && (
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-700/60 border border-slate-200 dark:border-slate-600 text-xs">
                <span className="font-bold text-slate-800 dark:text-slate-100">{currentUser.displayName}</span>
                <span className="text-slate-300 dark:text-slate-500">·</span>
                <span className="text-teal-600 dark:text-teal-400 font-semibold">{currentUser.specialty}</span>
                <span className="text-slate-300 dark:text-slate-500">·</span>
                <span className="text-slate-500 dark:text-slate-400 font-medium truncate max-w-[200px]">{currentUser.hospital}</span>
              </div>
            )}

            {/* Live indicator */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wide">Live</span>
            </div>

            {/* Notifications Bell Button & Popover */}
            <div className="relative" ref={notifDropdownRef}>
              <button
                type="button"
                onClick={handleToggleNotifications}
                className={cn(
                  'relative p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-800 dark:hover:text-slate-200 transition-all',
                  notificationOpen && 'bg-slate-100 dark:bg-slate-700 text-teal-600'
                )}
                aria-label="DocTalk Notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 min-w-[18px] h-[18px] px-1 text-[10px] font-bold rounded-full bg-red-500 text-white flex items-center justify-center animate-pulse shadow-md">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Dropdown Popover */}
              {notificationOpen && (
                <div className="absolute right-0 top-12 w-80 sm:w-96 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 py-3 z-50 animate-fade-in flex flex-col max-h-[480px]">
                  <div className="px-4 pb-2.5 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                        DocTalk Notifications
                      </span>
                      {unreadCount > 0 && (
                        <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-teal-100 dark:bg-teal-900/60 text-teal-700 dark:text-teal-300">
                          {unreadCount} new
                        </span>
                      )}
                    </div>
                    {unreadCount > 0 && (
                      <button
                        type="button"
                        onClick={handleMarkAllRead}
                        className="text-[11px] font-semibold text-teal-600 hover:text-teal-700 dark:text-teal-400 hover:underline"
                      >
                        Mark all read
                      </button>
                    )}
                  </div>

                  {/* Notification List */}
                  <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700/60">
                    {loadingNotifs ? (
                      <div className="p-6 text-center text-xs text-slate-400">
                        Loading notifications…
                      </div>
                    ) : notifications.length === 0 ? (
                      <div className="p-8 text-center space-y-2">
                        <Bell className="w-8 h-8 text-slate-300 dark:text-slate-600 mx-auto stroke-1" />
                        <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                          No notifications yet
                        </p>
                        <p className="text-[11px] text-slate-400">
                          You will be notified when specialists accept, decline, or updates occur.
                        </p>
                      </div>
                    ) : (
                      notifications.map((n) => (
                        <div
                          key={n.id}
                          onClick={() => {
                            if (!n.is_read) handleMarkSingleRead(n.id);
                          }}
                          className={cn(
                            'p-3.5 flex items-start gap-3 hover:bg-slate-50 dark:hover:bg-slate-700/40 transition-colors cursor-pointer',
                            !n.is_read && 'bg-teal-50/40 dark:bg-teal-950/20'
                          )}
                        >
                          <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 shrink-0 mt-0.5">
                            {getNotificationIcon(n.event_type, n.severity)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-1">
                              <p className={cn(
                                'text-xs truncate',
                                !n.is_read ? 'font-bold text-slate-900 dark:text-slate-100' : 'font-semibold text-slate-700 dark:text-slate-300'
                              )}>
                                {n.title}
                              </p>
                              {!n.is_read && (
                                <span className="w-2 h-2 rounded-full bg-teal-500 shrink-0" />
                              )}
                            </div>
                            <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5 line-clamp-2">
                              {n.message}
                            </p>
                            <p className="text-[10px] text-slate-400 mt-1" suppressHydrationWarning>
                              {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="pt-2 px-4 border-t border-slate-100 dark:border-slate-700 text-center">
                    <Link
                      href="/doctalk"
                      onClick={() => setNotificationOpen(false)}
                      className="text-xs font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400 hover:underline"
                    >
                      Open DocTalk Specialist Hub →
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center text-white text-xs font-black shadow-sm">
              DS
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-auto p-6 md:p-8">
          {children}
        </div>
      </div>
    </div>
  );
}
