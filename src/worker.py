from threading import Thread
from decimal import Decimal
from queue import Queue
from typing import Optional, Tuple, List


class Worker(Thread):
    """
    Pipeline-worker, which calculates a partial sum for a slice of the Taylor series.
    It processes assigned intervals, fetches the previous result from the corresponding queue,
    adds its local sum, and sends the new result to the next queue.
    """

    def __init__(
        self,
        worker_id: int,
        threads_count: int,
        intervals: List[Tuple[int, int]],
        queues: List[Queue],
        precision: int,
    ):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.threads_count = threads_count
        self.intervals = intervals
        self.queues = queues
        self.precision = precision
        self.result: Optional[Tuple[Decimal, int]] = None

    def run(self) -> None:
        from decimal import getcontext
        getcontext().prec = self.precision + 10
        one: Decimal = Decimal(1)

        for i in range(self.worker_id, len(self.intervals), self.threads_count):
            start_k, end_k = self.intervals[i]

            local_term: Decimal = one
            local_sum: Decimal = Decimal(0)

            for k in range(start_k, end_k):
                local_term /= Decimal(k + 1)
                local_sum += local_term

            previous_sum, base_term = self.queues[i].get()

            true_sum: Decimal = previous_sum + (local_sum * base_term)
            true_term: Decimal = base_term * local_term

            self.queues[i + 1].put((true_sum, true_term))

            if i == len(self.intervals) - 1:
                self.result = (true_sum, true_term)  # type: ignore
