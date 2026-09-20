const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface DocTalkNotification {
  id: string;
  user_id: string;
  consultation_id?: string | null;
  encounter_id?: string | null;
  event_type: string;
  title: string;
  message: string;
  severity: 'INFO' | 'SUCCESS' | 'WARNING' | 'URGENT';
  is_read: boolean;
  created_at: string;
  meta_data?: Record<string, any> | null;
}

export interface NotificationCountResponse {
  unread_count: number;
}

function getAuthHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function getNotifications(unreadOnly = false, limit = 50): Promise<DocTalkNotification[]> {
  const url = new URL(`${API_BASE_URL}/doctalk/notifications`);
  if (unreadOnly) url.searchParams.append('unread_only', 'true');
  url.searchParams.append('limit', limit.toString());

  const res = await fetch(url.toString(), {
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch notifications: ${res.statusText}`);
  }

  return res.json();
}

export async function getUnreadNotificationCount(): Promise<number> {
  const res = await fetch(`${API_BASE_URL}/doctalk/notifications/count`, {
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    return 0;
  }

  const data: NotificationCountResponse = await res.json();
  return data.unread_count || 0;
}

export async function markNotificationRead(id: string): Promise<DocTalkNotification> {
  const res = await fetch(`${API_BASE_URL}/doctalk/notifications/${id}/read`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    throw new Error(`Failed to mark notification as read: ${res.statusText}`);
  }

  return res.json();
}

export async function markAllNotificationsRead(): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/doctalk/notifications/read-all`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  if (!res.ok) {
    throw new Error(`Failed to mark all notifications as read: ${res.statusText}`);
  }
}
