import { dev } from '$app/environment';

export function root(): string {
	return '/';
}

export function apiRoot(): string {
	if (dev) {
		return 'http://localhost:8000/api';
	}
	return 'https://lyrics-backend-3u4c.onrender.com';
}
