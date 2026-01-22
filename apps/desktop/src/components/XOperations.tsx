/**
 * X Operations UI Component
 *
 * User interface for executing X operations:
 * - Post tweets with images
 * - Reply to tweets
 * - Quote tweets with comments
 * - Like and retweet (quick actions)
 *
 * Features:
 * - Tab-based interface for different operations
 * - Real-time character counter with color coding
 * - Image upload and preview
 * - Form validation with error messages
 * - Operation history tracking
 * - Loading states and success/error feedback
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import {
  TweetFormState,
  ReplyFormState,
  QuoteFormState,
  QuickActionState,
  OperationHistoryItem,
  WorkerApiResponse,
} from "../types/daemon";

/**
 * Character limit for tweets
 */
const MAX_TWEET_LENGTH = 280;

/**
 * Maximum number of images per tweet
 */
const MAX_IMAGES = 4;

/**
 * Valid image extensions
 */
const VALID_IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "webp"];

/**
 * X Operations component with tab-based interface for all X operations
 */
const XOperations: React.FC = () => {
  // Tab state
  const [activeTab, setActiveTab] = useState<"post" | "reply" | "quote" | "actions">("post");

  // Form states for each operation type
  const [postForm, setPostForm] = useState<TweetFormState>({
    text: "",
    images: [],
    isValid: false,
    charCount: 0,
  });

  const [replyForm, setReplyForm] = useState<ReplyFormState>({
    tweetUrl: "",
    text: "",
    isValid: false,
    charCount: 0,
  });

  const [quoteForm, setQuoteForm] = useState<QuoteFormState>({
    tweetUrl: "",
    text: "",
    images: [],
    isValid: false,
    charCount: 0,
  });

  const [quickActionForm, setQuickActionForm] = useState<QuickActionState>({
    tweetUrl: "",
    isValid: false,
  });

  // UI state
  const [operationHistory, setOperationHistory] = useState<OperationHistoryItem[]>([]);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const historyEndRef = useRef<HTMLDivElement>(null);

  /**
   * Auto-scroll to latest history item
   */
  useEffect(() => {
    if (historyEndRef.current) {
      historyEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [operationHistory]);

  /**
   * Validate tweet text (1-280 characters)
   */
  const validateTweetText = (text: string): boolean => {
    return text.trim().length > 0 && text.length <= MAX_TWEET_LENGTH;
  };

  /**
   * Validate X.com/Twitter.com URL format
   */
  const validateTwitterUrl = (url: string): boolean => {
    try {
      const urlObj = new URL(url);
      const hostname = urlObj.hostname.toLowerCase();
      return hostname.includes("twitter.com") || hostname.includes("x.com");
    } catch {
      return false;
    }
  };

  /**
   * Update post form state and validation
   */
  const handlePostTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setPostForm({
      ...postForm,
      text,
      charCount: text.length,
      isValid: validateTweetText(text),
    });
    setValidationErrors((prev) => ({ ...prev, postText: "" }));
  };

  /**
   * Update reply form state and validation
   */
  const handleReplyUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const tweetUrl = e.target.value;
    const isUrlValid = tweetUrl.length === 0 || validateTwitterUrl(tweetUrl);
    setReplyForm({
      ...replyForm,
      tweetUrl,
      isValid: isUrlValid && validateTweetText(replyForm.text),
    });
    setValidationErrors((prev) => ({
      ...prev,
      replyUrl: isUrlValid ? "" : "Invalid Twitter/X.com URL",
    }));
  };

  const handleReplyTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setReplyForm({
      ...replyForm,
      text,
      charCount: text.length,
      isValid: validateTwitterUrl(replyForm.tweetUrl) && validateTweetText(text),
    });
    setValidationErrors((prev) => ({ ...prev, replyText: "" }));
  };

  /**
   * Update quote form state and validation
   */
  const handleQuoteUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const tweetUrl = e.target.value;
    const isUrlValid = tweetUrl.length === 0 || validateTwitterUrl(tweetUrl);
    setQuoteForm({
      ...quoteForm,
      tweetUrl,
      isValid: isUrlValid && validateTweetText(quoteForm.text),
    });
    setValidationErrors((prev) => ({
      ...prev,
      quoteUrl: isUrlValid ? "" : "Invalid Twitter/X.com URL",
    }));
  };

  const handleQuoteTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setQuoteForm({
      ...quoteForm,
      text,
      charCount: text.length,
      isValid: validateTwitterUrl(quoteForm.tweetUrl) && validateTweetText(text),
    });
    setValidationErrors((prev) => ({ ...prev, quoteText: "" }));
  };

  /**
   * Update quick action form state and validation
   */
  const handleQuickActionUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const tweetUrl = e.target.value;
    const isUrlValid = validateTwitterUrl(tweetUrl);
    setQuickActionForm({
      tweetUrl,
      isValid: isUrlValid,
    });
    setValidationErrors((prev) => ({
      ...prev,
      actionUrl: isUrlValid ? "" : "Invalid Twitter/X.com URL",
    }));
  };

  /**
   * Pick images using Tauri file dialog
   */
  const pickImages = async (operation: "post" | "quote") => {
    try {
      const selected = await open({
        multiple: true,
        filters: [
          {
            name: "Image",
            extensions: VALID_IMAGE_EXTENSIONS,
          },
        ],
      });

      if (selected) {
        const selectedPaths = Array.isArray(selected) ? selected : [selected];
        const currentImages =
          operation === "post" ? postForm.images : quoteForm.images;
        const remainingSlots = MAX_IMAGES - currentImages.length;

        if (selectedPaths.length > remainingSlots) {
          setErrorMessage(
            `Maximum ${MAX_IMAGES} images allowed. ${remainingSlots} slots remaining.`
          );
          return;
        }

        const newImages = [...currentImages, ...selectedPaths];

        if (operation === "post") {
          setPostForm({ ...postForm, images: newImages });
        } else {
          setQuoteForm({ ...quoteForm, images: newImages });
        }

        setErrorMessage(null);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to pick images";
      setErrorMessage(errorMsg);
    }
  };

  /**
   * Remove image from form
   */
  const removeImage = (operation: "post" | "quote", index: number) => {
    if (operation === "post") {
      setPostForm({
        ...postForm,
        images: postForm.images.filter((_, i) => i !== index),
      });
    } else {
      setQuoteForm({
        ...quoteForm,
        images: quoteForm.images.filter((_, i) => i !== index),
      });
    }
  };

  /**
   * Get color for character counter based on count
   */
  const getCharCountColor = (count: number): string => {
    if (count <= 260) return "text-green-600";
    if (count <= 275) return "text-yellow-600";
    return "text-red-600";
  };

  /**
   * Execute post tweet operation
   */
  const executePostTweet = async () => {
    if (!postForm.isValid) {
      setValidationErrors({
        postText: "Tweet must be 1-280 characters",
      });
      return;
    }

    try {
      setLoadingAction("post");
      setErrorMessage(null);

      const body = JSON.stringify({
        text: postForm.text,
        images: postForm.images.length > 0 ? postForm.images : undefined,
      });

      const response = await invoke<WorkerApiResponse>("call_worker_api", {
        method: "POST",
        endpoint: "/x/post",
        body,
      });

      // Add to history
      const historyItem: OperationHistoryItem = {
        id: `post_${Date.now()}`,
        type: "post",
        status: response.status === "ok" ? "success" : "failed",
        timestamp: new Date().toISOString(),
        taskId: response.data?.task_id || "unknown",
        error: response.error,
      };
      setOperationHistory((prev) => [...prev, historyItem].slice(-20));

      if (response.status === "ok") {
        setSuccessMessage(
          `Tweet posted successfully! Task ID: ${response.data?.task_id || "pending"}`
        );
        // Clear form
        setPostForm({
          text: "",
          images: [],
          isValid: false,
          charCount: 0,
        });
      } else {
        setErrorMessage(
          response.error || "Failed to post tweet"
        );
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to post tweet";
      setErrorMessage(errorMsg);
      setOperationHistory((prev) => [
        ...prev,
        {
          id: `post_${Date.now()}`,
          type: "post",
          status: "failed",
          timestamp: new Date().toISOString(),
          taskId: "unknown",
          error: errorMsg,
        },
      ].slice(-20));
    } finally {
      setLoadingAction(null);
    }
  };

  /**
   * Execute reply operation
   */
  const executeReply = async () => {
    if (!replyForm.isValid) {
      setValidationErrors({
        replyUrl: validateTwitterUrl(replyForm.tweetUrl) ? "" : "Invalid URL",
        replyText: validateTweetText(replyForm.text) ? "" : "Text must be 1-280 characters",
      });
      return;
    }

    try {
      setLoadingAction("reply");
      setErrorMessage(null);

      const body = JSON.stringify({
        tweet_url: replyForm.tweetUrl,
        text: replyForm.text,
      });

      const response = await invoke<WorkerApiResponse>("call_worker_api", {
        method: "POST",
        endpoint: "/x/reply",
        body,
      });

      const historyItem: OperationHistoryItem = {
        id: `reply_${Date.now()}`,
        type: "reply",
        status: response.status === "ok" ? "success" : "failed",
        timestamp: new Date().toISOString(),
        taskId: response.data?.task_id || "unknown",
        error: response.error,
      };
      setOperationHistory((prev) => [...prev, historyItem].slice(-20));

      if (response.status === "ok") {
        setSuccessMessage(
          `Reply sent successfully! Task ID: ${response.data?.task_id || "pending"}`
        );
        setReplyForm({
          tweetUrl: "",
          text: "",
          isValid: false,
          charCount: 0,
        });
      } else {
        setErrorMessage(response.error || "Failed to send reply");
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to send reply";
      setErrorMessage(errorMsg);
      setOperationHistory((prev) => [
        ...prev,
        {
          id: `reply_${Date.now()}`,
          type: "reply",
          status: "failed",
          timestamp: new Date().toISOString(),
          taskId: "unknown",
          error: errorMsg,
        },
      ].slice(-20));
    } finally {
      setLoadingAction(null);
    }
  };

  /**
   * Execute quote tweet operation
   */
  const executeQuote = async () => {
    if (!quoteForm.isValid) {
      setValidationErrors({
        quoteUrl: validateTwitterUrl(quoteForm.tweetUrl) ? "" : "Invalid URL",
        quoteText: validateTweetText(quoteForm.text) ? "" : "Text must be 1-280 characters",
      });
      return;
    }

    try {
      setLoadingAction("quote");
      setErrorMessage(null);

      const body = JSON.stringify({
        tweet_url: quoteForm.tweetUrl,
        text: quoteForm.text,
        images: quoteForm.images.length > 0 ? quoteForm.images : undefined,
      });

      const response = await invoke<WorkerApiResponse>("call_worker_api", {
        method: "POST",
        endpoint: "/x/quote",
        body,
      });

      const historyItem: OperationHistoryItem = {
        id: `quote_${Date.now()}`,
        type: "quote",
        status: response.status === "ok" ? "success" : "failed",
        timestamp: new Date().toISOString(),
        taskId: response.data?.task_id || "unknown",
        error: response.error,
      };
      setOperationHistory((prev) => [...prev, historyItem].slice(-20));

      if (response.status === "ok") {
        setSuccessMessage(
          `Quote tweet posted! Task ID: ${response.data?.task_id || "pending"}`
        );
        setQuoteForm({
          tweetUrl: "",
          text: "",
          images: [],
          isValid: false,
          charCount: 0,
        });
      } else {
        setErrorMessage(response.error || "Failed to quote tweet");
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to quote tweet";
      setErrorMessage(errorMsg);
      setOperationHistory((prev) => [
        ...prev,
        {
          id: `quote_${Date.now()}`,
          type: "quote",
          status: "failed",
          timestamp: new Date().toISOString(),
          taskId: "unknown",
          error: errorMsg,
        },
      ].slice(-20));
    } finally {
      setLoadingAction(null);
    }
  };

  /**
   * Execute like operation
   */
  const executeLike = async (url: string = quickActionForm.tweetUrl) => {
    if (!validateTwitterUrl(url)) {
      setErrorMessage("Invalid Twitter/X.com URL");
      return;
    }

    try {
      setLoadingAction("like");
      setErrorMessage(null);

      const body = JSON.stringify({
        tweet_url: url,
      });

      const response = await invoke<WorkerApiResponse>("call_worker_api", {
        method: "POST",
        endpoint: "/x/like",
        body,
      });

      const historyItem: OperationHistoryItem = {
        id: `like_${Date.now()}`,
        type: "like",
        status: response.status === "ok" ? "success" : "failed",
        timestamp: new Date().toISOString(),
        taskId: response.data?.task_id || "unknown",
        error: response.error,
      };
      setOperationHistory((prev) => [...prev, historyItem].slice(-20));

      if (response.status === "ok") {
        setSuccessMessage(`Tweet liked! Task ID: ${response.data?.task_id || "pending"}`);
      } else {
        setErrorMessage(response.error || "Failed to like tweet");
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to like tweet";
      setErrorMessage(errorMsg);
      setOperationHistory((prev) => [
        ...prev,
        {
          id: `like_${Date.now()}`,
          type: "like",
          status: "failed",
          timestamp: new Date().toISOString(),
          taskId: "unknown",
          error: errorMsg,
        },
      ].slice(-20));
    } finally {
      setLoadingAction(null);
    }
  };

  /**
   * Execute retweet operation
   */
  const executeRetweet = async (url: string = quickActionForm.tweetUrl) => {
    if (!validateTwitterUrl(url)) {
      setErrorMessage("Invalid Twitter/X.com URL");
      return;
    }

    try {
      setLoadingAction("retweet");
      setErrorMessage(null);

      const body = JSON.stringify({
        tweet_url: url,
      });

      const response = await invoke<WorkerApiResponse>("call_worker_api", {
        method: "POST",
        endpoint: "/x/retweet",
        body,
      });

      const historyItem: OperationHistoryItem = {
        id: `retweet_${Date.now()}`,
        type: "retweet",
        status: response.status === "ok" ? "success" : "failed",
        timestamp: new Date().toISOString(),
        taskId: response.data?.task_id || "unknown",
        error: response.error,
      };
      setOperationHistory((prev) => [...prev, historyItem].slice(-20));

      if (response.status === "ok") {
        setSuccessMessage(`Tweet retweeted! Task ID: ${response.data?.task_id || "pending"}`);
      } else {
        setErrorMessage(response.error || "Failed to retweet");
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to retweet";
      setErrorMessage(errorMsg);
      setOperationHistory((prev) => [
        ...prev,
        {
          id: `retweet_${Date.now()}`,
          type: "retweet",
          status: "failed",
          timestamp: new Date().toISOString(),
          taskId: "unknown",
          error: errorMsg,
        },
      ].slice(-20));
    } finally {
      setLoadingAction(null);
    }
  };

  /**
   * Dismiss messages
   */
  const dismissMessages = () => {
    setSuccessMessage(null);
    setErrorMessage(null);
  };

  return (
    <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">X Operations</h1>
        <p className="text-gray-600 mt-1">Post, reply, quote, like, and retweet</p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="mb-6 bg-green-50 border-l-4 border-green-500 p-4 rounded-lg flex justify-between items-start">
          <div>
            <p className="text-sm font-medium text-green-800">Success</p>
            <p className="text-sm text-green-700 mt-1">{successMessage}</p>
          </div>
          <button
            onClick={dismissMessages}
            className="text-green-700 hover:text-green-900"
          >
            ✕
          </button>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-lg flex justify-between items-start">
          <div>
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-700 mt-1">{errorMessage}</p>
          </div>
          <button
            onClick={dismissMessages}
            className="text-red-700 hover:text-red-900"
          >
            ✕
          </button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        {["post", "reply", "quote", "actions"].map((tab) => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab as any);
              dismissMessages();
              setValidationErrors({});
            }}
            className={`px-4 py-3 font-medium text-sm transition-colors border-b-2 ${
              activeTab === tab
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-600 hover:text-gray-900"
            }`}
          >
            {tab === "post" && "📝 Post"}
            {tab === "reply" && "💬 Reply"}
            {tab === "quote" && "🔄 Quote"}
            {tab === "actions" && "⚡ Like/Retweet"}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content Area */}
        <div className="lg:col-span-2">
          {/* Post Tab */}
          {activeTab === "post" && (
            <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
              <h2 className="text-xl font-bold text-gray-900">Post a Tweet</h2>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tweet Text *
                </label>
                <textarea
                  value={postForm.text}
                  onChange={handlePostTextChange}
                  placeholder="What's happening?!"
                  maxLength={MAX_TWEET_LENGTH}
                  disabled={loadingAction !== null}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 resize-none"
                  rows={4}
                  aria-label="Tweet text"
                />
                <div className="flex justify-between items-center mt-2">
                  <span
                    className={`text-sm font-medium ${getCharCountColor(
                      postForm.charCount
                    )}`}
                  >
                    {postForm.charCount}/{MAX_TWEET_LENGTH}
                  </span>
                  {validationErrors.postText && (
                    <span className="text-sm text-red-600">
                      {validationErrors.postText}
                    </span>
                  )}
                </div>
              </div>

              {/* Image Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Images (optional, max {MAX_IMAGES})
                </label>
                <button
                  onClick={() => pickImages("post")}
                  disabled={
                    loadingAction !== null || postForm.images.length >= MAX_IMAGES
                  }
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 transition-colors text-sm font-medium"
                >
                  🖼️ Choose Images
                </button>

                {/* Image Previews */}
                {postForm.images.length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-3">
                    {postForm.images.map((img, idx) => (
                      <div key={idx} className="relative bg-gray-100 rounded-lg p-2">
                        <p className="text-xs text-gray-600 truncate mb-2">
                          {img.split(/[\\\/]/).pop()}
                        </p>
                        <button
                          onClick={() => removeImage("post", idx)}
                          className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Post Button */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={executePostTweet}
                  disabled={!postForm.isValid || loadingAction !== null}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition-colors font-medium"
                >
                  {loadingAction === "post" ? "⏳ Posting..." : "📤 Post Tweet"}
                </button>
                <button
                  onClick={() => {
                    setPostForm({
                      text: "",
                      images: [],
                      isValid: false,
                      charCount: 0,
                    });
                    setValidationErrors({});
                  }}
                  disabled={loadingAction !== null}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 transition-colors font-medium"
                >
                  🗑️ Clear
                </button>
              </div>
            </div>
          )}

          {/* Reply Tab */}
          {activeTab === "reply" && (
            <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
              <h2 className="text-xl font-bold text-gray-900">Reply to Tweet</h2>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tweet URL *
                </label>
                <input
                  type="text"
                  value={replyForm.tweetUrl}
                  onChange={handleReplyUrlChange}
                  placeholder="https://x.com/username/status/123456789"
                  disabled={loadingAction !== null}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  aria-label="Tweet URL"
                />
                {validationErrors.replyUrl && (
                  <p className="text-sm text-red-600 mt-1">
                    {validationErrors.replyUrl}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Reply Text *
                </label>
                <textarea
                  value={replyForm.text}
                  onChange={handleReplyTextChange}
                  placeholder="Write your reply..."
                  maxLength={MAX_TWEET_LENGTH}
                  disabled={loadingAction !== null}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 resize-none"
                  rows={4}
                  aria-label="Reply text"
                />
                <div className="flex justify-between items-center mt-2">
                  <span
                    className={`text-sm font-medium ${getCharCountColor(
                      replyForm.charCount
                    )}`}
                  >
                    {replyForm.charCount}/{MAX_TWEET_LENGTH}
                  </span>
                  {validationErrors.replyText && (
                    <span className="text-sm text-red-600">
                      {validationErrors.replyText}
                    </span>
                  )}
                </div>
              </div>

              {/* Reply Button */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={executeReply}
                  disabled={!replyForm.isValid || loadingAction !== null}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition-colors font-medium"
                >
                  {loadingAction === "reply" ? "⏳ Sending..." : "💬 Send Reply"}
                </button>
                <button
                  onClick={() => {
                    setReplyForm({
                      tweetUrl: "",
                      text: "",
                      isValid: false,
                      charCount: 0,
                    });
                    setValidationErrors({});
                  }}
                  disabled={loadingAction !== null}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 transition-colors font-medium"
                >
                  🗑️ Clear
                </button>
              </div>
            </div>
          )}

          {/* Quote Tab */}
          {activeTab === "quote" && (
            <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
              <h2 className="text-xl font-bold text-gray-900">Quote Tweet</h2>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tweet URL *
                </label>
                <input
                  type="text"
                  value={quoteForm.tweetUrl}
                  onChange={handleQuoteUrlChange}
                  placeholder="https://x.com/username/status/123456789"
                  disabled={loadingAction !== null}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  aria-label="Tweet URL to quote"
                />
                {validationErrors.quoteUrl && (
                  <p className="text-sm text-red-600 mt-1">
                    {validationErrors.quoteUrl}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quote Text *
                </label>
                <textarea
                  value={quoteForm.text}
                  onChange={handleQuoteTextChange}
                  placeholder="What do you think?"
                  maxLength={MAX_TWEET_LENGTH}
                  disabled={loadingAction !== null}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 resize-none"
                  rows={4}
                  aria-label="Quote text"
                />
                <div className="flex justify-between items-center mt-2">
                  <span
                    className={`text-sm font-medium ${getCharCountColor(
                      quoteForm.charCount
                    )}`}
                  >
                    {quoteForm.charCount}/{MAX_TWEET_LENGTH}
                  </span>
                  {validationErrors.quoteText && (
                    <span className="text-sm text-red-600">
                      {validationErrors.quoteText}
                    </span>
                  )}
                </div>
              </div>

              {/* Image Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Images (optional, max {MAX_IMAGES})
                </label>
                <button
                  onClick={() => pickImages("quote")}
                  disabled={
                    loadingAction !== null || quoteForm.images.length >= MAX_IMAGES
                  }
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 transition-colors text-sm font-medium"
                >
                  🖼️ Choose Images
                </button>

                {quoteForm.images.length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-3">
                    {quoteForm.images.map((img, idx) => (
                      <div key={idx} className="relative bg-gray-100 rounded-lg p-2">
                        <p className="text-xs text-gray-600 truncate mb-2">
                          {img.split(/[\\\/]/).pop()}
                        </p>
                        <button
                          onClick={() => removeImage("quote", idx)}
                          className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Quote Button */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={executeQuote}
                  disabled={!quoteForm.isValid || loadingAction !== null}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition-colors font-medium"
                >
                  {loadingAction === "quote" ? "⏳ Posting..." : "🔄 Quote Tweet"}
                </button>
                <button
                  onClick={() => {
                    setQuoteForm({
                      tweetUrl: "",
                      text: "",
                      images: [],
                      isValid: false,
                      charCount: 0,
                    });
                    setValidationErrors({});
                  }}
                  disabled={loadingAction !== null}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 transition-colors font-medium"
                >
                  🗑️ Clear
                </button>
              </div>
            </div>
          )}

          {/* Quick Actions Tab */}
          {activeTab === "actions" && (
            <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
              <h2 className="text-xl font-bold text-gray-900">Like & Retweet</h2>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tweet URL *
                </label>
                <input
                  type="text"
                  value={quickActionForm.tweetUrl}
                  onChange={handleQuickActionUrlChange}
                  placeholder="https://x.com/username/status/123456789"
                  disabled={loadingAction !== null}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  aria-label="Tweet URL"
                />
                {validationErrors.actionUrl && (
                  <p className="text-sm text-red-600 mt-1">
                    {validationErrors.actionUrl}
                  </p>
                )}
              </div>

              {/* Quick Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => executeLike()}
                  disabled={!quickActionForm.isValid || loadingAction !== null}
                  className="flex-1 px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:bg-gray-400 transition-colors font-medium text-lg"
                >
                  {loadingAction === "like" ? "⏳" : "❤️ Like"}
                </button>
                <button
                  onClick={() => executeRetweet()}
                  disabled={!quickActionForm.isValid || loadingAction !== null}
                  className="flex-1 px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-400 transition-colors font-medium text-lg"
                >
                  {loadingAction === "retweet" ? "⏳" : "🔁 Retweet"}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Operation History Sidebar */}
        <div className="lg:col-span-1 bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">
            Recent Operations
          </h3>

          {operationHistory.length === 0 ? (
            <p className="text-center text-gray-500 py-8">
              No operations yet. Your history will appear here.
            </p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {operationHistory.map((op) => (
                <div
                  key={op.id}
                  className={`p-3 rounded-lg border-l-4 ${
                    op.status === "success"
                      ? "bg-green-50 border-green-500"
                      : op.status === "failed"
                      ? "bg-red-50 border-red-500"
                      : "bg-yellow-50 border-yellow-500"
                  }`}
                  title={op.error || ""}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-semibold text-gray-900">
                        {op.type === "post" && "📝 Post"}
                        {op.type === "reply" && "💬 Reply"}
                        {op.type === "quote" && "🔄 Quote"}
                        {op.type === "like" && "❤️ Like"}
                        {op.type === "retweet" && "🔁 Retweet"}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        {new Date(op.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    <span
                      className={`text-lg ${
                        op.status === "success"
                          ? "text-green-600"
                          : op.status === "failed"
                          ? "text-red-600"
                          : "text-yellow-600"
                      }`}
                    >
                      {op.status === "success" && "✅"}
                      {op.status === "failed" && "❌"}
                      {op.status === "pending" && "⏳"}
                    </span>
                  </div>
                  {op.error && (
                    <p className="text-xs text-red-600 mt-2 line-clamp-2">
                      {op.error}
                    </p>
                  )}
                </div>
              ))}
              <div ref={historyEndRef} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default XOperations;
