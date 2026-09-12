import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

export function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'active':
    case 'passed':
    case 'success':
    case 'completed':
      return 'bg-green-500/20 text-green-400';
    case 'failed':
    case 'error':
    case 'fatal':
      return 'bg-red-500/20 text-red-400';
    case 'running':
    case 'pending':
      return 'bg-blue-500/20 text-blue-400';
    case 'warning':
      return 'bg-yellow-500/20 text-yellow-400';
    default:
      return 'bg-muted text-muted-foreground';
  }
}

export function getConfidenceColor(confidence: string): string {
  switch (confidence?.toLowerCase()) {
    case 'very_high':
      return 'bg-emerald-500/20 text-emerald-400';
    case 'high':
      return 'bg-green-500/20 text-green-400';
    case 'medium':
      return 'bg-yellow-500/20 text-yellow-400';
    case 'low':
      return 'bg-orange-500/20 text-orange-400';
    default:
      return 'bg-muted text-muted-foreground';
  }
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}