/**
 * Type definitions for X-Daemon monitoring and control
 */

/**
 * Represents the status of a single operation/task
 */
export interface OperationLog {
  task_id: string;
  task_type: string;
  timestamp: string;
  success: boolean;
  duration_ms?: number;
  error?: string;
}

/**
 * Queue statistics from the TaskQueue system
 */
export interface QueueStatus {
  pending: number;
  running: number;
  completed: number;
  failed: number;
}

/**
 * Chrome Pool health and state information
 */
export interface ChromeStatus {
  healthy: boolean;
  browser_active: boolean;
  last_activity?: string;
}

/**
 * Complete daemon status snapshot
 */
export interface DaemonStatus {
  daemon_status: "running" | "stopped";
  chrome_pool_healthy: boolean;
  queue_stats: QueueStatus;
  uptime_seconds: number;
  total_operations?: number;
  successful_operations?: number;
  failed_operations?: number;
  last_operation?: OperationLog;
}

/**
 * API response wrapper type
 */
export interface ApiResponse<T = any> {
  status?: string;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * Tauri invoke call response for worker API
 */
export interface WorkerApiResponse {
  status: string;
  data?: any;
  error?: string;
}

/**
 * Tweet form state for posting tweets
 */
export interface TweetFormState {
  text: string;
  images: string[];
  isValid: boolean;
  charCount: number;
}

/**
 * Reply form state for replying to tweets
 */
export interface ReplyFormState {
  tweetUrl: string;
  text: string;
  isValid: boolean;
  charCount: number;
}

/**
 * Quote tweet form state for quoting tweets
 */
export interface QuoteFormState {
  tweetUrl: string;
  text: string;
  images: string[];
  isValid: boolean;
  charCount: number;
}

/**
 * Quick action form state for likes/retweets
 */
export interface QuickActionState {
  tweetUrl: string;
  isValid: boolean;
}

/**
 * Operation history item from user actions
 */
export interface OperationHistoryItem {
  id: string;
  type: "post" | "reply" | "quote" | "like" | "retweet";
  status: "success" | "failed" | "pending";
  timestamp: string;
  taskId: string;
  error?: string;
}
