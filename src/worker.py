import math
import sys
from threading import Thread
from decimal import Decimal, getcontext
from queue import Queue
from typing import Optional, Tuple, List

# Increase the limit for integer string conversion to allow fast Decimal conversions
sys.set_int_max_str_digits(1000000)


class Worker(Thread):
    """
    Работник (поток), който изчислява частична сума за слайс от ред на Тейлър.
    Обработва назначените интервали, получава предишния резултат от съответната опашка,
    добавя локалната си сума и изпраща новия резултат в следващата опашка.
    """

    def __init__(
        self,
        worker_id: int,
        threads_count: int,
        intervals: List[Tuple[int, int]],
        queues: List[Queue],
        precision: int,
    ):
        """Инициализира работника с ID, брой нишки, интервали, опашки и точност."""
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.threads_count = threads_count
        self.intervals = intervals
        self.queues = queues
        self.precision = precision
        self.result: Optional[Tuple[Decimal, None]] = None

    def run(self) -> None:
        """Изпълнява изчислението за назначените интервали и предава резултатите през опашките."""
        getcontext().prec = self.precision + 10

        for i in range(self.worker_id, len(self.intervals), self.threads_count):
            start_k, end_k = self.intervals[i]
            local_sum_num = 0
            local_term_den = 1
            for k in range(start_k, end_k):
                local_term_den *= (k + 1)
                local_sum_num = local_sum_num * (k + 1) + 1

            previous_data = self.queues[i].get()
            if isinstance(previous_data, tuple):
                P_num = previous_data[0]
            else:
                P_num = 1

            # P_num / start_k! + local_sum_num / end_k!
            # = (P_num * local_term_den + local_sum_num) / end_k!
            new_P_num = P_num * local_term_den + local_sum_num

            if i == len(self.intervals) - 1:
                total_fact = math.factorial(end_k)
                true_sum = Decimal(str(new_P_num)) / Decimal(str(total_fact))
                self.queues[i + 1].put((true_sum, None))
                self.result = (true_sum, None)  # type: ignore
            else:
                self.queues[i + 1].put((new_P_num, None))
