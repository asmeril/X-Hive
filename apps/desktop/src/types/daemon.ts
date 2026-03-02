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

// ============================================
// APPROVAL SYSTEM TYPES
// ============================================

/**
 * Content category enum matching backend
 */
export type ContentCategory = 
  | "ai_ml"
  | "tech_programming"
  | "startup_business"
  | "gaming_entertainment"
  | "crypto_web3"
  | "mobile_apps"
  | "security_privacy"
  | "science"
  | "prediction_market"
  | "news";

/**
 * Single approval item from pending queue
 */
export interface ApprovalItem {
  id: string;
  title: string;
  category: ContentCategory;
  source: string;
  source_type: string;
  url: string;
  description?: string;
  content?: string;
  author?: string;
  published_at: string;
  created_at: string;
  relevance_score: number;
  engagement_score: number;
  suggested_tweet?: string;
  ai_summary?: string;
  images?: string[];
  tags?: string[];
  metadata?: Record<string, any>;
}

/**
 * Response from /approval/pending endpoint
 */
export interface ApprovalResponse {
  status: "success" | "error";
  data: {
    pending_count: number;
    items: ApprovalItem[];
  };
  message?: string;
}

/**
 * Response from /approval/approve or /approval/reject
 */
export interface ApprovalActionResponse {
  status: "success" | "error";
  message: string;
  item_id: string;
  action: "approved" | "rejected";
  timestamp?: string;
}

/**
 * Filter state for approval interface
 */
export interface ApprovalFilters {
  category: ContentCategory | "all";
  source: string | "all";
  searchQuery: string;
}

/**
 * Category metadata for display
 */
export interface CategoryInfo {
  id: ContentCategory;
  label: string;
  emoji: string;
  color: string;
}
