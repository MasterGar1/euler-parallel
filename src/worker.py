from threading import Thread
from decimal import Decimal
from queue import Queue
from typing import Optional, Tuple


class Worker(Thread):
    """
    Работна нишка, която изчислява частична сума от реда на Тейлър за даден интервал.
    За да избегне изчакване, всяка нишка изчислява "локална сума" и "локален множител"
    независимо от предишните нишки. Когато предишната нишка приключи,
    те споделят резултата и го комбинират мигновено!
    """

    def __init__(
        self,
        worker_id: int,
        in_queue: Queue,
        out_queue: Optional[Queue],
        start_k: int,
        end_k: int,
    ):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.start_k = start_k
        self.end_k = end_k
        self.result: Optional[Tuple[Decimal, int]] = None

    def run(self) -> None:
        # Напълно паралелно локално изчисление
        # Изнасяме базовия факториел:
        # 1/(start+1)! + 1/(start+2)! = (1/start!) * (1/(start+1) + 1/((start+1)*(start+2)))

        local_mult: int = 1
        local_sum: Decimal = Decimal(0)
        one: Decimal = Decimal(1)

        for i in range(self.start_k, self.end_k):
            local_mult *= i + 1
            local_sum += one / Decimal(local_mult)

        # Изчакване предишната нишка да сподели резултата си
        previous_sum, base_fact = self.in_queue.get()
        true_sum: Decimal = previous_sum + (local_sum / Decimal(base_fact))
        true_fact: int = base_fact * local_mult

        # Предаване на състоянието на следващата нишка линейно
        if self.out_queue is not None:
            self.out_queue.put((true_sum, true_fact))
        else:
            self.result = (true_sum, true_fact)
