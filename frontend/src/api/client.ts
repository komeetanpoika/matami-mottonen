export interface EventOut {
  id: number; slug: string; title_fi: string | null; title_en: string | null
  description_fi: string | null; description_en: string | null
  starts_at: string; ends_at: string | null; location: string | null
  price_cents: number; currency: string; capacity: number; seats_left: number; sold_out: boolean
}
export interface AdminEventOut extends EventOut { is_published: boolean; confirmed_count: number; pending_count: number }
export interface EventIn {
  title_fi: string | null; title_en: string | null; description_fi: string | null; description_en: string | null
  starts_at: string; ends_at: string | null; location: string | null
  price_cents: number; capacity: number; is_published: boolean
}
export interface AdminRegistrationOut {
  id: string; name: string; email: string; quantity: number; status: string
  amount_cents: number; created_at: string; confirmed_at: string | null
}
export type RegistrationStatus = 'pending' | 'confirmed' | 'cancelled' | 'expired'

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) { super(`API ${status}`) }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    credentials: 'same-origin',
  })
  if (!r.ok) {
    let detail: unknown = null
    try { detail = (await r.json()).detail } catch { /* no body */ }
    throw new ApiError(r.status, detail)
  }
  if (r.status === 204) return undefined as T
  return r.json() as Promise<T>
}
const post = <T,>(path: string, body?: unknown) => req<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
const put = <T,>(path: string, body: unknown) => req<T>(path, { method: 'PUT', body: JSON.stringify(body) })

export const api = {
  getEvents: () => req<EventOut[]>('/events'),
  getEvent: (slug: string) => req<EventOut>(`/events/${slug}`),
  checkout: (slug: string, body: { name: string; email: string; quantity: number; lang: string }) =>
    post<{ registration_id: string; checkout_url: string | null }>(`/events/${slug}/checkout`, body),
  registrationStatus: (id: string) => req<{ status: RegistrationStatus; event_slug: string; quantity: number }>(`/registrations/${id}/status`),
  cancelRegistration: (id: string) => post<void>(`/registrations/${id}/cancel`),
  login: (email: string, password: string) => post<void>('/auth/login', { email, password }),
  logout: () => post<void>('/auth/logout'),
  me: () => req<{ email: string }>('/auth/me'),
  admin: {
    listEvents: () => req<AdminEventOut[]>('/admin/events'),
    getEvent: (id: number) => req<AdminEventOut>(`/admin/events/${id}`),
    createEvent: (body: EventIn) => post<AdminEventOut>('/admin/events', body),
    updateEvent: (id: number, body: EventIn) => put<AdminEventOut>(`/admin/events/${id}`, body),
    deleteEvent: (id: number) => req<void>(`/admin/events/${id}`, { method: 'DELETE' }),
    registrations: (id: number) => req<AdminRegistrationOut[]>(`/admin/events/${id}/registrations`),
    registrationsCsvUrl: (id: number) => `/api/admin/events/${id}/registrations.csv`,
  },
}
