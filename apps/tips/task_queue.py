"""
Background task queue for asynchronous betslip processing
"""
import queue
import threading
import logging
from typing import Callable, Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskQueue:
    """Simple task queue using threading for background processing"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure only one queue instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the task queue"""
        if self._initialized:
            return

        self.task_queue = queue.Queue()
        self.workers = []
        self.running = False
        self.num_workers = 3  # Number of worker threads
        self._initialized = True

        logger.info("TaskQueue initialized")

    def start(self):
        """Start worker threads"""
        if self.running:
            return

        self.running = True
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker,
                name=f"TaskWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        logger.info(f"Started {self.num_workers} worker threads")

    def stop(self):
        """Stop all worker threads"""
        self.running = False
        # Add sentinel values to wake up workers
        for _ in range(self.num_workers):
            self.task_queue.put(None)

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)

        self.workers.clear()
        logger.info("All workers stopped")

    def _worker(self):
        """Worker thread function to process tasks"""
        while self.running:
            try:
                # Get task from queue with timeout
                task = self.task_queue.get(timeout=1)

                if task is None:  # Sentinel value to stop
                    break

                # Unpack task
                task_id, func, args, kwargs, callback = task

                try:
                    logger.info(f"Processing task {task_id}: {func.__name__}")
                    result = func(*args, **kwargs)

                    # Call callback if provided
                    if callback:
                        callback(task_id, result, None)

                    logger.info(f"Task {task_id} completed successfully")

                except Exception as e:
                    logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)

                    # Call callback with error
                    if callback:
                        callback(task_id, None, e)

                finally:
                    self.task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {str(e)}", exc_info=True)

    def enqueue(
        self,
        func: Callable,
        *args,
        callback: Callable = None,
        **kwargs
    ) -> str:
        """
        Add a task to the queue

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            callback: Optional callback function(task_id, result, error)
            **kwargs: Keyword arguments for the function

        Returns:
            str: Task ID
        """
        # Generate unique task ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Add task to queue
        self.task_queue.put((task_id, func, args, kwargs, callback))

        logger.info(f"Task {task_id} enqueued: {func.__name__}")

        return task_id

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.task_queue.qsize()

    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return self.task_queue.empty()


# Global task queue instance
_task_queue = None


def get_task_queue() -> TaskQueue:
    """Get or create the global task queue instance"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
        _task_queue.start()
    return _task_queue


def enqueue_task(func: Callable, *args, callback: Callable = None, **kwargs) -> str:
    """
    Convenience function to enqueue a task

    Args:
        func: Function to execute
        *args: Positional arguments
        callback: Optional callback function(task_id, result, error)
        **kwargs: Keyword arguments

    Returns:
        str: Task ID
    """
    queue = get_task_queue()
    return queue.enqueue(func, *args, callback=callback, **kwargs)
