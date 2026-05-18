from threading import Thread
from decimal import Decimal
from typing import List, Tuple


class Worker(Thread):
    """
    Работна нишка, която изчислява частични суми от реда на Тейлър за дадени интервали.
    """

    def __init__(
        self,
        worker_id: int,
        tasks: List[Tuple[int, int, int]],
    ):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.tasks = tasks
        self.results: List[Tuple[int, Decimal, int]] = []

    def run(self) -> None:
        for task_idx, start_k, end_k in self.tasks:
            local_mult: int = 1
            local_sum: Decimal = Decimal(0)
            one: Decimal = Decimal(1)

            for i in range(start_k, end_k):
                local_mult *= i + 1
                local_sum += one / Decimal(local_mult)

            self.results.append((task_idx, local_sum, local_mult))
